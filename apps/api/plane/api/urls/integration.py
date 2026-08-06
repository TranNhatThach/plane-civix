# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path
from plane.api.views.integration.telegram import (
    TelegramAutomationEndpoint,
    TelegramTestMessageEndpoint,
    TelegramWebhookEndpoint,
)

urlpatterns = [
    path(
        "integrations/telegram/webhook/",
        TelegramWebhookEndpoint.as_view(),
        name="telegram-webhook",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/telegram-automations/",
        TelegramAutomationEndpoint.as_view(),
        name="telegram-automation",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/telegram-automations/<uuid:pk>/",
        TelegramAutomationEndpoint.as_view(),
        name="telegram-automation-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/telegram-automations/test-message/",
        TelegramTestMessageEndpoint.as_view(),
        name="telegram-test-message",
    ),
]
