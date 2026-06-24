from django.http import HttpRequest
from ninja import NinjaAPI

from cleanapp.utils import get_cleanapp_logger
from core.api.auth import api_key_auth, session_auth, superuser_api_auth
from core.api.schemas import (
    AddEmailIn,
    AddEmailOut,
    AgentClientListOut,
    AgentPageListOut,
    AgentPageOut,
    AgentPageReviewIn,
    AgentPageReviewOut,
    AgentPageSelectionOut,
    AgentSitemapArchiveOut,
    AgentSitemapCreateIn,
    AgentSitemapListOut,
    AgentSitemapOut,
    AgentSitemapRefreshOut,
    BlogPostIn,
    BlogPostOut,
    BulkUpdatePagesIn,
    BulkUpdatePagesOut,
    DeleteEmailOut,
    DeleteSitemapOut,
    ErrorOut,
    SubmitFeedbackIn,
    SubmitFeedbackOut,
    ToggleEmailIn,
    ToggleEmailOut,
    UserSettingsOut,
)
from core.models import BlogPost, EmailPreference, Feedback, Page
from core.review_primitives import (
    PrimitiveError,
    archive_sitemap_for_profile,
    create_sitemap_for_profile,
    get_due_pages_for_profile,
    get_page_for_profile,
    get_pages_queryset,
    get_review_history_queryset,
    get_sitemap_for_profile,
    get_sitemaps_queryset,
    list_clients_for_profile,
    normalize_pagination,
    page_to_dict,
    queue_sitemap_refresh_for_profile,
    select_page_for_profile,
    sitemap_to_dict,
    update_page_review_outcome,
)

logger = get_cleanapp_logger(__name__)

api = NinjaAPI(docs_url=None)
profile_api_auth = [session_auth, api_key_auth]


def pagination_dict(*, limit: int, offset: int, total: int) -> dict:
    return {
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": offset + limit < total,
    }


def error_response(exc: PrimitiveError):
    return exc.status_code, {"code": exc.code, "detail": exc.message}


