# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import re
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from plane.authentication.adapter.error import AUTHENTICATION_ERROR_CODES


class MustChangePasswordMiddleware(MiddlewareMixin):
    """
    Blocks API requests if the authenticated user has must_change_password=True,
    until they update their password via /api/auth/change-password/ or /auth/change-password/.
    Exempts identity, authentication, and basic workspace membership/metadata queries
    so the user shell can render and present the password change interface.
    """

    ALLOWED_EXEMPT_PATHS = (
        "/api/users/me/",
        "/api/auth/change-password/",
        "/auth/change-password/",
        "/api/auth/sign-out/",
        "/auth/sign-out/",
        "/api/auth/csrf/",
        "/auth/get-csrf-token/",
        "/api/instances/",
        "/api/health/",
    )

    WORKSPACE_METADATA_PATTERN = re.compile(r"^/api/workspaces/[^/]+/?$")

    WORKSPACE_LAYOUT_EXEMPT_SUBPATHS = (
        "/workspace-members/me/",
        "/members/",
        "/projects/",
        "/workspace-views/",
        "/states/",
        "/user-favorite/",
        "/sidebar-preferences/",
        "/project-navigation-preferences/",
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

        # Allow user to check their own workspace membership and role
        if "/workspace-members/me/" in request.path:
            return None

        # Allow basic workspace metadata (name, slug, logo)
        if self.WORKSPACE_METADATA_PATTERN.match(request.path):
            return None

        # Allow layout-essential read endpoints for workspace shell navigation
        for subpath in self.WORKSPACE_LAYOUT_EXEMPT_SUBPATHS:
            if subpath in request.path:
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
