# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from html import escape
from plane.db.models import Project, Issue
from plane.app.views.external.base import get_llm_config, get_llm_response


def handle_ai_ask(project: Project, question: str) -> str:
    """Invokes God Mode AI configuration to answer natural questions about the project."""
    if not question:
        return "🤖 Bạn có thể hỏi tôi bất cứ điều gì về dự án! Ví dụ: <code>/ask Tiến độ dự án hiện tại thế nào?</code>"

    # Get LLM Config from God Mode / Instance Config
    api_key, model, provider, base_url = get_llm_config()

    # Build Project Context
    recent_issues = (
        Issue.objects.filter(project=project)
        .select_related("state")
        .prefetch_related("assignees")
        .order_by("-updated_at")[:15]
    )

    issue_context_lines = []
    for issue in recent_issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        assignees = ", ".join([a.display_name for a in issue.assignees.all() if a.display_name]) or "Unassigned"
        issue_context_lines.append(f"- {identifier}: {issue.name} | Status: {state_name} | Assignee: {assignees}")

    context_str = "\n".join(issue_context_lines)

    system_prompt = (
        f"Bạn là Trợ lý AI Telegram cho dự án '{project.name}' (Mã dự án: {project.identifier}).\n"
        f"Dưới đây là thông tin thực tế về các Task gần đây trong dự án:\n"
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
