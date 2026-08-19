# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path
from plane.api.views.integration.telegram import (
    TelegramAutomationEndpoint,
    TelegramTestMessageEndpoint,
    TelegramWebhookEndpoint,
)
from plane.api.views.integration.slack import (
    SlackAutomationEndpoint,
    SlackTestWebhookEndpoint,
    SlackCommandsEndpoint,
)
from plane.api.views.integration.trello import TrelloImportEndpoint

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
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/slack-automations/",
        SlackAutomationEndpoint.as_view(),
        name="slack-automation",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/slack-automations/<uuid:pk>/",
        SlackAutomationEndpoint.as_view(),
        name="slack-automation-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/slack-automations/test-message/",
        SlackTestWebhookEndpoint.as_view(),
        name="slack-test-message",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/slack-commands/",
        SlackCommandsEndpoint.as_view(),
        name="slack-commands",
    ),
    path(
        "workspaces/<str:slug>/projects/<str:project_id>/trello/import/",
        TrelloImportEndpoint.as_view(),
        name="trello-import",
    ),
]

