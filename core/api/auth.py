from django.http import HttpRequest
from ninja.security import APIKeyQuery

from cleanapp.utils import get_cleanapp_logger
from core.models import Profile

logger = get_cleanapp_logger(__name__)


class APIKeyAuth(APIKeyQuery):
    param_name = "api_key"

    def authenticate(self, request: HttpRequest, key: str) -> Profile | None:
        try:
            profile = Profile.objects.get(key=key)
            logger.info(
                "[Django Ninja Auth] API key authenticated",
                profile_id=profile.id,
                user_id=profile.user_id,
            )
            return profile
        except Profile.DoesNotExist:
            logger.warning("[Django Ninja Auth] Invalid API key")
            return None


class SessionAuth:
    """Authentication via Django session"""

    def authenticate(self, request: HttpRequest) -> Profile | None:
        if hasattr(request, "user") and request.user.is_authenticated:
            logger.info(
                "[Django Ninja Auth] API Request with authenticated user",
                user_id=request.user.id,
            )
            try:
                return request.user.profile
            except Profile.DoesNotExist:
                logger.warning("[Django Ninja Auth] No profile for user", user_id=request.user.id)
                return None
        return None

    def __call__(self, request: HttpRequest):
        return self.authenticate(request)


class SuperuserAPIKeyAuth(APIKeyQuery):
    param_name = "api_key"

    def authenticate(self, request: HttpRequest, key: str) -> Profile | None:
        try:
            profile = Profile.objects.get(key=key)
            if profile.user.is_superuser:
                logger.info(
                    "[Django Ninja Auth] Superuser API key authenticated",
                    profile_id=profile.id,
                    user_id=profile.user_id,
                )
                return profile
            logger.warning(
                "[Django Ninja Auth] Non-superuser attempted admin access",
                profile_id=profile.id,
                user_id=profile.user_id,
            )
            return None
        except Profile.DoesNotExist:
            logger.warning("[Django Ninja Auth] Profile does not exist")
            return None


api_key_auth = APIKeyAuth()
session_auth = SessionAuth()
superuser_api_auth = SuperuserAPIKeyAuth()
