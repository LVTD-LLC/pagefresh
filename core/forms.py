from datetime import datetime
from functools import lru_cache

import pytz
from allauth.account.forms import LoginForm, SignupForm
from django import forms

from core.models import Profile, Sitemap
from core.utils import DivErrorList


@lru_cache(maxsize=1)
def get_timezone_list():
    timezones = []
    now = datetime.now(pytz.UTC)

    for tz_name in pytz.common_timezones:
        try:
            tz = pytz.timezone(tz_name)
            dt = now.astimezone(tz)
            offset = dt.strftime("%z")
            offset_hours = f"{offset[:3]}:{offset[3:]}"
            label = f"(UTC{offset_hours}) {tz_name.replace('_', ' ')}"
            timezones.append({"value": tz_name, "label": label})
        except Exception:
            timezones.append({"value": tz_name, "label": tz_name})

    return sorted(timezones, key=lambda x: x["label"])


class CustomSignUpForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = Profile
        fields = ["preferred_email_time", "timezone"]
        widgets = {
            "preferred_email_time": forms.TimeInput(attrs={"type": "time"}),
            "timezone": forms.TextInput(attrs={"list": "timezone-list", "autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile.save()
        return profile


class SitemapForm(forms.ModelForm):
    class Meta:
        model = Sitemap
        fields = ["sitemap_url", "client_label"]
        widgets = {
            "sitemap_url": forms.URLInput(
                attrs={
                    "class": "pf-input mt-1",
                    "placeholder": "https://example.com/sitemap.xml",
                }
            ),
            "client_label": forms.TextInput(
                attrs={
                    "class": "pf-input mt-1",
                    "placeholder": "Client or workspace name",
                }
            ),
        }
        labels = {
            "sitemap_url": "Sitemap URL",
            "client_label": "Client label",
        }

    def clean_client_label(self):
        return (self.cleaned_data.get("client_label") or "").strip()


class SitemapSettingsForm(forms.ModelForm):
    class Meta:
        model = Sitemap
        fields = ["client_label", "pages_per_review", "review_cadence", "is_active"]
        widgets = {
            "client_label": forms.TextInput(
                attrs={
                    "class": "pf-input",
                    "placeholder": "Client label",
                }
            ),
            "pages_per_review": forms.NumberInput(
                attrs={
                    "class": "pf-input",
                    "min": "1",
                    "max": "50",
                }
            ),
            "review_cadence": forms.Select(attrs={"class": "pf-input"}),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": (
                        "h-4 w-4 rounded border-gray-300 text-emerald-700 focus:ring-emerald-600"
                    )
                }
            ),
        }
        labels = {
            "client_label": "Client label",
            "pages_per_review": "Pages per review email",
            "review_cadence": "Review cadence",
            "is_active": "Active",
        }

    def clean_client_label(self):
        return (self.cleaned_data.get("client_label") or "").strip()
