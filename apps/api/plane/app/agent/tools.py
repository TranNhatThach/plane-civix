import logging
from typing import Optional, List, Dict, Any
from django.utils import timezone
from django.db.models import Q
from plane.db.models import (
    Issue,
    State,
    IssueAssignee,
    ProjectMember,
    User,
    Project,
    Cycle,
    CycleIssue,
    Label,
    IssueLabel,
)

logger = logging.getLogger(__name__)


def tool_list_projects(workspace_slug: Optional[str] = None) -> Dict[str, Any]:
    """Tra cứu danh sách tất cả các dự án (Projects) đang có trong hệ thống Plane.

    Args:
        workspace_slug: Mã slug của Workspace (nếu có).

    Returns:
        Dict chứa số lượng và danh sách chi tiết các dự án.
    """
    queryset = Project.objects.filter(deleted_at__isnull=True).select_related("workspace")
    if workspace_slug:
        queryset = queryset.filter(workspace__slug=workspace_slug)

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


def tool_query_tasks(
    project_id: str,
    assignee_name: Optional[str] = None,
    status_group: Optional[str] = None,
    is_overdue: bool = False,
    priority: Optional[str] = None,
) -> Dict[str, Any]:
    """Tra cứu danh sách công việc (tasks) trong dự án theo tên người làm, trạng thái, quá hạn hoặc mức độ ưu tiên.

    Args:
        project_id: ID UUID của dự án Plane.
        assignee_name: Tên hoặc email của thành viên cần lọc task (ví dụ: Nam, Lan, admin).
        status_group: Nhóm trạng thái (backlog, started, completed, all).
        is_overdue: True nếu chỉ tìm các task đã quá hạn.
        priority: Mức ưu tiên (urgent, high, medium, low).

    Returns:
        Dict chứa số lượng task và danh sách chi tiết các công việc.
    """
    queryset = Issue.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("state", "project")

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
    if not tasks and not (assignee_name or status_group or is_overdue or priority):
        # Fallback to any active project that has tasks in system
        active_project = Project.objects.filter(deleted_at__isnull=True, issues__deleted_at__isnull=True).distinct().first()
        if active_project:
            queryset = Issue.objects.filter(project=active_project, deleted_at__isnull=True).select_related("state", "project")
            tasks = list(queryset[:15])

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


def tool_get_progress(project_id: str) -> Dict[str, Any]:
    """Lấy báo cáo tổng quan về phần trăm tiến độ dự án, tổng số task hoàn thành, đang làm và ách tắc.

    Args:
        project_id: ID UUID của dự án Plane.

    Returns:
        Dict chứa thống kê phần trăm tiến độ và chi tiết số lượng task.
    """
    all_issues = Issue.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("state", "project")
    project = all_issues.first().project if all_issues.exists() else None
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


def tool_get_members_workload(project_id: str) -> Dict[str, Any]:
    """Thống kê danh sách thành viên dự án và số lượng công việc họ đang đảm nhận.

    Args:
        project_id: ID UUID của dự án Plane.

    Returns:
        Dict chứa danh sách thành viên và khối lượng công việc tương ứng.
    """
    memberships = ProjectMember.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("member", "project")
    project = memberships.first().project if memberships.exists() else None
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


