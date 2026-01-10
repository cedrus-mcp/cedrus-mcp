"""Unit tests for result models."""

from cedrus.backend.models.results import NextAction


def test_create_next_action() -> None:
    """Test creating a NextAction."""
    action = NextAction(
        tool="add_claim", params={"label": "C1", "proposition": "Test"}, reason="Add a new claim"
    )

    assert action.tool == "add_claim"
    assert action.params["label"] == "C1"
    assert action.reason == "Add a new claim"


def test_next_action_with_action_type() -> None:
    """Test NextAction with action_type."""
    action = NextAction(
        tool="connect",
        params={"source": "A1", "target": "C1"},
        reason="Connect nodes",
        action_type="expand",
    )

    assert action.action_type == "expand"


def test_next_action_model_dump() -> None:
    """Test serializing NextAction to dict."""
    action = NextAction(
        tool="edit", params={"label": "C1", "field": "proposition"}, reason="Edit claim"
    )

    dumped = action.model_dump()

    assert isinstance(dumped, dict)
    assert dumped["tool"] == "edit"
    assert "params" in dumped
    assert "reason" in dumped


def test_next_action_json_serialization() -> None:
    """Test JSON serialization of NextAction."""
    action = NextAction(tool="remove", params={"label": "C1"}, reason="Remove node")

    json_str = action.model_dump_json()

    assert isinstance(json_str, str)
    assert "remove" in json_str
