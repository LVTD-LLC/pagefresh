from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django_q.tasks import async_task

from cleanapp.utils import get_cleanapp_logger
from core.billing import get_active_site_count, get_site_limit_for_profile
from core.choices import ReviewCadence, ReviewOutcome, SitemapImportStatus
from core.models import Page, Profile, Sitemap
from core.review_queue import get_due_pages_queryset, is_page_due_for_review

logger = get_cleanapp_logger(__name__)

MAX_API_LIMIT = 100
DEFAULT_API_LIMIT = 50
MAX_REVIEW_NOTE_LENGTH = 4000


@dataclass
class Pagination:
    limit: int = DEFAULT_API_LIMIT
    offset: int = 0


class PrimitiveError(Exception):
    status_code = 400
    code = "invalid_request"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(PrimitiveError):
    status_code = 404
    code = "not_found"


class SiteLimitError(PrimitiveError):
    status_code = 403
    code = "site_limit_reached"


def normalize_pagination(limit: int = DEFAULT_API_LIMIT, offset: int = 0) -> Pagination:
    limit = max(1, min(limit, MAX_API_LIMIT))
    offset = max(0, offset)
    return Pagination(limit=limit, offset=offset)


def build_review_url(page: Page) -> str:
    path = reverse("review_page_redirect", kwargs={"page_id": page.id})
    site_url = getattr(settings, "SITE_URL", "") or ""
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def get_sitemap_for_profile(profile: Profile, sitemap_id: int) -> Sitemap:
    try:
        return Sitemap.objects.get(id=sitemap_id, profile=profile)
    except Sitemap.DoesNotExist as exc:
        raise NotFoundError("Sitemap not found") from exc


def get_page_for_profile(profile: Profile, page_id: int) -> Page:
    try:
        return Page.objects.select_related("sitemap").get(id=page_id, profile=profile)
    except Page.DoesNotExist as exc:
        raise NotFoundError("Page not found") from exc


def get_sitemaps_queryset(
    profile: Profile,
    *,
    include_inactive: bool = False,
    client_label: str = "",
):
    queryset = Sitemap.objects.filter(profile=profile).order_by("client_label", "sitemap_url", "id")
    if not include_inactive:
        queryset = queryset.filter(is_active=True)
    if client_label:
        queryset = queryset.filter(client_label__iexact=client_label.strip())
    return queryset


def get_pages_queryset(
    profile: Profile,
    *,
    sitemap_id: int | None = None,
    client_label: str = "",
    include_inactive: bool = False,
    needs_review: bool | None = None,
    review_outcome: str = "",
):
    queryset = Page.objects.filter(profile=profile).select_related("sitemap")
    if sitemap_id is not None:
        queryset = queryset.filter(sitemap_id=sitemap_id, sitemap__profile=profile)
    if client_label:
        queryset = queryset.filter(sitemap__client_label__iexact=client_label.strip())
    if not include_inactive:
        queryset = queryset.filter(is_active=True, sitemap__is_active=True)
    if needs_review is not None:
        queryset = queryset.filter(needs_review=needs_review)
    if review_outcome:
        if review_outcome not in ReviewOutcome.values:
            raise PrimitiveError("Unsupported review outcome")
        queryset = queryset.filter(review_outcome=review_outcome)
    return queryset.order_by("sitemap__client_label", "sitemap__sitemap_url", "url", "id")


def create_sitemap_for_profile(
    profile: Profile,
    *,
    sitemap_url: str,
    client_label: str = "",
    pages_per_review: int | None = None,
    review_cadence: str | None = None,
) -> Sitemap:
    if get_active_site_count(profile) >= get_site_limit_for_profile(profile):
        raise SiteLimitError("The active site limit for this profile has been reached")

    sitemap = Sitemap(
        profile=profile,
        sitemap_url=sitemap_url,
        client_label=(client_label or "").strip(),
        import_status=SitemapImportStatus.QUEUED,
        last_import_message="Queued for initial import",
    )
    if pages_per_review is not None:
        sitemap.pages_per_review = pages_per_review
    if review_cadence is not None:
        if review_cadence not in ReviewCadence.values:
            raise PrimitiveError("Unsupported review cadence")
        sitemap.review_cadence = review_cadence

    try:
        sitemap.full_clean()
    except DjangoValidationError as exc:
        raise PrimitiveError("; ".join(exc.messages)) from exc

    sitemap.save()
    logger.info(
        "Sitemap created through shared primitive",
        profile_id=profile.id,
        sitemap_id=sitemap.id,
        sitemap_url=sitemap.sitemap_url,
        client_label=sitemap.client_label,
    )
    return sitemap


