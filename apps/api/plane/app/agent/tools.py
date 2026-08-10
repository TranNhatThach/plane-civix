import logging
from django.utils import timezone
from django.db.models import Q
from plane.db.models import Issue, State, IssueAssignee, ProjectMember, User, WorkspaceMember

logger = logging.getLogger(__name__)

# JSON Schemas for Tool Calling (OpenAPI Function Schemas)
AGENT_TOOLS_SCHEMA = [
    {
        "name": "tool_query_tasks",
        "description": "Tra cứu danh sách công việc (tasks) trong dự án theo tên người làm, trạng thái, quá hạn hoặc mức độ ưu tiên.",
        "parameters": {
            "type": "object",
            "properties": {
                "assignee_name": {
                    "type": "string",
                    "description": "Tên hoặc email của thành viên cần lọc task (ví dụ: Nam, Lan, admin)",
                },
                "status_group": {
                    "type": "string",
                    "description": "Nhóm trạng thái: backlog, started, completed, cancelled, all",
                },
                "is_overdue": {
                    "type": "boolean",
                    "description": "Chỉ lấy các task đã quá hạn (True/False)",
                },
                "priority": {
                    "type": "string",
                    "description": "Mức ưu tiên: urgent, high, medium, low, none",
                },
            },
        },
    },
    {
        "name": "tool_get_progress",
        "description": "Lấy báo cáo tổng quan về % tiến độ dự án, tổng số task hoàn thành, đang làm và ách tắc.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "tool_get_members_workload",
        "description": "Thống kê danh sách thành viên dự án và số lượng công việc họ đang đảm nhận.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "tool_create_task_with_subtasks",
        "description": "Tạo một task công việc mới trong dự án kèm danh sách các task con (sub-tasks) nếu có.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Tiêu đề của công việc chính",
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả chi tiết công việc",
                },
                "assignee_name": {
                    "type": "string",
                    "description": "Tên thành viên được gán làm việc chính",
                },
                "priority": {
                    "type": "string",
                    "description": "Mức ưu tiên: urgent, high, medium, low",
                },
                "due_date": {
                    "type": "string",
                    "description": "Hạn chót công việc (định dạng YYYY-MM-DD)",
                },
                "subtasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Danh sách các tiêu đề task con (sub-tasks)",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "tool_update_task_status",
        "description": "Cập nhật trạng thái của một công việc (ví dụ: chuyển sang Done, Started, Backlog).",
        "parameters": {
            "type": "object",
            "properties": {
                "sequence_id": {
                    "type": "integer",
                    "description": "Mã số task trong dự án (ví dụ 12 cho task CIV-12)",
                },
                "new_status": {
                    "type": "string",
                    "description": "Trạng thái mới: done, in_progress, backlog, todo",
                },
            },
            "required": ["sequence_id", "new_status"],
        },
    },
]


def execute_query_tasks(project, assignee_name=None, status_group=None, is_overdue=False, priority=None):
    """
    Tra cứu tasks từ Postgres DB thông qua Django ORM.
    """
    queryset = Issue.objects.filter(project=project, deleted_at__isnull=True).select_related("state", "project")

    if assignee_name:
        assignee_query = Q(assignees__first_name__icontains=assignee_name) | Q(assignees__email__icontains=assignee_name) | Q(assignees__display_name__icontains=assignee_name)
        queryset = queryset.filter(assignee_query)

    if status_group:
        sg = status_group.lower()
        if sg in ["started", "in_progress", "in progress"]:
            queryset = queryset.filter(state__group="started")
        elif sg in ["completed", "done"]:
            queryset = queryset.filter(state__group="completed")
        elif sg in ["backlog", "unstarted", "todo"]:
            queryset = queryset.filter(state__group__in=["backlog", "unstarted"])

    if is_overdue:
        today = timezone.now().date()
        queryset = queryset.filter(target_date__lt=today).exclude(state__group="completed")

    if priority:
        queryset = queryset.filter(priority__iexact=priority)

    tasks = list(queryset[:15])

    items = []
    for t in tasks:
        assignees = [a.display_name or a.first_name or a.email for a in t.assignees.all()]
        items.append({
            "sequence_id": t.sequence_id,
            "project_identifier": project.identifier,
            "key": f"{project.identifier}-{t.sequence_id}",
            "name": t.name,
            "status": t.state.name if t.state else "N/A",
            "status_group": t.state.group if t.state else "backlog",
            "priority": t.priority or "none",
            "target_date": str(t.target_date) if t.target_date else None,
            "assignees": assignees,
        })

    return {
        "count": len(items),
        "total_matched": queryset.count(),
        "tasks": items,
    }


