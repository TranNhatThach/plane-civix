import logging
from typing import Optional, List, Dict, Any
from django.utils import timezone
from django.db.models import Q
from plane.db.models import Issue, State, User, Project, Label, IssueLabel, IssueAssignee
from plane.app.agent.registry import agent_tool
from plane.app.agent.core.scope_guard import scope_guard

logger = logging.getLogger(__name__)


@agent_tool(
    name="tool_query_tasks",
    description="Tra cứu danh sách công việc (tasks) trong dự án hoặc trên toàn bộ Workspace theo người làm, trạng thái, quá hạn, ưu tiên.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane (bỏ trống nếu muốn tra cứu toàn workspace)."},
            "assignee_name": {"type": "string", "description": "Tên hoặc email của thành viên cần lọc task."},
            "status_group": {"type": "string", "enum": ["backlog", "started", "completed", "all"], "description": "Nhóm trạng thái công việc."},
            "is_overdue": {"type": "boolean", "description": "True nếu chỉ tìm các công việc đã quá hạn."},
            "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"], "description": "Mức độ ưu tiên."},
            "month": {"type": "integer", "description": "Số tháng cần lọc (từ 1 đến 12). Ví dụ 8 cho tháng 8."},
            "year": {"type": "integer", "description": "Năm cần lọc (ví dụ 2026)."}
        },
        "required": []
    }
)
@scope_guard(requires_project=False)
def tool_query_tasks(
    project_id: Optional[str] = None,
    assignee_name: Optional[str] = None,
    status_group: Optional[str] = None,
    is_overdue: bool = False,
    priority: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    queryset = Issue.objects.filter(deleted_at__isnull=True).select_related("state", "project", "workspace")

    if project_id:
        queryset = queryset.filter(project_id=project_id)
    elif workspace_id:
        queryset = queryset.filter(workspace_id=workspace_id)
        if _context and getattr(_context, "accessible_project_ids", None):
            queryset = queryset.filter(project_id__in=_context.accessible_project_ids)


    if assignee_name:
        clean_name = assignee_name.lstrip("@").strip()
        assignee_query = (
            Q(assignees__first_name__icontains=clean_name)
            | Q(assignees__email__icontains=clean_name)
            | Q(assignees__display_name__icontains=clean_name)
            | Q(assignees__username__icontains=clean_name)
        )
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

    if month:
        current_year = year or timezone.now().year
        date_query = (
            Q(target_date__month=month, target_date__year=current_year)
            | Q(created_at__month=month, created_at__year=current_year)
            | Q(start_date__month=month, start_date__year=current_year)
        )
        queryset = queryset.filter(date_query)
    elif year:
        date_query = (
            Q(target_date__year=year)
            | Q(created_at__year=year)
            | Q(start_date__year=year)
        )
        queryset = queryset.filter(date_query)

    tasks = list(queryset[:100])

    items = []
    for t in tasks:
        assignees = [a.display_name or a.first_name or a.email for a in t.assignees.all()]
        items.append({
            "sequence_id": t.sequence_id,
            "project_identifier": t.project.identifier if t.project else "",
            "key": f"{t.project.identifier if t.project else 'TASK'}-{t.sequence_id}",
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


@agent_tool(
    name="tool_create_task_with_subtasks",
    description="Tạo một công việc (task) mới trong dự án kèm danh sách các task con (sub-tasks).",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
            "title": {"type": "string", "description": "Tiêu đề công việc."},
            "description": {"type": "string", "description": "Mô tả công việc."},
            "assignee_name": {"type": "string", "description": "Tên người làm công việc (ví dụ: Nam, Minh, email...)."},
            "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"], "description": "Mức độ ưu tiên."},
            "due_date": {"type": "string", "description": "Hạn chót công việc (YYYY-MM-DD)."},
            "subtasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách tiêu đề các công việc con (subtasks)."
            }
        },
        "required": ["title"]
    }
)
@scope_guard(requires_project=False)
def tool_create_task_with_subtasks(
    title: str,
    project_id: Optional[str] = None,
    description: str = "",
    assignee_name: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None,
    subtasks: Optional[List[str]] = None,
    created_by_user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    project = None
    if project_id and str(project_id).strip() not in ["None", "null", ""]:
        project = Project.objects.filter(pk=project_id, deleted_at__isnull=True).first()

    if not project and _context and getattr(_context, "project_id", None):
        project = Project.objects.filter(pk=_context.project_id, deleted_at__isnull=True).first()

    if not project and _context and getattr(_context, "accessible_project_ids", None):
        p_ids = _context.accessible_project_ids
        if p_ids:
            project = Project.objects.filter(pk=p_ids[0], deleted_at__isnull=True).first()

    if not project and workspace_id:
        project = Project.objects.filter(workspace_id=workspace_id, deleted_at__isnull=True).first()

    if not project:
        project = Project.objects.filter(deleted_at__isnull=True).first()

    if not project:
        return {"success": False, "error": "Hệ thống chưa có dự án nào để tạo công việc."}

    created_by_user = User.objects.filter(pk=created_by_user_id).first() if created_by_user_id else project.workspace.owner

    default_state = State.objects.filter(project=project, group="backlog", deleted_at__isnull=True).first()
    if not default_state:
        default_state = State.objects.filter(project=project, deleted_at__isnull=True).first()

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
        clean_name = assignee_name.lstrip("@").strip()
        assigned_user = User.objects.filter(
            Q(first_name__icontains=clean_name) | Q(email__icontains=clean_name) | Q(display_name__icontains=clean_name) | Q(username__icontains=clean_name)
        ).first()

        if assigned_user:
            IssueAssignee.objects.create(
                issue=parent_issue,
                assignee=assigned_user,
                project=project,
                workspace=project.workspace,
                created_by=created_by_user,
            )

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
                    created_by=created_by_user,
                )
            created_subtasks.append({
                "key": f"{project.identifier}-{sub_issue.sequence_id}",
                "title": sub_issue.name,
            })

    return {
        "success": True,
        "task_id": str(parent_issue.id),
        "task_key": f"{project.identifier}-{parent_issue.sequence_id}",
        "title": parent_issue.name,
        "assignee": assigned_user.display_name if assigned_user else (assignee_name or "Chưa gán"),
        "priority": parent_issue.priority,
        "due_date": str(parent_issue.target_date) if parent_issue.target_date else None,
        "subtasks_count": len(created_subtasks),
        "subtasks": created_subtasks,
    }