@api.post("/submit-feedback", response=SubmitFeedbackOut, auth=[session_auth])
def submit_feedback(request: HttpRequest, data: SubmitFeedbackIn):
    profile = request.auth
    try:
        Feedback.objects.create(profile=profile, feedback=data.feedback, page=data.page)
        return {"status": True, "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e), profile_id=profile.id)
        return {"status": False, "message": "Failed to submit feedback. Please try again."}


@api.post("/blog-posts/submit", response=BlogPostOut, auth=[superuser_api_auth])
def submit_blog_post(request: HttpRequest, data: BlogPostIn):
    profile = request.auth

    if not profile or not getattr(profile.user, "is_superuser", False):
        return BlogPostOut(status="error", message="Forbidden: superuser access required."), 403

    try:
        BlogPost.objects.create(
            title=data.title,
            description=data.description,
            slug=data.slug,
            tags=data.tags,
            content=data.content,
            status=data.status,
            # icon and image are ignored for now (file upload not handled)
        )
        return BlogPostOut(status="success", message="Blog post submitted successfully.")
    except Exception as e:
        return BlogPostOut(status="failure", message=f"Failed to submit blog post: {str(e)}")


@api.get("/user/settings", response=UserSettingsOut, auth=[session_auth])
def user_settings(request: HttpRequest):
    profile = request.auth
    try:
        profile_data = {
            "has_pro_subscription": profile.has_active_subscription,
        }
        data = {"profile": profile_data}

        return data
    except Exception as e:
        logger.error(
            "Error fetching user settings",
            error=str(e),
            profile_id=profile.id,
            exc_info=True,
        )
        return {"profile": {"has_pro_subscription": False}}


@api.post(
    "/agent/sitemaps",
    response={201: AgentSitemapOut, 400: ErrorOut, 403: ErrorOut},
    auth=profile_api_auth,
)
def agent_create_sitemap(request: HttpRequest, data: AgentSitemapCreateIn):
    profile = request.auth
    try:
        sitemap = create_sitemap_for_profile(
            profile,
            sitemap_url=data.sitemap_url,
            client_label=data.client_label,
            pages_per_review=data.pages_per_review,
            review_cadence=data.review_cadence,
        )
    except PrimitiveError as exc:
        return error_response(exc)
    return 201, sitemap_to_dict(sitemap)


@api.get(
    "/agent/sitemaps",
    response={200: AgentSitemapListOut, 400: ErrorOut},
    auth=profile_api_auth,
)
def agent_list_sitemaps(
    request: HttpRequest,
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
    client_label: str = "",
):
    profile = request.auth
    pagination = normalize_pagination(limit=limit, offset=offset)
    queryset = get_sitemaps_queryset(
        profile,
        include_inactive=include_inactive,
        client_label=client_label,
    )
    total = queryset.count()
    sitemaps = queryset[pagination.offset : pagination.offset + pagination.limit]
    return {
        "items": [sitemap_to_dict(sitemap) for sitemap in sitemaps],
        "pagination": pagination_dict(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        ),
    }


def agent_sitemap_payload(profile, sitemap_id: int) -> dict:
    return sitemap_to_dict(get_sitemap_for_profile(profile, sitemap_id))


@api.get(
    "/agent/sitemaps/{sitemap_id}",
    response={200: AgentSitemapOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_get_sitemap(request: HttpRequest, sitemap_id: int):
    try:
        return agent_sitemap_payload(request.auth, sitemap_id)
    except PrimitiveError as exc:
        return error_response(exc)


@api.delete(
    "/agent/sitemaps/{sitemap_id}",
    response={200: AgentSitemapArchiveOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_archive_sitemap(request: HttpRequest, sitemap_id: int):
    try:
        sitemap, archived_pages = archive_sitemap_for_profile(request.auth, sitemap_id)
    except PrimitiveError as exc:
        return error_response(exc)
    return {
        "success": True,
        "archived_pages": archived_pages,
        "sitemap": sitemap_to_dict(sitemap),
    }


@api.get(
    "/agent/sitemaps/{sitemap_id}/status",
    response={200: AgentSitemapOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_sitemap_status(request: HttpRequest, sitemap_id: int):
    try:
        return agent_sitemap_payload(request.auth, sitemap_id)
    except PrimitiveError as exc:
        return error_response(exc)


@api.post(
    "/agent/sitemaps/{sitemap_id}/refresh",
    response={200: AgentSitemapRefreshOut, 400: ErrorOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_refresh_sitemap(request: HttpRequest, sitemap_id: int):
    try:
        sitemap = queue_sitemap_refresh_for_profile(request.auth, sitemap_id)
    except PrimitiveError as exc:
        return error_response(exc)
    return {"success": True, "queued": True, "sitemap": sitemap_to_dict(sitemap)}


@api.get(
    "/agent/clients",
    response=AgentClientListOut,
    auth=profile_api_auth,
)
def agent_list_clients(request: HttpRequest, limit: int = 50, offset: int = 0):
    pagination = normalize_pagination(limit=limit, offset=offset)
    clients, total = list_clients_for_profile(request.auth, pagination=pagination)
    return {
        "items": clients,
        "pagination": pagination_dict(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        ),
    }


@api.get(
    "/agent/pages",
    response={200: AgentPageListOut, 400: ErrorOut},
    auth=profile_api_auth,
)
def agent_list_pages(
    request: HttpRequest,
    limit: int = 50,
    offset: int = 0,
    sitemap_id: int | None = None,
    client_label: str = "",
    include_inactive: bool = False,
    needs_review: bool | None = None,
    review_outcome: str = "",
):
    pagination = normalize_pagination(limit=limit, offset=offset)
    try:
        queryset = get_pages_queryset(
            request.auth,
            sitemap_id=sitemap_id,
            client_label=client_label,
            include_inactive=include_inactive,
            needs_review=needs_review,
            review_outcome=review_outcome,
        )
    except PrimitiveError as exc:
        return error_response(exc)
    total = queryset.count()
    pages = queryset[pagination.offset : pagination.offset + pagination.limit]
    return {
        "items": [page_to_dict(page) for page in pages],
        "pagination": pagination_dict(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        ),
    }


@api.get(
    "/agent/due-pages",
    response=AgentPageListOut,
    auth=profile_api_auth,
)
def agent_list_due_pages(
    request: HttpRequest,
    limit: int = 50,
    offset: int = 0,
    sitemap_id: int | None = None,
    client_label: str = "",
):
    pagination = normalize_pagination(limit=limit, offset=offset)
    pages, total = get_due_pages_for_profile(
        request.auth,
        sitemap_id=sitemap_id,
        client_label=client_label,
        pagination=pagination,
    )
    return {
        "items": [page_to_dict(page) for page in pages],
        "pagination": pagination_dict(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        ),
    }


@api.get(
    "/agent/review-history",
    response=AgentPageListOut,
    auth=profile_api_auth,
)
def agent_review_history(request: HttpRequest, limit: int = 50, offset: int = 0):
    pagination = normalize_pagination(limit=limit, offset=offset)
    queryset = get_review_history_queryset(request.auth)
    total = queryset.count()
    pages = queryset[pagination.offset : pagination.offset + pagination.limit]
    return {
        "items": [page_to_dict(page) for page in pages],
        "pagination": pagination_dict(
            limit=pagination.limit,
            offset=pagination.offset,
            total=total,
        ),
    }


@api.get(
    "/agent/pages/select",
    response={200: AgentPageSelectionOut, 400: ErrorOut},
    auth=profile_api_auth,
)
def agent_select_page(
    request: HttpRequest,
    mode: str = "next_due",
    sitemap_id: int | None = None,
    client_label: str = "",
    review_outcome: str = "",
):
    try:
        page = select_page_for_profile(
            request.auth,
            mode=mode,
            sitemap_id=sitemap_id,
            client_label=client_label,
            review_outcome=review_outcome,
        )
    except PrimitiveError as exc:
        return error_response(exc)
    return {"page": page_to_dict(page) if page else None}


@api.get(
    "/agent/pages/{page_id}",
    response={200: AgentPageOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_get_page(request: HttpRequest, page_id: int):
    try:
        page = get_page_for_profile(request.auth, page_id)
    except PrimitiveError as exc:
        return error_response(exc)
    return page_to_dict(page)


@api.patch(
    "/agent/pages/{page_id}/review",
    response={200: AgentPageReviewOut, 400: ErrorOut, 404: ErrorOut},
    auth=profile_api_auth,
)
def agent_update_page_review(request: HttpRequest, page_id: int, data: AgentPageReviewIn):
    try:
        page = update_page_review_outcome(
            request.auth,
            page_id,
            outcome=data.outcome,
            note=data.note,
        )
    except PrimitiveError as exc:
        return error_response(exc)
    return {"success": True, "page": page_to_dict(page)}


@api.delete("/sitemaps/{sitemap_id}", response=DeleteSitemapOut, auth=[session_auth])
def delete_sitemap(request: HttpRequest, sitemap_id: int):
    profile = request.auth
    try:
        sitemap, _archived_pages = archive_sitemap_for_profile(profile, sitemap_id)

        logger.info(
            "Sitemap archived",
            profile_id=profile.id,
            email=profile.user.email,
            sitemap_id=sitemap_id,
            sitemap_url=sitemap.sitemap_url,
        )

        return {"success": True, "message": "Sitemap archived successfully"}
    except PrimitiveError:
        logger.warning(
            "Sitemap not found for archive",
            profile_id=profile.id,
            email=profile.user.email,
            sitemap_id=sitemap_id,
        )
        return {"success": False, "message": "Sitemap not found"}
    except Exception as e:
        logger.error(
            "Failed to archive sitemap",
            error=str(e),
            profile_id=profile.id,
            sitemap_id=sitemap_id,
            exc_info=True,
        )
        return {"success": False, "message": "Failed to archive sitemap"}


@api.post("/pages/bulk-update", response=BulkUpdatePagesOut, auth=[session_auth])
def bulk_update_pages(request: HttpRequest, data: BulkUpdatePagesIn):
    profile = request.auth
    try:
        pages = Page.objects.filter(id__in=data.page_ids, profile=profile)

        if not pages.exists():
            logger.warning(
                "No pages found for bulk update",
                profile_id=profile.id,
                email=profile.user.email,
                page_ids=data.page_ids,
            )
            return {"success": False, "message": "No pages found", "updated_count": 0}

        updated_count = pages.update(needs_review=data.needs_review)

        action = (
            "marked as no need to review" if not data.needs_review else "marked as need to review"
        )
        return {
            "success": True,
            "message": f"{updated_count} page(s) {action}",
            "updated_count": updated_count,
        }
    except Exception as e:
        logger.error(
            "Failed to bulk update pages",
            error=str(e),
            profile_id=profile.id,
            page_ids=data.page_ids,
            exc_info=True,
        )
        return {"success": False, "message": "Failed to update pages", "updated_count": 0}


@api.post("/emails/add", response=AddEmailOut, auth=[session_auth])
def add_email(request: HttpRequest, data: AddEmailIn):
    profile = request.auth
    try:
        email_address = data.email_address.strip().lower()

        if EmailPreference.objects.filter(profile=profile, email_address=email_address).exists():
            return {"success": False, "message": "This email address is already added"}

        email_pref = EmailPreference.objects.create(
            profile=profile, email_address=email_address, enabled=True
        )

        logger.info(
            "Email preference added",
            profile_id=profile.id,
            email=profile.user.email,
            new_email=email_address,
        )

        return {
            "success": True,
            "message": "Email address added successfully",
            "email_id": email_pref.id,
        }
    except Exception as e:
        logger.error("Failed to add email", error=str(e), profile_id=profile.id, exc_info=True)
        return {"success": False, "message": "Failed to add email address"}


@api.patch("/emails/{email_id}", response=ToggleEmailOut, auth=[session_auth])
def toggle_email(request: HttpRequest, email_id: int, data: ToggleEmailIn):
    profile = request.auth
    try:
        email_pref = EmailPreference.objects.get(id=email_id, profile=profile)
        email_pref.enabled = data.enabled
        email_pref.save(update_fields=["enabled"])

        status = "enabled" if data.enabled else "disabled"
        logger.info(
            f"Email preference {status}",
            profile_id=profile.id,
            email=profile.user.email,
            email_id=email_id,
            email_address=email_pref.email_address,
        )

        return {"success": True, "message": f"Email notifications {status}"}
    except EmailPreference.DoesNotExist:
        logger.warning(
            "Email preference not found for toggle",
            profile_id=profile.id,
            email_id=email_id,
        )
        return {"success": False, "message": "Email address not found"}
    except Exception as e:
        logger.error(
            "Failed to toggle email",
            error=str(e),
            profile_id=profile.id,
            email_id=email_id,
            exc_info=True,
        )
        return {"success": False, "message": "Failed to update email address"}


@api.delete("/emails/{email_id}", response=DeleteEmailOut, auth=[session_auth])
def delete_email(request: HttpRequest, email_id: int):
    profile = request.auth
    try:
        email_pref = EmailPreference.objects.get(id=email_id, profile=profile)
        email_address = email_pref.email_address
        email_pref.delete()

        logger.info(
            "Email preference deleted",
            profile_id=profile.id,
            email=profile.user.email,
            email_id=email_id,
            deleted_email=email_address,
        )

        return {"success": True, "message": "Email address removed successfully"}
    except EmailPreference.DoesNotExist:
        logger.warning(
            "Email preference not found for deletion",
            profile_id=profile.id,
            email_id=email_id,
        )
        return {"success": False, "message": "Email address not found"}
    except Exception as e:
        logger.error(
            "Failed to delete email",
            error=str(e),
            profile_id=profile.id,
            email_id=email_id,
            exc_info=True,
        )
        return {"success": False, "message": "Failed to delete email address"}
