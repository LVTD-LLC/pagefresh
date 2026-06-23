import pytest
import requests

from core.models import Page, Sitemap
from core.tasks import process_sitemap_pages, reparse_sitemap


class FakeResponse:
    def __init__(self, content=b"", exc=None):
        self.content = content
        self.exc = exc

    def raise_for_status(self):
        if self.exc:
            raise self.exc


def sitemap_index(*urls):
    locs = "".join(f"<sitemap><loc>{url}</loc></sitemap>" for url in urls)
    return (
        '<?xml version="1.0"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{locs}</sitemapindex>"
    ).encode()


def urlset(*urls):
    locs = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    return (
        '<?xml version="1.0"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{locs}</urlset>"
    ).encode()


@pytest.mark.django_db
def test_process_sitemap_pages_imports_nested_sitemaps_without_duplicates(monkeypatch, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://example.com/sitemap.xml",
    )

    responses = {
        "https://example.com/sitemap.xml": FakeResponse(
            sitemap_index(
                "https://example.com/posts.xml",
                "https://example.com/pages.xml",
            )
        ),
        "https://example.com/posts.xml": FakeResponse(
            urlset("https://example.com/a", "https://example.com/b")
        ),
        "https://example.com/pages.xml": FakeResponse(
            urlset("https://example.com/b", "https://example.com/c")
        ),
    }

    monkeypatch.setattr("requests.get", lambda url, timeout: responses[url])

    message = process_sitemap_pages(sitemap.id)

    assert "created 3 pages" in message
    assert "skipped 0 existing pages" in message
    assert set(Page.objects.filter(sitemap=sitemap).values_list("url", flat=True)) == {
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    }


@pytest.mark.django_db
def test_process_sitemap_pages_reports_fetch_failure_without_creating_pages(monkeypatch, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://broken.example.com/sitemap.xml",
    )

    def fail_fetch(url, timeout):
        return FakeResponse(exc=requests.Timeout("timed out"))

    monkeypatch.setattr("requests.get", fail_fetch)

    message = process_sitemap_pages(sitemap.id)

    assert message.startswith("Failed to process sitemap:")
    assert Page.objects.filter(sitemap=sitemap).count() == 0


@pytest.mark.django_db
def test_process_sitemap_pages_reports_parse_failure_without_creating_pages(monkeypatch, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://invalid.example.com/sitemap.xml",
    )

    monkeypatch.setattr("requests.get", lambda url, timeout: FakeResponse(b"<not-xml"))

    message = process_sitemap_pages(sitemap.id)

    assert message.startswith("Failed to process sitemap:")
    assert Page.objects.filter(sitemap=sitemap).count() == 0


@pytest.mark.django_db
def test_process_sitemap_pages_respects_max_sitemap_limit(monkeypatch, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://limited.example.com/sitemap.xml",
    )

    responses = {
        "https://limited.example.com/sitemap.xml": FakeResponse(
            sitemap_index(
                "https://limited.example.com/one.xml",
                "https://limited.example.com/two.xml",
            )
        ),
        "https://limited.example.com/one.xml": FakeResponse(
            urlset("https://limited.example.com/a")
        ),
        "https://limited.example.com/two.xml": FakeResponse(
            urlset("https://limited.example.com/b")
        ),
    }

    monkeypatch.setattr("requests.get", lambda url, timeout: responses[url])

    message = process_sitemap_pages(sitemap.id, max_sitemaps=2)

    assert "processed 2 sitemap(s)" in message
    assert set(Page.objects.filter(sitemap=sitemap).values_list("url", flat=True)) == {
        "https://limited.example.com/a",
    }


@pytest.mark.django_db
def test_process_sitemap_pages_keeps_valid_siblings_after_nested_parse_error(monkeypatch, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://partial-import.example.com/sitemap.xml",
    )

    responses = {
        "https://partial-import.example.com/sitemap.xml": FakeResponse(
            sitemap_index(
                "https://partial-import.example.com/valid.xml",
                "https://partial-import.example.com/invalid.xml",
            )
        ),
        "https://partial-import.example.com/valid.xml": FakeResponse(
            urlset("https://partial-import.example.com/a")
        ),
        "https://partial-import.example.com/invalid.xml": FakeResponse(b"<not-xml"),
    }

    monkeypatch.setattr("requests.get", lambda url, timeout: responses[url])

    message = process_sitemap_pages(sitemap.id)

    assert "created 1 pages" in message
    assert "1 nested sitemap fetch/parse error(s)" in message
    assert set(Page.objects.filter(sitemap=sitemap).values_list("url", flat=True)) == {
        "https://partial-import.example.com/a",
    }


@pytest.mark.django_db
def test_reparse_sitemap_does_not_mark_pages_inactive_after_nested_fetch_error(
    monkeypatch, profile
):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://partial.example.com/sitemap.xml",
    )
    page = Page.objects.create(
        profile=profile,
        sitemap=sitemap,
        url="https://partial.example.com/still-valid",
    )

    responses = {
        "https://partial.example.com/sitemap.xml": FakeResponse(
            sitemap_index("https://partial.example.com/nested.xml")
        ),
        "https://partial.example.com/nested.xml": FakeResponse(
            exc=requests.Timeout("nested sitemap timed out")
        ),
    }

    monkeypatch.setattr("requests.get", lambda url, timeout: responses[url])

    message = reparse_sitemap(sitemap.id)

    page.refresh_from_db()
    assert "skipped 1 inactive update(s) after sitemap errors" in message
    assert page.is_active is True


@pytest.mark.django_db
def test_reparse_sitemap_does_not_mark_pages_inactive_after_nested_parse_error(
    monkeypatch, profile
):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://partial-parse.example.com/sitemap.xml",
    )
    page = Page.objects.create(
        profile=profile,
        sitemap=sitemap,
        url="https://partial-parse.example.com/still-valid",
    )

    responses = {
        "https://partial-parse.example.com/sitemap.xml": FakeResponse(
            sitemap_index("https://partial-parse.example.com/nested.xml")
        ),
        "https://partial-parse.example.com/nested.xml": FakeResponse(b"<not-xml"),
    }

    monkeypatch.setattr("requests.get", lambda url, timeout: responses[url])

    message = reparse_sitemap(sitemap.id)

    page.refresh_from_db()
    assert "skipped 1 inactive update(s) after sitemap errors" in message
    assert page.is_active is True
