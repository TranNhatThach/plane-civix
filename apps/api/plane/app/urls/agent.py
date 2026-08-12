# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path
from plane.app.views.agent import AgentStreamEndpoint, AgentSessionViewSet

urlpatterns = [
    path(
        "workspaces/<str:slug>/agent/chat/stream/",
        AgentStreamEndpoint.as_view(),
        name="agent-chat-stream",
    ),
    path(
        "workspaces/<str:slug>/agent/sessions/",
        AgentSessionViewSet.as_view({"get": "list", "post": "create"}),
        name="agent-sessions",
    ),
    path(
        "workspaces/<str:slug>/agent/sessions/<uuid:pk>/",
        AgentSessionViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="agent-session-detail",
    ),
]
