import xml.etree.ElementTree as ET
from datetime import timedelta

import requests
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.html import conditional_escape

from cleanapp.utils import get_cleanapp_logger

logger = get_cleanapp_logger(__name__)


class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ""
        return f"""
            <div class="p-4 my-4 bg-red-50 rounded-md border border-red-600 border-solid">
              <div class="flex">
                <div class="flex-shrink-0">
                  <!-- Heroicon name: solid/x-circle -->
                  <svg class="w-5 h-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3 text-sm text-red-700">
                      {"".join(f"<p>{conditional_escape(e)}</p>" for e in self)}
                </div>
              </div>
            </div>
         """  # noqa: E501


def ping_healthchecks(ping_id):
    try:
        requests.get(f"https://healthchecks.cr.lvtd.dev/ping/{ping_id}", timeout=10)
    except requests.RequestException as e:
        logger.error("Ping failed", error=e, exc_info=True)


def should_send_email_to_profile(profile, last_email_time, current_time_in_user_tz):
    from core.choices import ReviewCadence
    from core.models import Sitemap

    if not last_email_time:
        return True

    sitemaps = Sitemap.objects.filter(profile=profile, is_active=True)
    if not sitemaps.exists():
        return False

    most_frequent_cadence = sitemaps.order_by("review_cadence").first().review_cadence

    time_since_last_email = current_time_in_user_tz - last_email_time

    if most_frequent_cadence == ReviewCadence.DAILY:
        return time_since_last_email >= timedelta(days=1)
    elif most_frequent_cadence == ReviewCadence.WEEKLY:
        return time_since_last_email >= timedelta(weeks=1)
    elif most_frequent_cadence == ReviewCadence.MONTHLY:
        return time_since_last_email >= timedelta(days=30)

    return False


def _loc_text(element):
    return (element.text or "").strip()


def extract_urls_from_sitemap(  # noqa: C901
    sitemap_content: bytes,
    sitemap_id: int = None,
    depth: int = 0,
    max_depth: int = 10,
    max_sitemaps: int = 100,
    visited_urls: set[str] | None = None,
    stats: dict | None = None,
) -> set:
    found_urls = set()
    visited_urls = visited_urls if visited_urls is not None else set()
    stats = stats if stats is not None else {"sitemaps_processed": 1, "fetch_errors": 0}

    if depth > max_depth:
        logger.warning(
            "Max recursion depth reached during sitemap parsing",
            sitemap_id=sitemap_id,
            depth=depth,
        )
        return found_urls

    try:
        root = ET.fromstring(sitemap_content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        nested_sitemaps = root.findall(".//ns:sitemap/ns:loc", namespace)
        if not nested_sitemaps:
            nested_sitemaps = root.findall(".//sitemap/loc")

        if nested_sitemaps:
            logger.info(
                "Found nested sitemaps",
                sitemap_id=sitemap_id,
                nested_count=len(nested_sitemaps),
                depth=depth,
            )
            for nested_sitemap_element in nested_sitemaps:
                nested_url = _loc_text(nested_sitemap_element)
                if not nested_url:
                    continue

                if nested_url in visited_urls:
                    logger.warning(
                        "Circular sitemap reference skipped",
                        sitemap_id=sitemap_id,
                        nested_url=nested_url,
                        depth=depth,
                    )
                    continue

                if stats["sitemaps_processed"] >= max_sitemaps:
                    logger.warning(
                        "Max sitemaps limit reached during sitemap parsing",
                        sitemap_id=sitemap_id,
                        max_sitemaps=max_sitemaps,
                    )
                    break

                visited_urls.add(nested_url)
                stats["sitemaps_processed"] += 1

                try:
                    nested_response = requests.get(nested_url, timeout=30)
                    nested_response.raise_for_status()
                    nested_urls = extract_urls_from_sitemap(
                        nested_response.content,
                        sitemap_id=sitemap_id,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_sitemaps=max_sitemaps,
                        visited_urls=visited_urls,
                        stats=stats,
                    )
                    found_urls.update(nested_urls)
                except (requests.RequestException, ValidationError) as e:
                    stats["fetch_errors"] += 1
                    logger.warning(
                        "Failed to fetch or parse nested sitemap",
                        sitemap_id=sitemap_id,
                        nested_url=nested_url,
                        error=str(e),
                    )
            return found_urls

        urls = root.findall(".//ns:url/ns:loc", namespace)
        if not urls:
            urls = root.findall(".//url/loc")

        for url_element in urls:
            url = _loc_text(url_element)
            if url:
                found_urls.add(url)

    except ET.ParseError as e:
        logger.error(
            "Failed to parse sitemap XML",
            sitemap_id=sitemap_id,
            error=str(e),
            exc_info=True,
        )
        raise ValidationError("Sitemap XML could not be parsed.") from e

    return found_urls
