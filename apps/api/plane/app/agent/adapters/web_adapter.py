from typing import Dict, Any


def render_web_response(agent_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapts Plane Core Agent Engine JSON result for Plane Web UI & Rest API endpoints.
    """
    return {
        "status": "success",
        "action_taken": agent_result.get("action_taken", ""),
        "message": agent_result.get("text", ""),
        "data": agent_result.get("data", {}),
        "requires_confirmation": agent_result.get("requires_confirmation", False),
        "pending_action": agent_result.get("pending_action", None),
    }
