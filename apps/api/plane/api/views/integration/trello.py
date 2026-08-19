# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import re
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from plane.app.views.base import BaseAPIView
from plane.authentication.session import BaseSessionAuthentication
from plane.api.middleware.api_authentication import APIKeyAuthentication
from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Project, Workspace, Issue, State, Label, IssueLabel
from plane.db.models.state import StateGroup


def map_trello_color(trello_color: str) -> str:
    color_map = {
        "green": "#46A758",
        "yellow": "#F59E0B",
        "orange": "#F97316",
        "red": "#E54D2E",
        "purple": "#8E4EC6",
        "blue": "#0090FF",
        "sky": "#00A2C7",
        "lime": "#99D52A",
        "pink": "#E54666",
        "black": "#1F2937",
    }
    return color_map.get((trello_color or "").lower(), "#60646C")


def determine_state_group_and_color(name: str):
    lower_name = (name or "").lower()
    if any(k in lower_name for k in ["done", "hoàn thành", "xong", "completed", "finished", "closed"]):
        return StateGroup.COMPLETED.value, "#46A758"
    elif any(k in lower_name for k in ["doing", "in progress", "đang làm", "đang thực hiện", "progress", "review", "testing", "qa"]):
        return StateGroup.STARTED.value, "#F59E0B"
    elif any(k in lower_name for k in ["cancel", "hủy", "dropped", "archived"]):
        return StateGroup.CANCELLED.value, "#9AA4BC"
    elif any(k in lower_name for k in ["backlog", "ideas", "icebox", "ý tưởng", "chờ duyệt"]):
        return StateGroup.BACKLOG.value, "#60646C"
    else:
        return StateGroup.UNSTARTED.value, "#60646C"


def clean_html_desc(desc: str, checklists_html: str = "") -> str:
    if not desc and not checklists_html:
        return "<p></p>"
    
    parts = []
    if desc:
        paragraphs = desc.split("\n\n")
        for p in paragraphs:
            p_clean = p.strip().replace("\n", "<br/>")
            if p_clean:
                parts.append(f"<p>{p_clean}</p>")
    
    if checklists_html:
        if parts:
            parts.append("<hr/>")
        parts.append(checklists_html)
        
    return "".join(parts) or "<p></p>"


def generate_project_identifier(name: str, workspace: Workspace) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name.upper())
    if not words:
        base = "PROJ"
    elif len(words) == 1:
        base = words[0][:5]
    else:
        base = "".join(w[0] for w in words)[:5]

    if len(base) < 2:
        base = (base + "PR")[:3]

    candidate = base
    counter = 1
    while Project.objects.filter(workspace=workspace, identifier=candidate).exists():
        candidate = f"{base[:3]}{counter}"
        counter += 1

    return candidate


