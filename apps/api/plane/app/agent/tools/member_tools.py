import logging
from typing import Dict, Any
from plane.db.models import ProjectMember, Issue, Project, IssueAssignee
from plane.app.agent.registry import agent_tool

logger = logging.getLogger(__name__)


@agent_tool(
    name="tool_get_members_workload",
    description="Thống kê danh sách thành viên dự án và số lượng khối lượng công việc họ đang đảm nhận.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
        },
        "required": []
    }
)
def tool_get_members_workload(project_id: str) -> Dict[str, Any]:
    memberships = ProjectMember.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("member", "project")
    project = memberships.first().project if memberships.exists() else Project.objects.filter(pk=project_id).first()
    project_name = project.name if project else "Dự án"

    result = []
    for pm in memberships:
        u = pm.member
        assigned_issues = Issue.objects.filter(project_id=project_id, assignees=u, deleted_at__isnull=True).select_related("state")
        total_assigned = assigned_issues.count()
        in_progress = assigned_issues.filter(state__group="started").count()
        completed = assigned_issues.filter(state__group="completed").count()

        result.append({
            "user_id": str(u.id),
            "display_name": u.display_name or u.first_name or u.email,
            "email": u.email,
            "role": pm.role,
            "total_assigned": total_assigned,
            "in_progress": in_progress,
            "completed": completed,
        })

    return {
        "project_name": project_name,
        "total_members": len(result),
        "members": result,
    }


@agent_tool(
    name="tool_rebalance_workload",
    description="Đề xuất hoặc thực hiện tái phân bổ khối lượng công việc trễ hạn giữa các thành viên bận và rảnh.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
            "dry_run": {"type": "boolean", "description": "True nếu chỉ đề xuất (không đổi DB), False để áp dụng ngay."}
        },
        "required": []
    }
)
def tool_rebalance_workload(project_id: str, dry_run: bool = True) -> Dict[str, Any]:
    workload = tool_get_members_workload(project_id)
    members = workload.get("members", [])
    if len(members) < 2:
        return {
            "success": False,
            "error": "Cần ít nhất 2 thành viên trong dự án để có thể tái phân bổ công việc.",
        }

    sorted_members = sorted(members, key=lambda x: x["in_progress"], reverse=True)
    most_busy = sorted_members[0]
    least_busy = sorted_members[-1]

    busy_issues = Issue.objects.filter(
        project_id=project_id,
        assignees__id=most_busy["user_id"],
        state__group="started",
        deleted_at__isnull=True,
    )

    reassigned = list(busy_issues[:2])
    reassigned_items = []
    for issue in reassigned:
        reassigned_items.append({
            "key": f"{issue.project.identifier}-{issue.sequence_id}",
            "title": issue.name,
        })

    if not dry_run and reassigned:
        from plane.db.models import User
        least_busy_user = User.objects.get(pk=least_busy["user_id"])
        for issue in reassigned:
            IssueAssignee.objects.filter(issue=issue, assignee_id=most_busy["user_id"]).delete()
            IssueAssignee.objects.create(
                issue=issue,
                assignee=least_busy_user,
                project=issue.project,
                workspace=issue.workspace,
            )

    return {
        "success": True,
        "dry_run": dry_run,
        "project_name": workload["project_name"],
        "most_busy": most_busy["display_name"],
        "least_busy": least_busy["display_name"],
        "reassigned_count": len(reassigned_items),
        "reassigned_tasks": reassigned_items,
    }
