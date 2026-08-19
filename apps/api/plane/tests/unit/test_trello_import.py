import pytest
from unittest.mock import MagicMock, patch

from plane.api.views.integration.trello import (
    map_trello_color,
    determine_state_group_and_color,
    clean_html_desc,
    generate_project_identifier,
    TrelloImportEndpoint,
)
from plane.db.models.state import StateGroup


@pytest.mark.unit
def test_map_trello_color():
    assert map_trello_color("green") == "#46A758"
    assert map_trello_color("yellow") == "#F59E0B"
    assert map_trello_color("red") == "#E54D2E"
    assert map_trello_color("blue") == "#0090FF"
    assert map_trello_color("unknown_color") == "#60646C"
    assert map_trello_color("") == "#60646C"


@pytest.mark.unit
def test_determine_state_group_and_color():
    group, color = determine_state_group_and_color("Done")
    assert group == StateGroup.COMPLETED.value
    assert color == "#46A758"

    group, color = determine_state_group_and_color("Hoàn thành công việc")
    assert group == StateGroup.COMPLETED.value

    group, color = determine_state_group_and_color("In Progress")
    assert group == StateGroup.STARTED.value
    assert color == "#F59E0B"

    group, color = determine_state_group_and_color("Đang làm")
    assert group == StateGroup.STARTED.value

    group, color = determine_state_group_and_color("Backlog Ideas")
    assert group == StateGroup.BACKLOG.value

    group, color = determine_state_group_and_color("Cancelled Tasks")
    assert group == StateGroup.CANCELLED.value

    group, color = determine_state_group_and_color("To Do")
    assert group == StateGroup.UNSTARTED.value
    assert color == "#60646C"


@pytest.mark.unit
def test_clean_html_desc():
    desc = "Line 1\n\nLine 2"
    checklists = "<ul><li>☑ Task 1</li></ul>"
    result = clean_html_desc(desc, checklists)
    assert "<p>Line 1</p>" in result
    assert "<p>Line 2</p>" in result
    assert "<hr/>" in result
    assert "<ul><li>☑ Task 1</li></ul>" in result

    empty_result = clean_html_desc("", "")
    assert empty_result == "<p></p>"


@pytest.mark.unit
def test_generate_project_identifier():
    mock_workspace = MagicMock()
    with patch("plane.db.models.Project.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = False
        identifier = generate_project_identifier("Civix Core Engine", mock_workspace)
        assert len(identifier) >= 2
        assert identifier.isalnum()


@pytest.mark.unit
@pytest.mark.django_db
def test_trello_import_endpoint_success():
    endpoint = TrelloImportEndpoint()

    mock_request = MagicMock()
    mock_request.FILES = {}
    mock_request.data = {
        "name": "Civix Platform Board",
        "lists": [
            {"id": "list_1", "name": "To Do", "closed": False},
            {"id": "list_2", "name": "Done", "closed": False},
        ],
        "labels": [
            {"id": "lbl_1", "name": "Bug", "color": "red"},
            {"id": "lbl_2", "name": "Feature", "color": "green"},
        ],
        "checklists": [
            {
                "id": "chk_1",
                "name": "Checklist items",
                "checkItems": [
                    {"name": "Step 1", "state": "complete"},
                    {"name": "Step 2", "state": "incomplete"},
                ],
            }
        ],
        "cards": [
            {
                "id": "card_1",
                "name": "Implement Trello Importer",
                "desc": "Detail description",
                "idList": "list_1",
                "idLabels": ["lbl_1"],
                "idChecklists": ["chk_1"],
                "due": "2026-08-30T10:00:00.000Z",
                "closed": False,
            }
        ],
        "target_project_id": "11111111-1111-1111-1111-111111111111",
    }
    mock_request.user.is_authenticated = True

    mock_workspace = MagicMock()
    mock_workspace.slug = "civix"
    mock_workspace.owner = mock_request.user

    mock_project = MagicMock()
    mock_project.id = "11111111-1111-1111-1111-111111111111"
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.workspace = mock_workspace

    mock_state = MagicMock()
    mock_state.id = "state-1"

    mock_label = MagicMock()
    mock_label.id = "label-1"

    mock_issue = MagicMock()

    with patch("plane.db.models.Workspace.objects.get", return_value=mock_workspace), \
         patch("plane.db.models.WorkspaceMember.objects.filter") as mock_member_filter, \
         patch("plane.db.models.Project.objects.get", return_value=mock_project), \
         patch("plane.db.models.State.objects.filter") as mock_state_filter, \
         patch("plane.db.models.State.objects.create", return_value=mock_state), \
         patch("plane.db.models.Label.objects.filter") as mock_label_filter, \
         patch("plane.db.models.Label.objects.create", return_value=mock_label), \
         patch("plane.db.models.Issue.objects.create", return_value=mock_issue), \
         patch("plane.db.models.IssueLabel.objects.create"):

        mock_member_filter.return_value.exists.return_value = True
        mock_state_filter.return_value.first.return_value = None
        mock_label_filter.return_value.first.return_value = None

        response = endpoint.post(mock_request, slug="civix", project_id="global")

        assert response.status_code == 200, getattr(response, "data", None)
        assert response.data["status"] == "success"
        assert response.data["imported_tasks"] == 1
        assert response.data["created_states"] == 2
        assert response.data["created_labels"] == 2
        assert response.data["board_name"] == "Civix Platform Board"
