from core.choices import ReviewCadence
from core.forms import ProfileUpdateForm, SitemapSettingsForm
from core.models import Sitemap


def test_profile_update_form_rejects_unknown_timezone():
    form = ProfileUpdateForm(
        data={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "preferred_email_time": "09:30",
            "timezone": "Mars/Base",
        }
    )

    assert not form.is_valid()
    assert "timezone" in form.errors


def test_sitemap_settings_form_limits_pages_per_review():
    sitemap = Sitemap(
        sitemap_url="https://example.com/sitemap.xml",
        review_cadence=ReviewCadence.DAILY,
        pages_per_review=1,
        is_active=True,
    )
    form = SitemapSettingsForm(
        data={
            "client_label": "Acme",
            "pages_per_review": "51",
            "review_cadence": ReviewCadence.DAILY,
            "is_active": "on",
        },
        instance=sitemap,
    )

    assert not form.is_valid()
    assert "pages_per_review" in form.errors