class TrelloImportEndpoint(BaseAPIView):
    """
    API endpoint to import Trello Board JSON export into a Plane Project.
    """

    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, project_id):
        # 1. Parse Trello JSON payload
        trello_data = None
        if "file" in request.FILES:
            try:
                uploaded_file = request.FILES["file"]
                trello_data = json.loads(uploaded_file.read().decode("utf-8"))
            except Exception as e:
                return Response(
                    {"error": f"Invalid JSON file format: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif "data" in request.data:
            data_field = request.data["data"]
            if isinstance(data_field, str):
                try:
                    trello_data = json.loads(data_field)
                except Exception as e:
                    return Response(
                        {"error": f"Invalid JSON string in 'data': {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif isinstance(data_field, dict):
                trello_data = data_field
        elif isinstance(request.data, dict) and "cards" in request.data:
            trello_data = request.data

        if not trello_data or not isinstance(trello_data, dict):
            return Response(
                {"error": "Please provide a valid Trello JSON export (via file upload or 'data' field)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Get Workspace
        try:
            workspace = Workspace.objects.get(slug=slug)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)

        # 3. Determine Target Project
        target_project_id = request.data.get("target_project_id") or project_id
        create_new_project = str(request.data.get("create_new_project", "false")).lower() in ["true", "1"]
        board_name = trello_data.get("name", "Trello Import").strip() or "Trello Import"

        user = request.user if request.user and request.user.is_authenticated else workspace.owner

        project = None
        if create_new_project or str(target_project_id).lower() == "new":
            proj_identifier = generate_project_identifier(board_name, workspace)
            project = Project.objects.create(
                workspace=workspace,
                name=board_name,
                identifier=proj_identifier,
                description=trello_data.get("desc", ""),
                created_by=user,
                updated_by=user,
            )
        else:
            if str(target_project_id).lower() == "global":
                # Find first project or create one if none exists
                project = Project.objects.filter(workspace=workspace).first()
                if not project:
                    proj_identifier = generate_project_identifier(board_name, workspace)
                    project = Project.objects.create(
                        workspace=workspace,
                        name=board_name,
                        identifier=proj_identifier,
                        created_by=user,
                        updated_by=user,
                    )
            else:
                try:
                    project = Project.objects.get(pk=target_project_id, workspace=workspace)
                except (Project.DoesNotExist, ValueError, ValidationError):
                    return Response(
                        {"error": f"Target project '{target_project_id}' not found in workspace."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        include_closed = str(request.data.get("include_closed", "false")).lower() in ["true", "1"]

        # 4. Perform Import inside Database Transaction
        try:
            with transaction.atomic():
                # A. Parse Checklists
                checklists_by_id = {}
                for cl in trello_data.get("checklists", []):
                    items = cl.get("checkItems", [])
                    items_html = []
                    for it in items:
                        check_mark = "☑" if it.get("state") == "complete" else "☐"
                        items_html.append(f"<li>{check_mark} {it.get('name', '')}</li>")
                    checklists_by_id[cl.get("id")] = f"<div><b>{cl.get('name', 'Checklist')}:</b><ul>{''.join(items_html)}</ul></div>"

                # B. Map Trello Lists ➔ Plane States
                trello_lists = trello_data.get("lists", [])
                if not include_closed:
                    trello_lists = [l for l in trello_lists if not l.get("closed", False)]

                list_state_map = {}
                created_states_count = 0

                for idx, l in enumerate(trello_lists):
                    list_name = (l.get("name") or "Unnamed List").strip()
                    state = State.objects.filter(project=project, name__iexact=list_name).first()
                    if not state:
                        group, color = determine_state_group_and_color(list_name)
                        state = State.objects.create(
                            project=project,
                            workspace=workspace,
                            name=list_name,
                            color=color,
                            group=group,
                            sequence=15000 + idx * 10000,
                            created_by=user,
                            updated_by=user,
                        )
                        created_states_count += 1
                    list_state_map[l.get("id")] = state

                default_state = State.objects.filter(project=project).first()

                # C. Map Labels
                trello_labels = trello_data.get("labels", [])
                label_map = {}
                created_labels_count = 0

                for lbl in trello_labels:
                    lbl_name = (lbl.get("name") or lbl.get("color") or "").strip()
                    if not lbl_name:
                        continue
                    plane_label = Label.objects.filter(project=project, name__iexact=lbl_name).first()
                    if not plane_label:
                        plane_label = Label.objects.create(
                            project=project,
                            workspace=workspace,
                            name=lbl_name,
                            color=map_trello_color(lbl.get("color", "")),
                            created_by=user,
                            updated_by=user,
                        )
                        created_labels_count += 1
                    label_map[lbl.get("id")] = plane_label

                # D. Import Cards ➔ Issues
                cards = trello_data.get("cards", [])
                if not include_closed:
                    cards = [c for c in cards if not c.get("closed", False)]

                imported_tasks_count = 0

                for card in cards:
                    card_name = (card.get("name") or "Untitled Task").strip()
                    card_desc = card.get("desc", "")
                    list_id = card.get("idList")
                    state = list_state_map.get(list_id, default_state)

                    # Append checklists into description HTML
                    card_checklists = [
                        checklists_by_id[cid]
                        for cid in card.get("idChecklists", [])
                        if cid in checklists_by_id
                    ]
                    checklists_html = "<br/>".join(card_checklists)
                    desc_html = clean_html_desc(card_desc, checklists_html)

                    # Target Due Date
                    target_date = None
                    if card.get("due"):
                        try:
                            target_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00")).date()
                        except Exception:
                            target_date = None

                    issue = Issue.objects.create(
                        project=project,
                        workspace=workspace,
                        name=card_name,
                        description_html=desc_html,
                        state=state,
                        target_date=target_date,
                        created_by=user,
                        updated_by=user,
                    )

                    # Assign labels
                    for lid in card.get("idLabels", []):
                        if lid in label_map:
                            IssueLabel.objects.create(
                                issue=issue,
                                label=label_map[lid],
                                project=project,
                                workspace=workspace,
                                created_by=user,
                                updated_by=user,
                            )

                    imported_tasks_count += 1

                return Response(
                    {
                        "status": "success",
                        "message": f"Successfully imported {imported_tasks_count} tasks from Trello!",
                        "board_name": board_name,
                        "project_id": str(project.id),
                        "project_name": project.name,
                        "project_identifier": project.identifier,
                        "imported_tasks": imported_tasks_count,
                        "created_states": created_states_count,
                        "created_labels": created_labels_count,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"error": f"Import failed due to error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
