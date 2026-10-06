# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from plane.authentication.adapter.error import AUTHENTICATION_ERROR_CODES


class MustChangePasswordMiddleware(MiddlewareMixin):
    """
    Blocks API requests if the authenticated user has must_change_password=True,
    until they update their password via /api/auth/change-password/.
    """

    ALLOWED_EXEMPT_PATHS = (
        "/api/users/me/",
        "/api/auth/change-password/",
        "/api/auth/sign-out/",
        "/api/auth/csrf/",
        "/api/instances/",
        "/api/health/",
    )

    def process_request(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        # Only enforce on API paths
        if not request.path.startswith("/api/"):
            return None

        # Check exemptions
        for exempt_path in self.ALLOWED_EXEMPT_PATHS:
            if request.path.startswith(exempt_path):
                return None

        profile = getattr(user, "profile", None)
        if profile and profile.must_change_password:
            return JsonResponse(
                {
                    "error_message": "PASSWORD_CHANGE_REQUIRED",
                    "error_code": AUTHENTICATION_ERROR_CODES.get("PASSWORD_CHANGE_REQUIRED", 5196),
                    "error": "Password change is required before accessing other resources",
                },
                status=403,
            )

        return None