def tool_create_task_with_subtasks(
    project_id: str,
    title: str,
    description: str = "",
    assignee_name: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None,
    subtasks: Optional[List[str]] = None,
    created_by_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Tạo một task công việc mới trong dự án kèm danh sách các task con (sub-tasks) nếu có.

    Args:
        project_id: ID UUID của dự án Plane.
        title: Tiêu đề công việc chính.
        description: Mô tả chi tiết công việc.
        assignee_name: Tên hoặc email người được gán việc.
        priority: Mức ưu tiên (urgent, high, medium, low).
        due_date: Hạn chót định dạng YYYY-MM-DD.
        subtasks: Danh sách các tiêu đề task con.
        created_by_user_id: ID của người dùng khởi tạo.

    Returns:
        Dict thông báo kết quả tạo task.
    """
    from plane.db.models import Project
    project = Project.objects.get(pk=project_id)
    created_by_user = User.objects.filter(pk=created_by_user_id).first() if created_by_user_id else project.workspace.owner

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


def tool_update_task_status(
    project_id: str,
    sequence_id: int,
    new_status: str,
) -> Dict[str, Any]:
    """Cập nhật trạng thái của một công việc (ví dụ chuyển sang Done, In Progress, Backlog).

    Args:
        project_id: ID UUID của dự án Plane.
        sequence_id: Mã số thứ tự của task (ví dụ 12 trong CIV-12).
        new_status: Trạng thái mới (done, in_progress, backlog, todo).

    Returns:
        Dict thông báo kết quả cập nhật trạng thái.
    """
    issue = Issue.objects.filter(project_id=project_id, sequence_id=sequence_id, deleted_at__isnull=True).first()
    if not issue:
        return {"success": False, "error": f"Task {sequence_id} not found."}

    ns = new_status.lower()
    target_group = "backlog"
    if ns in ["done", "completed", "complete"]:
        target_group = "completed"
    elif ns in ["in_progress", "started", "in progress"]:
        target_group = "started"

    target_state = State.objects.filter(project_id=project_id, group=target_group, deleted_at__isnull=True).first()
    if not target_state:
        target_state = State.objects.filter(project_id=project_id, deleted_at__isnull=True).first()

    issue.state = target_state
    issue.save(update_fields=["state"])

    return {
        "success": True,
        "task_key": f"{issue.project.identifier}-{issue.sequence_id}",
        "title": issue.name,
        "new_status": target_state.name,
        "group": target_state.group,
    }


def tool_manage_cycles(
    project_id: str,
    action: str = "list",
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Quản lý các đợt Sprint/Cycle của dự án (xem danh sách hoặc tạo Cycle mới).

    Args:
        project_id: ID UUID của dự án Plane.
        action: Hành động ("list" hoặc "create").
        name: Tên của Cycle (nếu action="create").
        description: Mô tả Cycle (tùy chọn).

    Returns:
        Dict thông tin danh sách Cycle hoặc kết quả tạo Cycle mới.
    """
    project = Project.objects.filter(id=project_id, deleted_at__isnull=True).first()
    if not project:
        return {"success": False, "error": f"Project {project_id} not found."}

    if action.lower() == "create" and name:
        cycle = Cycle.objects.create(
            name=name,
            description=description or "",
            project=project,
            workspace=project.workspace,
            owned_by=project.created_by,
        )
        return {
            "success": True,
            "action": "create",
            "cycle_id": str(cycle.id),
            "name": cycle.name,
            "project_name": project.name,
        }

    # Default action: list
    cycles = list(Cycle.objects.filter(project_id=project_id, deleted_at__isnull=True).order_by("-created_at")[:10])
    items = []
    for c in cycles:
        issue_count = CycleIssue.objects.filter(cycle=c, deleted_at__isnull=True).count()
        items.append({
            "id": str(c.id),
            "name": c.name,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "issue_count": issue_count,
        })

    return {
        "success": True,
        "action": "list",
        "count": len(items),
        "cycles": items,
        "project_name": project.name,
    }


def tool_rebalance_workload(
    project_id: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Phân tích các task trễ hạn/dở dang của những người bận nhất để tái phân bổ cho thành viên rảnh nhất.

    Args:
        project_id: ID UUID của dự án Plane.
        dry_run: True nếu chỉ phân tích & đề xuất (chưa thực hiện đổi assignee), False nếu thực hiện đổi trực tiếp.

    Returns:
        Dict chứa thông tin phân tích và các đề xuất/kết quả chuyển giao task.
    """
    project = Project.objects.filter(id=project_id, deleted_at__isnull=True).first()
    if not project:
        return {"success": False, "error": f"Project {project_id} not found."}

    # Get project members
    pm_list = list(ProjectMember.objects.filter(project_id=project_id, deleted_at__isnull=True).select_related("member"))
    if not pm_list:
        return {"success": False, "error": "No project members found."}

    # Count active in-progress tasks per member
    workload = {}
    for pm in pm_list:
        if pm.member:
            active_cnt = IssueAssignee.objects.filter(
                issue__project_id=project_id,
                assignee=pm.member,
                issue__deleted_at__isnull=True,
                issue__state__group="started",
            ).count()
            workload[pm.member] = active_cnt

    if not workload:
        return {"success": True, "rebalanced": False, "message": "Không có thành viên nào để phân bổ lại."}

    sorted_members = sorted(workload.items(), key=lambda x: x[1])
    least_busy_member, min_tasks = sorted_members[0]
    most_busy_member, max_tasks = sorted_members[-1]

    # Find overdue or started tasks assigned to most busy member
    today = timezone.now().date()
    overdue_issues = list(
        Issue.objects.filter(
            project_id=project_id,
            assignees=most_busy_member,
            deleted_at__isnull=True,
        ).filter(Q(target_date__lt=today) | Q(state__group="started")).exclude(state__group="completed")[:3]
    )

    reassigned_items = []
    for issue in overdue_issues:
        item_info = {
            "key": f"{project.identifier}-{issue.sequence_id}",
            "title": issue.name,
            "from_user": most_busy_member.display_name or most_busy_member.email,
            "to_user": least_busy_member.display_name or least_busy_member.email,
        }
        if not dry_run:
            IssueAssignee.objects.filter(issue=issue).delete()
            IssueAssignee.objects.create(
                issue=issue,
                assignee=least_busy_member,
                project=project,
                workspace=project.workspace,
            )
        reassigned_items.append(item_info)

    return {
        "success": True,
        "dry_run": dry_run,
        "project_name": project.name,
        "most_busy": most_busy_member.display_name or most_busy_member.email,
        "least_busy": least_busy_member.display_name or least_busy_member.email,
        "reassigned_count": len(reassigned_items),
        "reassigned_tasks": reassigned_items,
    }


def tool_export_report(project_id: str) -> Dict[str, Any]:
    """Xuất báo cáo tình hình dự án tổng hợp dưới dạng văn bản Markdown định dạng đẹp.

    Args:
        project_id: ID UUID của dự án Plane.

    Returns:
        Dict chứa văn bản báo cáo Markdown và dữ liệu tóm tắt.
    """
    project = Project.objects.filter(id=project_id, deleted_at__isnull=True).first()
    if not project:
        return {"success": False, "error": f"Project {project_id} not found."}

    total_issues = Issue.objects.filter(project=project, deleted_at__isnull=True).count()
    completed_issues = Issue.objects.filter(project=project, state__group="completed", deleted_at__isnull=True).count()
    started_issues = Issue.objects.filter(project=project, state__group="started", deleted_at__isnull=True).count()
    today = timezone.now().date()
    overdue_issues = Issue.objects.filter(project=project, target_date__lt=today, deleted_at__isnull=True).exclude(state__group="completed").count()

    pct = round((completed_issues / total_issues * 100), 1) if total_issues > 0 else 0.0

    report_md = (
        f"# 📊 BÁO CÁO DỰ ÁN: {project.name.upper()} (`{project.identifier}`)\n\n"
        f"**Ngày xuất báo cáo**: {today.strftime('%d/%m/%Y')}\n\n"
        f"---\n\n"
        f"### 📈 1. Báo Cáo Tiến Độ Chuyển Đổi\n"
        f"- **Mức độ hoàn thành**: `{pct}%`\n"
        f"- **Tổng số task**: {total_issues}\n"
        f"- **Đã hoàn thành**: {completed_issues}\n"
        f"- **Đang thực hiện**: {started_issues}\n"
        f"- **Cần chú ý (Quá hạn)**: {overdue_issues}\n\n"
        f"---\n\n"
        f"*(Báo cáo được khởi tạo tự động bởi Plane Core AI Assistant)*"
    )

    return {
        "success": True,
        "project_name": project.name,
        "report_markdown": report_md,
        "completion_percentage": pct,
        "total_issues": total_issues,
        "overdue_issues": overdue_issues,
    }


def tool_tag_labels(
    project_id: str,
    sequence_id: int,
    label_name: str,
) -> Dict[str, Any]:
    """Gán nhãn (Label) cho một task trong dự án.

    Args:
        project_id: ID UUID của dự án Plane.
        sequence_id: Mã số thứ tự của task (ví dụ 12 trong CIV-12).
        label_name: Tên nhãn (ví dụ: bug, frontend, urgent).

    Returns:
        Dict kết quả gán nhãn cho task.
    """
    issue = Issue.objects.filter(project_id=project_id, sequence_id=sequence_id, deleted_at__isnull=True).first()
    if not issue:
        return {"success": False, "error": f"Task {sequence_id} not found."}

    label, _ = Label.objects.get_or_create(
        name=label_name.strip(),
        workspace=issue.workspace,
        defaults={"project": issue.project},
    )

    IssueLabel.objects.get_or_create(
        issue=issue,
        label=label,
        defaults={"project": issue.project, "workspace": issue.workspace},
    )

    return {
        "success": True,
        "task_key": f"{issue.project.identifier}-{issue.sequence_id}",
        "task_title": issue.name,
        "label_name": label.name,
    }

