# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from html import escape
from plane.db.models import Project, Issue


def handle_project_summary(project: Project) -> str:
    """Generates project progress report & state breakdown."""
    total_issues = Issue.objects.filter(project=project).count()
    if total_issues == 0:
        return f"📊 Dự án <b>{escape(project.name)}</b> chưa có Task nào."

    completed_count = Issue.objects.filter(project=project, state__group="completed").count()
    started_count = Issue.objects.filter(project=project, state__group="started").count()
    unstarted_count = Issue.objects.filter(project=project, state__group="unstarted").count()
    backlog_count = Issue.objects.filter(project=project, state__group="backlog").count()
    cancelled_count = Issue.objects.filter(project=project, state__group="cancelled").count()

    completion_rate = int((completed_count / total_issues) * 100) if total_issues > 0 else 0
    filled = int(completion_rate / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    lines = [
        f"📊 <b>Báo cáo Tiến độ Dự án: {escape(project.name)}</b>\n",
        f"📈 <b>Tiến độ:</b> <code>{progress_bar}</code> <b>{completion_rate}%</b>",
        f"📦 <b>Tổng số Task:</b> {total_issues}\n",
        f"• ✅ <b>Hoàn thành (Completed):</b> {completed_count}",
        f"• 🔄 <b>Đang thực hiện (In Progress):</b> {started_count}",
        f"• ⏳ <b>Chưa bắt đầu (Todo):</b> {unstarted_count}",
        f"• 📥 <b>Backlog:</b> {backlog_count}",
        f"• 🚫 <b>Đã hủy (Cancelled):</b> {cancelled_count}",
    ]
    return "\n".join(lines)
