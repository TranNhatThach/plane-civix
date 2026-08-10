# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from typing import Optional
from html import escape
from plane.db.models import Project, Workspace, Issue
from plane.app.views.external.base import get_llm_config, get_llm_response


def handle_ai_ask(project_or_workspace, question: str, default_project: Optional[Project] = None) -> str:
    """Invokes God Mode AI configuration to answer natural questions about projects in the workspace."""
    if not question:
        return "🤖 Bạn có thể hỏi tôi bất cứ điều gì về các dự án trong Workspace! Ví dụ: <code>/ask Tiến độ dự án hiện tại thế nào?</code>"

    workspace = None
    project = None

    if isinstance(project_or_workspace, Project):
        project = project_or_workspace
        workspace = project.workspace
    elif isinstance(project_or_workspace, Workspace):
        workspace = project_or_workspace
        project = default_project
    else:
        workspace = getattr(project_or_workspace, "workspace", None)

    if not workspace and project:
        workspace = project.workspace

    # Get LLM Config from God Mode / Instance Config
    api_key, model, provider, base_url = get_llm_config()

    if workspace:
        projects = list(Project.objects.filter(workspace=workspace))
        recent_issues = (
            Issue.objects.filter(project__workspace=workspace)
            .select_related("state", "project")
            .prefetch_related("assignees")
            .order_by("-updated_at")[:30]
        )
        proj_str = ", ".join([f"{p.name} (Mã: {p.identifier})" for p in projects]) or "Chưa có dự án"
        workspace_name = workspace.name
    elif project:
        projects = [project]
        recent_issues = (
            Issue.objects.filter(project=project)
            .select_related("state", "project")
            .prefetch_related("assignees")
            .order_by("-updated_at")[:20]
        )
        proj_str = f"{project.name} (Mã: {project.identifier})"
        workspace_name = project.name
    else:
        return "⚠️ Không xác định được Workspace hoặc Dự án."

    issue_context_lines = []
    for issue in recent_issues:
        proj = issue.project
        identifier = f"{proj.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        assignees = ", ".join([a.display_name for a in issue.assignees.all() if a.display_name]) or "Unassigned"
        issue_context_lines.append(f"- [{identifier}] (Dự án: {proj.name}): {issue.name} | Status: {state_name} | Assignee: {assignees}")

    context_str = "\n".join(issue_context_lines) if issue_context_lines else "Chưa có task nào."

    system_prompt = (
        f"Bạn là Trợ lý AI Telegram cho Workspace '{workspace_name}'.\n"
        f"Danh sách tất cả các dự án trong Workspace: {proj_str}.\n"
        f"Dưới đây là thông tin thực tế về các Task mới nhất trên toàn hệ thống Workspace:\n"
        f"{context_str}\n\n"
        f"Hãy trả lời câu hỏi của người dùng một cách ngắn gọn, chính xác, lịch sự bằng tiếng Việt (hoặc ngôn ngữ người dùng hỏi). "
        f"Sử dụng định dạng HTML Telegram đơn giản (dùng <b>, <i>, <code>) nếu cần."
    )

    if not provider or not model or (not api_key and provider not in ["custom", "ollama"] and not base_url):
        return (
            f"🤖 <b>Plane AI Assistant</b>\n\n"
            f"⚠️ AI trong God Mode chưa được cấu hình API Key hoặc Provider.\n"
            f"Vui lòng vào <b>God Mode / Admin Settings ➔ AI Configuration</b> để thiết lập LLM API Key."
        )

    response_text, error_msg = get_llm_response(
        task=system_prompt,
        prompt=question,
        api_key=api_key,
        model=model,
        provider=provider,
        base_url=base_url,
    )

    if error_msg:
        return f"⚠️ <b>Lỗi kết nối AI ({provider}):</b> {escape(error_msg)}"

    return f"🤖 <b>Plane AI Assistant ({model}):</b>\n\n{response_text}"
