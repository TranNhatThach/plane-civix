import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from plane.db.models import Project, Issue, ProjectMember
from plane.app.agent.registry import agent_tool
from plane.app.agent.core.scope_guard import scope_guard


logger = logging.getLogger(__name__)


@agent_tool(
    name="tool_list_projects",
    description="Tra cứu danh sách các dự án (Projects) mà người dùng có quyền truy cập trong Workspace hiện tại.",
    parameters_schema={
        "type": "object",
        "properties": {
            "workspace_slug": {"type": "string", "description": "Mã slug workspace (nếu có)."}
        },
        "required": []
    }
)
@scope_guard(requires_project=False)
def tool_list_projects(
    workspace_slug: Optional[str] = None,
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    eff_ws_id = workspace_id or (_context.workspace_id if _context else None)
    
    queryset = Project.objects.filter(deleted_at__isnull=True).select_related("workspace")
    if eff_ws_id:
        queryset = queryset.filter(workspace_id=eff_ws_id)
    elif workspace_slug:
        queryset = queryset.filter(workspace__slug=workspace_slug)

    # Strictly filter by accessible projects for this specific user
    if _context and getattr(_context, "accessible_project_ids", None) is not None:
        queryset = queryset.filter(id__in=_context.accessible_project_ids)

    projects = list(queryset)
    items = []
    for p in projects:
        total_issues = Issue.objects.filter(project=p, deleted_at__isnull=True).count()
        members_count = ProjectMember.objects.filter(project=p, deleted_at__isnull=True).count()
        items.append({
            "id": str(p.id),
            "name": p.name,
            "identifier": p.identifier,
            "workspace_slug": p.workspace.slug if p.workspace else "",
            "total_issues": total_issues,
            "members_count": members_count,
        })

    return {
        "count": len(items),
        "projects": items,
    }


@agent_tool(
    name="tool_get_progress",
    description="Lấy báo cáo tổng quan về phần trăm tiến độ dự án, tổng số task hoàn thành, đang làm và quá hạn.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
        },
        "required": []
    }
)
def tool_get_progress(project_id: str) -> Dict[str, Any]:
    all_issues = Issue.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("state", "project")
    project = all_issues.first().project if all_issues.exists() else Project.objects.filter(pk=project_id).first()
    project_name = project.name if project else "Dự án"

    total_count = all_issues.count()
    completed_count = all_issues.filter(state__group="completed").count()
    started_count = all_issues.filter(state__group="started").count()
    backlog_count = all_issues.filter(state__group__in=["backlog", "unstarted"]).count()

    today = timezone.now().date()
    overdue_count = all_issues.filter(target_date__lt=today).exclude(state__group="completed").count()

    percent = round((completed_count / total_count * 100)) if total_count > 0 else 0

    return {
        "project_name": project_name,
        "total_tasks": total_count,
        "completed_tasks": completed_count,
        "started_tasks": started_count,
        "backlog_tasks": backlog_count,
        "overdue_tasks": overdue_count,
        "completion_percentage": percent,
    }


@agent_tool(
    name="tool_export_report",
    description="Xuất báo cáo chi tiết dự án dưới dạng Markdown.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
        },
        "required": []
    }
)
def tool_export_report(project_id: str) -> Dict[str, Any]:
    project = Project.objects.filter(pk=project_id).first()
    proj_name = project.name if project else "Dự án"

    progress = tool_get_progress(project_id)
    all_issues = Issue.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("state")

    lines = [
        f"# 📊 BÁO CÁO DỰ ÁN: {proj_name.upper()}",
        f"*Thời gian xuất*: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## 1. TỔNG QUAN TIẾN ĐỘ",
        f"- **Mức độ hoàn thành**: `{progress['completion_percentage']}%`",
        f"- **Đã hoàn thành**: `{progress['completed_tasks']}` / `{progress['total_tasks']}` tasks",
        f"- **Đang thực hiện**: `{progress['started_tasks']}` tasks",
        f"- **Quá hạn**: `{progress['overdue_tasks']}` tasks\n",
        "## 2. DANH SÁCH CÔNG VIỆC ACTIVE",
    ]

    for issue in all_issues[:30]:
        status_name = issue.state.name if issue.state else "N/A"
        lines.append(f"- **[{project.identifier}-{issue.sequence_id}] {issue.name}** (`{status_name}`)")

    markdown_content = "\n".join(lines)

    return {
        "success": True,
        "project_name": proj_name,
        "report_markdown": markdown_content,
    }


@agent_tool(
    name="tool_get_workspace_summary",
    description="Lấy báo cáo tổng hợp tiến độ và danh sách tất cả dự án trong toàn bộ Workspace cho Manager/Lead.",
    parameters_schema={
        "type": "object",
        "properties": {
            "workspace_id": {"type": "string", "description": "ID UUID của Workspace (nếu có)."}
        },
        "required": []
    }
)
@scope_guard(requires_project=False)
def tool_get_workspace_summary(
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    ws_id = workspace_id or (_context.workspace_id if _context else None)
    projects_qs = Project.objects.filter(workspace_id=ws_id, deleted_at__isnull=True)
    if _context and getattr(_context, "accessible_project_ids", None):
        projects_qs = projects_qs.filter(id__in=_context.accessible_project_ids)

    projects_data = []
    total_workspace_tasks = 0
    total_workspace_completed = 0
    total_workspace_overdue = 0

    today = timezone.now().date()

    for p in projects_qs:
        issues = Issue.objects.filter(project=p, deleted_at__isnull=True).select_related("state")
        t_count = issues.count()
        c_count = issues.filter(state__group="completed").count()
        o_count = issues.filter(target_date__lt=today).exclude(state__group="completed").count()

        total_workspace_tasks += t_count
        total_workspace_completed += c_count
        total_workspace_overdue += o_count

        percent = round((c_count / t_count * 100)) if t_count > 0 else 0
        projects_data.append({
            "id": str(p.id),
            "name": p.name,
            "identifier": p.identifier,
            "total_tasks": t_count,
            "completed_tasks": c_count,
            "overdue_tasks": o_count,
            "completion_percentage": percent,
        })

    ws_percent = round((total_workspace_completed / total_workspace_tasks * 100)) if total_workspace_tasks > 0 else 0

    return {
        "success": True,
        "total_projects": len(projects_data),
        "total_workspace_tasks": total_workspace_tasks,
        "total_workspace_completed": total_workspace_completed,
        "total_workspace_overdue": total_workspace_overdue,
        "workspace_completion_percentage": ws_percent,
        "projects": projects_data,
    }


