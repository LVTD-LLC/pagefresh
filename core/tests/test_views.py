from types import SimpleNamespace

import pytest
from allauth.account.models import EmailAddress
from django.test import RequestFactory
from django.urls import reverse

from core.choices import ProfileStates
from core.models import Sitemap
from core.views import HomeView


@pytest.fixture
def configured_billing_plans(settings):
    settings.CLEANAPP_FREE_SITE_LIMIT = 1
    settings.CLEANAPP_BILLING_PLANS = {
        "starter": {
            "display_name": "Starter",
            "price_id": "price_starter",
            "site_limit": 5,
            "trial_days": 14,
        },
        "agency": {
            "display_name": "Agency",
            "price_id": "price_agency",
            "site_limit": 30,
            "trial_days": 14,
        },
    }
    settings.STRIPE_PRICE_IDS = {
        "starter": "price_starter",
        "agency": "price_agency",
        "monthly": "price_starter",
        "yearly": "price_agency",
    }


@pytest.fixture(autouse=True)
def disable_sitemap_background_tasks(monkeypatch):
    from core import signals

    monkeypatch.setattr(signals, "async_task", lambda *args, **kwargs: None)


@pytest.mark.django_db
class TestHomeView:
    def test_home_view_status_code(self, user):
        request = RequestFactory().get(reverse("home"))
        request.user = user

        response = HomeView.as_view()(request)

        assert response.status_code == 200

    def test_home_view_uses_correct_template(self, user):
        request = RequestFactory().get(reverse("home"))
        request.user = user

        response = HomeView.as_view()(request)

        assert "pages/home.html" in response.template_name

    def test_home_blocks_new_sitemap_when_limit_reached(
        self, auth_client, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.stripe_plan_key = "starter"
        profile.save(update_fields=["state", "stripe_plan_key"])

        for idx in range(5):
            Sitemap.objects.create(
                profile=profile,
                sitemap_url=f"https://limit-{idx}.example.com/sitemap.xml",
            )

        response = auth_client.post(
            reverse("home"),
            {"sitemap_url": "https://blocked.example.com/sitemap.xml"},
        )

        assert response.status_code == 302
        assert response.url == reverse("pricing")
        assert Sitemap.objects.filter(profile=profile, is_active=True).count() == 5

    def test_home_allows_new_sitemap_when_under_limit(
        self, auth_client, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.stripe_plan_key = "starter"
        profile.save(update_fields=["state", "stripe_plan_key"])

        for idx in range(4):
            Sitemap.objects.create(
                profile=profile,
                sitemap_url=f"https://under-{idx}.example.com/sitemap.xml",
            )

        response = auth_client.post(
            reverse("home"),
            {"sitemap_url": "https://allowed.example.com/sitemap.xml"},
        )

        assert response.status_code == 302
        assert response.url == reverse("home")
        assert Sitemap.objects.filter(profile=profile, is_active=True).count() == 5

    def test_home_limit_counts_only_active_sitemaps(
        self, auth_client, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.stripe_plan_key = "starter"
        profile.save(update_fields=["state", "stripe_plan_key"])

        for idx in range(4):
            Sitemap.objects.create(
                profile=profile,
                sitemap_url=f"https://active-{idx}.example.com/sitemap.xml",
            )

        Sitemap.objects.create(
            profile=profile,
            sitemap_url="https://archived.example.com/sitemap.xml",
            is_active=False,
        )

        response = auth_client.post(
            reverse("home"),
            {"sitemap_url": "https://fifth-active.example.com/sitemap.xml"},
        )

        assert response.status_code == 302
        assert response.url == reverse("home")
        assert Sitemap.objects.filter(profile=profile, is_active=True).count() == 5


@pytest.mark.django_db
class TestCheckoutSession:
    def test_checkout_adds_trial_for_eligible_profiles(
        self, auth_client, user, profile, configured_billing_plans, monkeypatch
    ):
        profile.state = ProfileStates.SIGNED_UP
        profile.save(update_fields=["state"])

        captured = {}

        def fake_session_create(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(url="https://stripe.test/checkout")

        monkeypatch.setattr(
            "core.views.get_or_create_stripe_customer",
            lambda *_args, **_kwargs: SimpleNamespace(id="cus_test"),
        )
        monkeypatch.setattr("core.views.stripe.checkout.Session.create", fake_session_create)

        response = auth_client.post(
            reverse("user_upgrade_checkout_session", kwargs={"pk": user.id, "plan": "starter"})
        )

        assert response.status_code == 302
        assert response.url == "https://stripe.test/checkout"
        assert captured["metadata"]["plan"] == "starter"
        assert captured["subscription_data"]["trial_period_days"] == 14

    def test_checkout_skips_trial_for_already_subscribed_profiles(
        self, auth_client, user, profile, configured_billing_plans, monkeypatch
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.save(update_fields=["state"])

        captured = {}

        def fake_session_create(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(url="https://stripe.test/checkout")

        monkeypatch.setattr(
            "core.views.get_or_create_stripe_customer",
            lambda *_args, **_kwargs: SimpleNamespace(id="cus_test"),
        )
        monkeypatch.setattr("core.views.stripe.checkout.Session.create", fake_session_create)

        response = auth_client.post(
            reverse("user_upgrade_checkout_session", kwargs={"pk": user.id, "plan": "agency"})
        )

        assert response.status_code == 302
        assert response.url == "https://stripe.test/checkout"
        assert captured["metadata"]["plan"] == "agency"
        assert "trial_period_days" not in captured["subscription_data"]


@pytest.mark.django_db
class TestPricingView:
    def test_pricing_uses_configured_plan_limits(
        self, auth_client, configured_billing_plans, settings
    ):
        settings.CLEANAPP_BILLING_PLANS["starter"]["site_limit"] = 7
        settings.CLEANAPP_BILLING_PLANS["agency"]["site_limit"] = 42

        response = auth_client.get(reverse("pricing"))

        assert response.status_code == 200
        assert response.context["starter_site_limit"] == 7
        assert response.context["agency_site_limit"] == 42
        assert b">7<" in response.content
        assert b">42<" in response.content

    def test_starter_subscriber_can_upgrade_to_agency(
        self, auth_client, user, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.stripe_plan_key = "starter"
        profile.save(update_fields=["state", "stripe_plan_key"])

        response = auth_client.get(reverse("pricing"))

        assert response.status_code == 200
        assert response.content.count(b"Current plan is active") == 1
        agency_checkout_url = reverse(
            "user_upgrade_checkout_session",
            kwargs={"pk": user.id, "plan": "agency"},
        ).encode()
        assert agency_checkout_url in response.content
        assert b"Choose Agency" in response.content

    def test_agency_subscriber_only_sees_agency_as_current(
        self, auth_client, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.SUBSCRIBED
        profile.stripe_plan_key = "agency"
        profile.save(update_fields=["state", "stripe_plan_key"])

        response = auth_client.get(reverse("pricing"))

        assert response.status_code == 200
        assert response.content.count(b"Current plan is active") == 1
        assert b"Included in Agency" in response.content

    def test_churned_user_with_stale_plan_can_resubscribe(
        self, auth_client, user, profile, configured_billing_plans
    ):
        profile.state = ProfileStates.CHURNED
        profile.stripe_plan_key = "starter"
        profile.save(update_fields=["state", "stripe_plan_key"])

        response = auth_client.get(reverse("pricing"))

        starter_checkout_url = reverse(
            "user_upgrade_checkout_session",
            kwargs={"pk": user.id, "plan": "starter"},
        ).encode()
        agency_checkout_url = reverse(
            "user_upgrade_checkout_session",
            kwargs={"pk": user.id, "plan": "agency"},
        ).encode()
        assert response.status_code == 200
        assert b"Current plan is active" not in response.content
        assert starter_checkout_url in response.content
        assert agency_checkout_url in response.content


@pytest.mark.django_db
class TestUserSettingsView:
    def test_settings_form_preserves_django_field_names(self, auth_client, user):
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)

        response = auth_client.get(reverse("settings"))

        assert response.status_code == 200
        assert b'name="first_name"' in response.content
        assert b'name="last_name"' in response.content
        assert b'name="first-name"' not in response.content
        assert b'name="last-name"' not in response.content

    def test_settings_updates_first_and_last_name(self, auth_client, user):
        response = auth_client.post(
            reverse("settings"),
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "preferred_email_time": "09:30",
                "timezone": "UTC",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("settings")

        user.refresh_from_db()
        assert user.first_name == "Ada"
        assert user.last_name == "Lovelace"
