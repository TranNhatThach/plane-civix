# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Unit tests for SessionMiddleware.

Verifies:
- Sliding session behavior for standard web app requests (saving session when SESSION_SAVE_EVERY_REQUEST=True).
- Preserving strict 1-hour session expiration for admin/instance paths without sliding on normal read requests.
"""

from unittest.mock import MagicMock
from django.test import RequestFactory, override_settings
from django.http import HttpResponse

from plane.authentication.middleware.session import SessionMiddleware


class TestSessionMiddleware:
    def setup_method(self):
        self.factory = RequestFactory()
        self.get_response = MagicMock(return_value=HttpResponse())
        self.middleware = SessionMiddleware(self.get_response)

    @override_settings(SESSION_SAVE_EVERY_REQUEST=True, SESSION_COOKIE_AGE=2592000)
    def test_normal_app_session_slides_when_save_every_request_enabled(self):
        request = self.factory.get("/api/users/me/")
        request.session = MagicMock()
        request.session.accessed = True
        request.session.modified = False
        request.session.is_empty.return_value = False
        request.session.get_expire_at_browser_close.return_value = False
        request.session.get_expiry_age.return_value = 2592000
        request.session.session_key = "test-session-key"

        response = HttpResponse()
        self.middleware.process_response(request, response)

        # Should save the session and refresh cookie for normal user
        request.session.save.assert_called_once()
        assert "session-id" in response.cookies

    @override_settings(SESSION_SAVE_EVERY_REQUEST=True, ADMIN_SESSION_COOKIE_AGE=3600)
    def test_admin_session_does_not_slide_on_unmodified_request(self):
        request = self.factory.get("/api/instances/configurations/")
        request.session = MagicMock()
        request.session.accessed = True
        request.session.modified = False
        request.session.is_empty.return_value = False

        response = HttpResponse()
        self.middleware.process_response(request, response)

        # Should NOT save unmodified admin session to preserve fixed 1-hour expiry
        request.session.save.assert_not_called()
        assert "admin-session-id" not in response.cookies

    @override_settings(SESSION_SAVE_EVERY_REQUEST=True, ADMIN_SESSION_COOKIE_AGE=3600)
    def test_admin_session_saves_when_explicitly_modified(self):
        request = self.factory.get("/api/instances/configurations/")
        request.session = MagicMock()
        request.session.accessed = True
        request.session.modified = True
        request.session.is_empty.return_value = False
        request.session.get_expire_at_browser_close.return_value = False
        request.session.session_key = "admin-session-key"

        response = HttpResponse()
        self.middleware.process_response(request, response)

        # Should save when modified
        request.session.save.assert_called_once()
        assert "admin-session-id" in response.cookies