def archive_sitemap_for_profile(profile: Profile, sitemap_id: int) -> tuple[Sitemap, int]:
    with transaction.atomic():
        try:
            sitemap = Sitemap.objects.select_for_update().get(id=sitemap_id, profile=profile)
        except Sitemap.DoesNotExist as exc:
            raise NotFoundError("Sitemap not found") from exc

        if not sitemap.is_active:
            return sitemap, 0

        sitemap.is_active = False
        sitemap.save(update_fields=["is_active", "updated_at"])
        archived_pages = Page.objects.filter(sitemap=sitemap, is_active=True).update(
            is_active=False
        )

    logger.info(
        "Sitemap archived through shared primitive",
        profile_id=profile.id,
        sitemap_id=sitemap.id,
        archived_pages=archived_pages,
    )
    return sitemap, archived_pages


def queue_sitemap_refresh_for_profile(profile: Profile, sitemap_id: int) -> Sitemap:
    sitemap = get_sitemap_for_profile(profile, sitemap_id)
    if not sitemap.is_active:
        raise PrimitiveError("Archived sitemaps cannot be refreshed")
    if sitemap.import_status in {SitemapImportStatus.QUEUED, SitemapImportStatus.RUNNING}:
        logger.info(
            "Sitemap refresh already pending",
            profile_id=profile.id,
            sitemap_id=sitemap.id,
            import_status=sitemap.import_status,
        )
        return sitemap

    sitemap.import_status = SitemapImportStatus.QUEUED
    sitemap.last_import_message = "Refresh queued"
    sitemap.last_import_started_at = None
    sitemap.last_import_finished_at = None
    sitemap.save(
        update_fields=[
            "import_status",
            "last_import_message",
            "last_import_started_at",
            "last_import_finished_at",
            "updated_at",
        ]
    )
    async_task("core.tasks.reparse_sitemap", sitemap_id=sitemap.id, group="Sitemap Reparse")
    logger.info(
        "Sitemap refresh queued through shared primitive",
        profile_id=profile.id,
        sitemap_id=sitemap.id,
    )
    return sitemap


def mark_sitemap_import_running(sitemap: Sitemap, message: str) -> None:
    sitemap.import_status = SitemapImportStatus.RUNNING
    sitemap.last_import_message = message
    sitemap.last_import_started_at = timezone.now()
    sitemap.last_import_finished_at = None
    sitemap.save(
        update_fields=[
            "import_status",
            "last_import_message",
            "last_import_started_at",
            "last_import_finished_at",
            "updated_at",
        ]
    )


def mark_sitemap_import_succeeded(sitemap: Sitemap, message: str) -> None:
    sitemap.import_status = SitemapImportStatus.SUCCEEDED
    sitemap.last_import_message = message
    sitemap.last_import_finished_at = timezone.now()
    sitemap.save(
        update_fields=[
            "import_status",
            "last_import_message",
            "last_import_finished_at",
            "updated_at",
        ]
    )


def mark_sitemap_import_failed(sitemap: Sitemap, message: str) -> None:
    sitemap.import_status = SitemapImportStatus.FAILED
    sitemap.last_import_message = message[:1000]
    sitemap.last_import_finished_at = timezone.now()
    sitemap.save(
        update_fields=[
            "import_status",
            "last_import_message",
            "last_import_finished_at",
            "updated_at",
        ]
    )


def list_clients_for_profile(profile: Profile, *, pagination: Pagination) -> tuple[list[dict], int]:
    queryset = (
        Sitemap.objects.filter(profile=profile, is_active=True)
        .exclude(client_label="")
        .values("client_label")
        .annotate(active_site_count=Count("id"))
        .order_by("client_label")
    )
    total = queryset.count()
    clients = [
        {
            "client_label": row["client_label"],
            "active_site_count": row["active_site_count"],
        }
        for row in queryset[pagination.offset : pagination.offset + pagination.limit]
    ]
    return clients, total


def get_due_pages_for_profile(
    profile: Profile,
    *,
    sitemap_id: int | None = None,
    client_label: str = "",
    pagination: Pagination | None = None,
    now=None,
) -> tuple[list[Page], int]:
    pagination = pagination or normalize_pagination()
    now = now or timezone.now()
    sitemaps = get_sitemaps_queryset(profile, client_label=client_label)
    if sitemap_id is not None:
        sitemaps = sitemaps.filter(id=sitemap_id)

    due_ids: list[int] = []
    for sitemap in sitemaps:
        due_ids.extend(get_due_pages_queryset(sitemap, now=now).values_list("id", flat=True))

    total = len(due_ids)
    selected_ids = due_ids[pagination.offset : pagination.offset + pagination.limit]
    if not selected_ids:
        return [], total

    pages_by_id = Page.objects.filter(id__in=selected_ids).select_related("sitemap").in_bulk()
    return [pages_by_id[page_id] for page_id in selected_ids if page_id in pages_by_id], total


