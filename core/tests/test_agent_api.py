import json
from datetime import timedelta

import pytest
from django.utils import timezone

from core.choices import ReviewCadence, ReviewOutcome, SitemapImportStatus
from core.models import Page, Sitemap


def post_json(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def patch_json(client, path, payload):
    return client.patch(path, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_agent_api_creates_and_lists_sitemaps_for_profile(auth_client, profile, django_user_model):
    other_user = django_user_model.objects.create_user(
        username="other",
        email="other@example.com",
        password="password123",
    )
    Sitemap.objects.create(
        profile=other_user.profile,
        sitemap_url="https://other.example.com/sitemap.xml",
        client_label="Other",
    )

    response = post_json(
        auth_client,
        "/api/agent/sitemaps",
        {
            "sitemap_url": "https://client.example.com/sitemap.xml",
            "client_label": "Client A",
            "pages_per_review": 3,
            "review_cadence": ReviewCadence.WEEKLY,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["sitemap_url"] == "https://client.example.com/sitemap.xml"
    assert payload["client_label"] == "Client A"
    assert payload["pages_per_review"] == 3
    assert payload["review_cadence"] == ReviewCadence.WEEKLY
    assert payload["import_status"] == SitemapImportStatus.QUEUED

    list_response = auth_client.get("/api/agent/sitemaps")

    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert [item["id"] for item in items] == [payload["id"]]


@pytest.mark.django_db
def test_agent_api_accepts_profile_api_key(client, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://key.example.com/sitemap.xml",
        client_label="Key Client",
    )

    response = client.get("/api/agent/sitemaps", {"api_key": profile.key})

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == sitemap.id


@pytest.mark.django_db
def test_agent_api_archives_sitemap_and_pages(auth_client, profile, django_user_model):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://archive.example.com/sitemap.xml",
    )
    page = Page.objects.create(
        profile=profile,
        sitemap=sitemap,
        url="https://archive.example.com/a",
    )
    other_user = django_user_model.objects.create_user(
        username="archive-other",
        email="archive-other@example.com",
        password="password123",
    )
    other_sitemap = Sitemap.objects.create(
        profile=other_user.profile,
        sitemap_url="https://archive-other.example.com/sitemap.xml",
    )

    response = auth_client.delete(f"/api/agent/sitemaps/{sitemap.id}")
    denied_response = auth_client.delete(f"/api/agent/sitemaps/{other_sitemap.id}")

    assert response.status_code == 200
    assert response.json()["archived_pages"] == 1
    assert denied_response.status_code == 404

    sitemap.refresh_from_db()
    page.refresh_from_db()
    assert sitemap.is_active is False
    assert page.is_active is False


@pytest.mark.django_db
def test_agent_api_queues_sitemap_refresh_without_fetching(auth_client, profile, monkeypatch):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://refresh.example.com/sitemap.xml",
    )
    Sitemap.objects.filter(id=sitemap.id).update(
        import_status=SitemapImportStatus.SUCCEEDED,
        last_import_message="Previous import succeeded",
        last_import_finished_at=timezone.now(),
    )
    sitemap.refresh_from_db()
    captured = {}

    def fake_async_task(task_name, *args, **kwargs):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs

    monkeypatch.setattr("core.review_primitives.async_task", fake_async_task)

    response = auth_client.post(f"/api/agent/sitemaps/{sitemap.id}/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] is True
    assert payload["sitemap"]["import_status"] == SitemapImportStatus.QUEUED
    assert captured == {
        "task_name": "core.tasks.reparse_sitemap",
        "kwargs": {"sitemap_id": sitemap.id, "group": "Sitemap Reparse"},
    }

    captured.clear()
    second_response = auth_client.post(f"/api/agent/sitemaps/{sitemap.id}/refresh")
    assert second_response.status_code == 200
    assert second_response.json()["queued"] is True
    assert captured == {}

    status_response = auth_client.get(f"/api/agent/sitemaps/{sitemap.id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["import_status"] == SitemapImportStatus.QUEUED


@pytest.mark.django_db
def test_agent_api_lists_clients_pages_due_pages_and_selection(auth_client, profile):
    now = timezone.now()
    agency = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://agency.example.com/sitemap.xml",
        client_label="Agency",
        review_cadence=ReviewCadence.DAILY,
    )
    solo = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://solo.example.com/sitemap.xml",
        client_label="Solo",
        review_cadence=ReviewCadence.DAILY,
    )
    due_page = Page.objects.create(
        profile=profile,
        sitemap=agency,
        url="https://agency.example.com/due",
    )
    not_due_page = Page.objects.create(
        profile=profile,
        sitemap=agency,
        url="https://agency.example.com/not-due",
        last_review_email_sent_at=now,
    )
    Page.objects.create(
        profile=profile,
        sitemap=solo,
        url="https://solo.example.com/old",
        reviewed=True,
        reviewed_at=now - timedelta(days=1),
    )

    clients_response = auth_client.get("/api/agent/clients")
    pages_response = auth_client.get("/api/agent/pages", {"client_label": "Agency"})
    due_response = auth_client.get("/api/agent/due-pages", {"client_label": "Agency"})
    selection_response = auth_client.get(
        "/api/agent/pages/select",
        {"mode": "next_due", "client_label": "Agency"},
    )

    assert clients_response.status_code == 200
    assert clients_response.json()["items"] == [
        {"client_label": "Agency", "active_site_count": 1},
        {"client_label": "Solo", "active_site_count": 1},
    ]

    assert pages_response.status_code == 200
    assert [item["id"] for item in pages_response.json()["items"]] == [
        due_page.id,
        not_due_page.id,
    ]

    assert due_response.status_code == 200
    assert [item["id"] for item in due_response.json()["items"]] == [due_page.id]

    assert selection_response.status_code == 200
    selected = selection_response.json()["page"]
    assert selected["id"] == due_page.id
    assert selected["is_due"] is True
    assert selected["review_url"].endswith(f"/review-page/{due_page.id}/")


@pytest.mark.django_db
def test_agent_api_updates_review_outcomes_and_history(auth_client, profile):
    sitemap = Sitemap.objects.create(
        profile=profile,
        sitemap_url="https://review.example.com/sitemap.xml",
    )
    follow_up_page = Page.objects.create(
        profile=profile,
        sitemap=sitemap,
        url="https://review.example.com/follow-up",
    )
    reviewed_page = Page.objects.create(
        profile=profile,
        sitemap=sitemap,
        url="https://review.example.com/reviewed",
    )

    follow_up_response = patch_json(
        auth_client,
        f"/api/agent/pages/{follow_up_page.id}/review",
        {"outcome": ReviewOutcome.NEEDS_FOLLOW_UP, "note": "Refresh product screenshots."},
    )
    reviewed_response = patch_json(
        auth_client,
        f"/api/agent/pages/{reviewed_page.id}/review",
        {"outcome": ReviewOutcome.REVIEWED, "note": "Looks current."},
    )

    assert follow_up_response.status_code == 200
    follow_up_payload = follow_up_response.json()["page"]
    assert follow_up_payload["review_outcome"] == ReviewOutcome.NEEDS_FOLLOW_UP
    assert follow_up_payload["review_note"] == "Refresh product screenshots."
    assert follow_up_payload["reviewed"] is False
    assert follow_up_payload["needs_review"] is True

    assert reviewed_response.status_code == 200
    reviewed_payload = reviewed_response.json()["page"]
    assert reviewed_payload["review_outcome"] == ReviewOutcome.REVIEWED
    assert reviewed_payload["reviewed"] is True
    assert reviewed_payload["needs_review"] is False

    history_response = auth_client.get("/api/agent/review-history")

    assert history_response.status_code == 200
    history_ids = {item["id"] for item in history_response.json()["items"]}
    assert history_ids == {follow_up_page.id, reviewed_page.id}