@agent_tool(
    name="tool_update_task_status",
    description="Cập nhật trạng thái hoặc thông tin của một task theo mã task key (ví dụ: CIVIX-10) hoặc sequence_id.",
    parameters_schema={
        "type": "object",
        "properties": {
            "task_key": {"type": "string", "description": "Mã công việc, ví dụ: CIVIX-10."},
            "project_id": {"type": "string", "description": "ID UUID của dự án."},
            "sequence_id": {"type": "integer", "description": "Số sequence_id của task."},
            "status": {"type": "string", "description": "Tên hoặc nhóm trạng thái mới."},
            "new_status": {"type": "string", "description": "Tên hoặc nhóm trạng thái mới."},
            "assignee_name": {"type": "string", "description": "Tên người được đổi gán việc."}
        },
        "required": []
    }
)
@scope_guard(requires_project=False)
def tool_update_task_status(
    task_key: str = "",
    status: Optional[str] = None,
    assignee_name: Optional[str] = None,
    project_id: Optional[str] = None,
    sequence_id: Optional[int] = None,
    new_status: Optional[str] = None,
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    _issue_instance: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    eff_status = status or new_status
    issue = _issue_instance

    if not issue and task_key:
        parts = task_key.strip().split("-")
        if len(parts) >= 2:
            proj_identifier, seq_id_str = parts[0], parts[1]
            try:
                seq_id = int(seq_id_str)
                issue = Issue.objects.filter(
                    project__identifier__iexact=proj_identifier,
                    sequence_id=seq_id,
                    deleted_at__isnull=True,
                ).first()
            except ValueError:
                pass

    if not issue and project_id and sequence_id:
        issue = Issue.objects.filter(
            project_id=project_id,
            sequence_id=sequence_id,
            deleted_at__isnull=True,
        ).first()

    if not issue:
        return {"success": False, "error": "Không tìm thấy công việc để cập nhật."}

    updated_fields = []

    if eff_status:
        st_lower = eff_status.lower()
        target_state = None
        if st_lower in ["completed", "done", "hoàn thành", "xong"]:
            target_state = State.objects.filter(project=issue.project, group="completed", deleted_at__isnull=True).first()
        elif st_lower in ["started", "in_progress", "in progress", "đang làm"]:
            target_state = State.objects.filter(project=issue.project, group="started", deleted_at__isnull=True).first()
        elif st_lower in ["backlog", "todo", "chưa làm", "unstarted"]:
            target_state = State.objects.filter(project=issue.project, group__in=["backlog", "unstarted"], deleted_at__isnull=True).first()
        else:
            target_state = State.objects.filter(project=issue.project, name__icontains=eff_status, deleted_at__isnull=True).first()

        if target_state:
            issue.state = target_state
            issue.save(update_fields=["state"])
            updated_fields.append(f"trạng thái ➔ '{target_state.name}'")

    if assignee_name:
        user = User.objects.filter(
            Q(first_name__icontains=assignee_name) | Q(email__icontains=assignee_name) | Q(display_name__icontains=assignee_name)
        ).first()

        if user:
            IssueAssignee.objects.filter(issue=issue).delete()
            IssueAssignee.objects.create(
                issue=issue,
                assignee=user,
                project=issue.project,
                workspace=issue.workspace,
                created_by=issue.created_by,
            )
            updated_fields.append(f"người phụ trách ➔ @{user.display_name or user.first_name}")

    eff_key = task_key if task_key else f"{issue.project.identifier}-{issue.sequence_id}"
    return {
        "success": True,
        "task_key": eff_key,
        "new_status": issue.state.name if issue.state else eff_status,
        "updated_fields": updated_fields,
        "message": f"Đã cập nhật công việc [{eff_key}]: {', '.join(updated_fields)}" if updated_fields else "Không có thay đổi nào.",
    }



@agent_tool(
    name="tool_tag_labels",
    description="Gán nhãn (Label) cho công việc.",
    parameters_schema={
        "type": "object",
        "properties": {
            "task_key": {"type": "string", "description": "Mã task, ví dụ CIVIX-5."},
            "project_id": {"type": "string", "description": "ID UUID của dự án."},
            "sequence_id": {"type": "integer", "description": "Số sequence_id của task."},
            "label_name": {"type": "string", "description": "Tên nhãn cần gán."}
        },
        "required": ["label_name"]
    }
)
@scope_guard(requires_project=False)
def tool_tag_labels(
    task_key: str = "",
    label_name: str = "",
    project_id: Optional[str] = None,
    sequence_id: Optional[int] = None,
    workspace_id: Optional[str] = None,
    _context: Optional[Any] = None,
    _issue_instance: Optional[Any] = None,
    **kwargs,
) -> Dict[str, Any]:
    issue = _issue_instance

    if not issue and task_key:
        parts = task_key.strip().split("-")
        if len(parts) >= 2:
            proj_identifier, seq_id_str = parts[0], parts[1]
            try:
                seq_id = int(seq_id_str)
                issue = Issue.objects.filter(
                    project__identifier__iexact=proj_identifier,
                    sequence_id=seq_id,
                    deleted_at__isnull=True,
                ).first()
            except ValueError:
                pass

    if not issue and project_id and sequence_id:
        issue = Issue.objects.filter(
            project_id=project_id,
            sequence_id=sequence_id,
            deleted_at__isnull=True,
        ).first()

    if not issue:
        return {"success": False, "error": "Không tìm thấy task để gán nhãn."}

    label, _ = Label.objects.get_or_create(
        name=label_name,
        project=issue.project,
        workspace=issue.workspace,
    )
    IssueLabel.objects.get_or_create(
        issue=issue,
        label=label,
        project=issue.project,
        workspace=issue.workspace,
    )
    eff_key = task_key if task_key else f"{issue.project.identifier}-{issue.sequence_id}"
    return {
        "success": True,
        "task_key": eff_key,
        "label_name": label.name,
        "message": f"Đã gán nhãn '{label.name}' cho task [{eff_key}].",
    }

