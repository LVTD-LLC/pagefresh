from django.conf import settings


def test_default_from_email_uses_pagefresh_lvtd_sender():
    assert settings.DEFAULT_FROM_EMAIL == "Rasul from PageFresh <rasul@lvtd.dev>"
