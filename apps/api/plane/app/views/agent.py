# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import time
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from plane.app.views.base import BaseAPIView, BaseViewSet
from plane.db.models import Workspace, Project, Issue, AgentSession, AgentMessage
from plane.app.serializers.agent import AgentSessionSerializer, AgentMessageSerializer
from plane.app.agent.core.engine import PlaneAgentEngine


class AgentSessionViewSet(BaseViewSet):
    serializer_class = AgentSessionSerializer
    model = AgentSession

    def get_queryset(self):
        return AgentSession.objects.filter(
            workspace__slug=self.kwargs.get("slug"),
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        workspace = Workspace.objects.get(slug=self.kwargs.get("slug"))
        serializer.save(workspace=workspace, user=self.request.user)


class AgentStreamEndpoint(BaseAPIView):
    """
    Server-Sent Events (SSE) Streaming API for Plane AI Agent.
    Supports token-by-token streaming, 3-layer Context History & 5 Exclusive Features.
    """

    def post(self, request, slug):
        user_prompt = request.data.get("prompt", "").strip()
        session_id = request.data.get("session_id")
        active_project_id = request.data.get("active_project_id")
        active_issue_id = request.data.get("active_issue_id")
        feature_mode = request.data.get("feature_mode", "chat")

        if not user_prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workspace = Workspace.objects.get(slug=slug)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get or create AgentSession
        if session_id:
            try:
                session = AgentSession.objects.get(id=session_id, workspace=workspace, user=request.user)
            except AgentSession.DoesNotExist:
                session = AgentSession.objects.create(
                    workspace=workspace,
                    user=request.user,
                    title=user_prompt[:35] or "Chat Session"
                )
        else:
            session = AgentSession.objects.create(
                workspace=workspace,
                user=request.user,
                title=user_prompt[:35] or "Chat Session"
            )

        # Save user message
        AgentMessage.objects.create(
            session=session,
            role="user",
            content=user_prompt,
            metadata={
                "active_project_id": active_project_id,
                "active_issue_id": active_issue_id,
                "feature_mode": feature_mode,
            }
        )

        # Resolve target project
        project = None
        if active_project_id:
            project = Project.objects.filter(id=active_project_id, workspace=workspace).first()
        if not project:
            project = Project.objects.filter(workspace=workspace, deleted_at__isnull=True).first()

        if not project:
            return Response({"error": "No valid project found in workspace"}, status=status.HTTP_404_NOT_FOUND)

        # Context Layer 1: Active Screen Context
        active_context_info = []
        if active_issue_id:
            issue = Issue.objects.filter(id=active_issue_id, workspace=workspace).first()
            if issue:
                active_context_info.append(f"Người dùng đang xem Task: [{issue.sequence_id}] {issue.name}")

        # Context Layer 2: Session History (recent 5 messages)
        recent_msgs = AgentMessage.objects.filter(session=session).order_by("-created_at")[:6]
        history_str = "\n".join([f"{m.role.upper()}: {m.content}" for m in reversed(list(recent_msgs))])

        enriched_prompt = user_prompt
        if active_context_info or history_str:
            context_prefix = ""
            if active_context_info:
                context_prefix += "Context màn hình hiện tại:\n" + "\n".join(active_context_info) + "\n"
            if history_str:
                context_prefix += f"Lịch sử hội thoại phiên:\n{history_str}\n"
            enriched_prompt = f"{context_prefix}\nYêu cầu mới: {user_prompt}"

        # Execute Engine
        engine = PlaneAgentEngine(project=project, user=request.user)
        result = engine.process_request(enriched_prompt)

        final_text = result.get("text", "")
        action_taken = result.get("action_taken", "chat")
        result_data = result.get("data", {})

        # Save assistant message to DB
        AgentMessage.objects.create(
            session=session,
            role="assistant",
            content=final_text,
            metadata={
                "action_taken": action_taken,
                "data": result_data,
                "requires_confirmation": result.get("requires_confirmation", False),
                "pending_action": result.get("pending_action", None),
            }
        )

        def event_stream():
            # Send initial metadata header event
            init_payload = {
                "event": "start",
                "session_id": str(session.id),
                "action_taken": action_taken,
                "requires_confirmation": result.get("requires_confirmation", False),
                "pending_action": result.get("pending_action", None),
                "data": result_data,
            }
            yield f"data: {json.dumps(init_payload, ensure_ascii=False)}\n\n"

            # Stream words token by token to simulate real-time typing
            tokens = final_text.split(" ")
            for i, token in enumerate(tokens):
                chunk = token if i == 0 else " " + token
                chunk_payload = {
                    "event": "chunk",
                    "content": chunk,
                    "done": False,
                }
                yield f"data: {json.dumps(chunk_payload, ensure_ascii=False)}\n\n"
                time.sleep(0.02)  # smooth typing delay

            # Send done event
            end_payload = {
                "event": "end",
                "session_id": str(session.id),
                "done": True,
            }
            yield f"data: {json.dumps(end_payload, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