def execute_get_progress(project, workspace_slug=""):
    """
    Tính % tiến độ & tổng quan dự án.
    """
    all_issues = Issue.objects.filter(project=project, deleted_at__isnull=True).select_related("state")
    total_count = all_issues.count()
    completed_count = all_issues.filter(state__group="completed").count()
    started_count = all_issues.filter(state__group="started").count()
    backlog_count = all_issues.filter(state__group__in=["backlog", "unstarted"]).count()

    today = timezone.now().date()
    overdue_count = all_issues.filter(target_date__lt=today).exclude(state__group="completed").count()

    percent = round((completed_count / total_count * 100)) if total_count > 0 else 0

    return {
        "project_name": project.name,
        "project_identifier": project.identifier,
        "total_tasks": total_count,
        "completed_tasks": completed_count,
        "started_tasks": started_count,
        "backlog_tasks": backlog_count,
        "overdue_tasks": overdue_count,
        "completion_percentage": percent,
    }


def execute_get_members_workload(project):
    """
    Thống kê danh sách thành viên và công việc đang nắm giữ.
    """
    memberships = ProjectMember.objects.filter(project=project, deleted_at__isnull=True).select_related("member")
    
    result = []
    for pm in memberships:
        u = pm.member
        assigned_issues = Issue.objects.filter(project=project, assignees=u, deleted_at__isnull=True).select_related("state")
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
        "project_name": project.name,
        "total_members": len(result),
        "members": result,
    }


def execute_create_task_with_subtasks(project, created_by_user, title, description="", assignee_name=None, priority="medium", due_date=None, subtasks=None):
    """
    Tạo Task chính + Các Sub-tasks con qua Django ORM.
    """
    default_state = State.objects.filter(project=project, group="backlog", deleted_at__isnull=True).first()
    if not default_state:
        default_state = State.objects.filter(project=project, deleted_at__isnull=True).first()

    # Create Parent Task
    parent_issue = Issue.objects.create(
        project=project,
        workspace=project.workspace,
        name=title,
        description_html=f"<p>{description}</p>" if description else "<p></p>",
        state=default_state,
        priority=priority.lower(),
        created_by=created_by_user,
    )

    if due_date:
        try:
            parent_issue.target_date = due_date
            parent_issue.save(update_fields=["target_date"])
        except Exception:
            pass

    assigned_user = None
    if assignee_name:
        assigned_user = User.objects.filter(
            Q(first_name__icontains=assignee_name) | Q(email__icontains=assignee_name) | Q(display_name__icontains=assignee_name)
        ).first()

        if assigned_user:
            IssueAssignee.objects.create(
                issue=parent_issue,
                assignee=assigned_user,
                project=project,
                workspace=project.workspace,
            )

    # Create Subtasks if specified
    created_subtasks = []
    if subtasks and isinstance(subtasks, list):
        for sub_title in subtasks:
            sub_issue = Issue.objects.create(
                project=project,
                workspace=project.workspace,
                parent=parent_issue,
                name=sub_title,
                state=default_state,
                priority=priority.lower(),
                created_by=created_by_user,
            )
            if assigned_user:
                IssueAssignee.objects.create(
                    issue=sub_issue,
                    assignee=assigned_user,
                    project=project,
                    workspace=project.workspace,
                )
            created_subtasks.append({
                "sequence_id": sub_issue.sequence_id,
                "key": f"{project.identifier}-{sub_issue.sequence_id}",
                "title": sub_issue.name,
            })

    return {
        "success": True,
        "task_key": f"{project.identifier}-{parent_issue.sequence_id}",
        "sequence_id": parent_issue.sequence_id,
        "title": parent_issue.name,
        "assignee": assigned_user.display_name or assigned_user.email if assigned_user else "Unassigned",
        "priority": parent_issue.priority,
        "subtasks": created_subtasks,
    }


def execute_update_task_status(project, sequence_id, new_status):
    """
    Cập nhật trạng thái task.
    """
    issue = Issue.objects.filter(project=project, sequence_id=sequence_id, deleted_at__isnull=True).first()
    if not issue:
        return {"success": False, "error": f"Task {project.identifier}-{sequence_id} not found."}

    ns = new_status.lower()
    target_group = "backlog"
    if ns in ["done", "completed", "complete"]:
        target_group = "completed"
    elif ns in ["in_progress", "started", "in progress"]:
        target_group = "started"

    target_state = State.objects.filter(project=project, group=target_group, deleted_at__isnull=True).first()
    if not target_state:
        target_state = State.objects.filter(project=project, deleted_at__isnull=True).first()

    issue.state = target_state
    issue.save(update_fields=["state"])

    return {
        "success": True,
        "task_key": f"{project.identifier}-{issue.sequence_id}",
        "title": issue.name,
        "new_status": target_state.name,
        "group": target_state.group,
    }
