import logging
from typing import Dict, Any, Optional
from plane.db.models import Cycle, Project
from plane.app.agent.registry import agent_tool

logger = logging.getLogger(__name__)


@agent_tool(
    name="tool_manage_cycles",
    description="Xem hoặc quản lý danh sách các Sprint / Cycle của dự án.",
    parameters_schema={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
            "action": {"type": "string", "enum": ["list", "create"], "description": "Hành động (list hoặc create)."},
            "name": {"type": "string", "description": "Tên Cycle khi tạo mới."}
        },
        "required": []
    }
)
def tool_manage_cycles(
    project_id: str,
    action: str = "list",
    name: Optional[str] = None
) -> Dict[str, Any]:
    project = Project.objects.filter(pk=project_id).first()
    proj_name = project.name if project else "Dự án"

    if action == "create" and name:
        owner = (project.workspace.owner if project and project.workspace else None) or (project.created_by if project else None)
        cycle = Cycle.objects.create(
            name=name,
            project=project,
            workspace=project.workspace,
            owned_by=owner,
            created_by=owner,
        )

        return {
            "success": True,
            "action": "create",
            "project_name": proj_name,
            "cycle_id": str(cycle.id),
            "name": cycle.name,
            "cycle_name": cycle.name,
        }


    cycles = Cycle.objects.filter(project_id=project_id, deleted_at__isnull=True)
    items = []
    for c in cycles:
        items.append({
            "id": str(c.id),
            "name": c.name,
            "issue_count": c.issue_cycle.count(),
        })

    return {
        "success": True,
        "action": "list",
        "project_name": proj_name,
        "count": len(items),
        "cycles": items,
    }
