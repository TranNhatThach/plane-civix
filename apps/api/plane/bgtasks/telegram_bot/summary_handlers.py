# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from html import escape
from plane.db.models import Project, Workspace, Issue


def handle_workspace_summary(project_or_workspace) -> str:
    """Generates workspace-wide progress report & per-project breakdown."""
    workspace = None
    project = None

    if isinstance(project_or_workspace, Project):
        project = project_or_workspace
        workspace = project.workspace
    elif isinstance(project_or_workspace, Workspace):
        workspace = project_or_workspace
    else:
        workspace = getattr(project_or_workspace, "workspace", None)

    if not workspace and project:
        workspace = project.workspace

    if workspace:
        total_issues = Issue.objects.filter(project__workspace=workspace).count()
        ws_name = workspace.name
        projects = list(Project.objects.filter(workspace=workspace))
    elif project:
        total_issues = Issue.objects.filter(project=project).count()
        ws_name = project.name
        projects = [project]
    else:
        return "⚠️ Không xác định được Workspace hoặc Dự án."

    if total_issues == 0:
        return f"📊 Workspace <b>{escape(ws_name)}</b> chưa có Task nào."

    if workspace:
        issue_qs = Issue.objects.filter(project__workspace=workspace)
    else:
        issue_qs = Issue.objects.filter(project=project)

    completed_count = issue_qs.filter(state__group="completed").count()
    started_count = issue_qs.filter(state__group="started").count()
    unstarted_count = issue_qs.filter(state__group="unstarted").count()
    backlog_count = issue_qs.filter(state__group="backlog").count()
    cancelled_count = issue_qs.filter(state__group="cancelled").count()

    completion_rate = int((completed_count / total_issues) * 100) if total_issues > 0 else 0
    filled = int(completion_rate / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    lines = [
        f"📊 <b>Báo cáo Tiến độ Workspace: {escape(ws_name)}</b>\n",
        f"📈 <b>Tiến độ tổng thể:</b> <code>{progress_bar}</code> <b>{completion_rate}%</b>",
        f"📦 <b>Tổng số Task:</b> {total_issues}\n",
        f"• ✅ <b>Hoàn thành (Completed):</b> {completed_count}",
        f"• 🔄 <b>Đang thực hiện (In Progress):</b> {started_count}",
        f"• ⏳ <b>Chưa bắt đầu (Todo):</b> {unstarted_count}",
        f"• 📥 <b>Backlog:</b> {backlog_count}",
        f"• 🚫 <b>Đã hủy (Cancelled):</b> {cancelled_count}",
    ]

    if len(projects) > 0:
        lines.append("\n📁 <b>Chi tiết theo từng Dự án:</b>")
        for proj in projects:
            p_total = Issue.objects.filter(project=proj).count()
            p_completed = Issue.objects.filter(project=proj, state__group="completed").count()
            p_rate = int((p_completed / p_total) * 100) if p_total > 0 else 0
            lines.append(f"• <b>{escape(proj.name)}</b> (<code>{escape(proj.identifier)}</code>): {p_completed}/{p_total} task (<b>{p_rate}%</b>)")

    return "\n".join(lines)


def handle_project_summary(project: Project) -> str:
    """Alias for handle_workspace_summary for backward compatibility."""
    return handle_workspace_summary(project)