def select_page_for_profile(
    profile: Profile,
    *,
    mode: Literal["next_due", "random", "filtered"] = "next_due",
    sitemap_id: int | None = None,
    client_label: str = "",
    review_outcome: str = "",
    now=None,
) -> Page | None:
    if mode == "next_due":
        pages, _total = get_due_pages_for_profile(
            profile,
            sitemap_id=sitemap_id,
            client_label=client_label,
            pagination=Pagination(limit=1, offset=0),
            now=now,
        )
        return pages[0] if pages else None

    queryset = get_pages_queryset(
        profile,
        sitemap_id=sitemap_id,
        client_label=client_label,
        review_outcome=review_outcome,
    )
    if mode == "random":
        return queryset.order_by("?").first()
    if mode == "filtered":
        return queryset.first()
    raise PrimitiveError("Unsupported page selection mode")


def get_review_history_queryset(profile: Profile):
    return (
        Page.objects.filter(profile=profile)
        .select_related("sitemap")
        .filter(Q(review_outcome_at__isnull=False) | Q(reviewed=True))
        .order_by("-review_outcome_at", "-reviewed_at", "-updated_at", "-id")
    )


def update_page_review_outcome(
    profile: Profile,
    page_id: int,
    *,
    outcome: str,
    note: str = "",
    now=None,
) -> Page:
    if outcome not in ReviewOutcome.values:
        raise PrimitiveError("Unsupported review outcome")

    page = get_page_for_profile(profile, page_id)
    now = now or timezone.now()
    note = (note or "").strip()
    if len(note) > MAX_REVIEW_NOTE_LENGTH:
        raise PrimitiveError(f"Review notes must be {MAX_REVIEW_NOTE_LENGTH} characters or fewer")

    page.review_outcome = outcome
    page.review_note = note
    page.review_outcome_at = now

    if outcome == ReviewOutcome.REVIEWED:
        page.reviewed = True
        page.reviewed_at = now
        page.needs_review = False
    elif outcome == ReviewOutcome.SKIPPED:
        page.reviewed = False
        page.reviewed_at = None
        page.needs_review = False
    else:
        page.reviewed = False
        page.reviewed_at = None
        page.needs_review = True

    page.save(
        update_fields=[
            "review_outcome",
            "review_note",
            "review_outcome_at",
            "reviewed",
            "reviewed_at",
            "needs_review",
            "updated_at",
        ]
    )
    logger.info(
        "Page review outcome updated",
        profile_id=profile.id,
        page_id=page.id,
        sitemap_id=page.sitemap_id,
        review_outcome=outcome,
        has_note=bool(note),
    )
    return page


def sitemap_to_dict(sitemap: Sitemap) -> dict:
    return {
        "id": sitemap.id,
        "uuid": str(sitemap.uuid),
        "sitemap_url": sitemap.sitemap_url,
        "client_label": sitemap.client_label,
        "pages_per_review": sitemap.pages_per_review,
        "review_cadence": sitemap.review_cadence,
        "is_active": sitemap.is_active,
        "import_status": sitemap.import_status,
        "last_import_message": sitemap.last_import_message,
        "last_import_started_at": sitemap.last_import_started_at,
        "last_import_finished_at": sitemap.last_import_finished_at,
        "created_at": sitemap.created_at,
        "updated_at": sitemap.updated_at,
    }


def page_to_dict(page: Page, *, now=None) -> dict:
    now = now or timezone.now()
    sitemap = page.sitemap
    return {
        "id": page.id,
        "uuid": str(page.uuid),
        "url": page.url,
        "sitemap_id": page.sitemap_id,
        "sitemap_url": sitemap.sitemap_url if sitemap else "",
        "client_label": sitemap.client_label if sitemap else "",
        "review_cadence": sitemap.review_cadence if sitemap else "",
        "is_active": page.is_active,
        "needs_review": page.needs_review,
        "reviewed": page.reviewed,
        "reviewed_at": page.reviewed_at,
        "last_review_email_sent_at": page.last_review_email_sent_at,
        "review_queue_attempts": page.review_queue_attempts,
        "review_outcome": page.review_outcome,
        "review_note": page.review_note,
        "review_outcome_at": page.review_outcome_at,
        "is_due": is_page_due_for_review(page, now=now),
        "review_url": build_review_url(page),
        "created_at": page.created_at,
        "updated_at": page.updated_at,
    }
