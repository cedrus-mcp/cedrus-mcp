"""Unit tests for edit tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import add, edit
from koala.server import AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


def test_edit_claim_proposition(tool_context: Mock) -> None:
    """Test editing a claim's proposition."""
    # Add a claim
    add(label="C1", ctx=tool_context, node_options={"proposition": "Original"})
    
    # Edit it
    result = edit(
        label="C1",
        field="proposition",
        ctx=tool_context,
        edit_options={"new_value": "Updated"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    prop = arg_map.get_proposition(node.proposition_id)
    assert prop.content == "Updated"


def test_edit_argument_gist(tool_context: Mock) -> None:
    """Test editing an argument's gist."""
    # Add an argument
    add(
        label="A1",
        ctx=tool_context,
        node_options={"node_type": "argument", "gist": "Original gist"}
    )
    
    # Edit it
    result = edit(
        label="A1",
        field="gist",
        ctx=tool_context,
        edit_options={"new_value": "Updated gist"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    assert node.gist == "Updated gist"


def test_edit_argument_conclusion(tool_context: Mock) -> None:
    """Test editing an argument's conclusion."""
    # Add an argument
    add(
        label="A1",
        ctx=tool_context,
        node_options={"node_type": "argument", "gist": "Argument"}
    )
    
    # Edit conclusion
    result = edit(
        label="A1",
        field="conclusion",
        ctx=tool_context,
        edit_options={"new_value": "New conclusion"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    # conclusion is a proposition ID string
    prop = arg_map.get_proposition(node.conclusion)
    assert prop is not None
    assert prop.content == "New conclusion"


def test_edit_nonexistent_node_fails(tool_context: Mock) -> None:
    """Test editing a non-existent node raises KeyError."""
    with pytest.raises(KeyError):
        edit(
            label="NONEXISTENT",
            field="proposition",
            ctx=tool_context,
            edit_options={"new_value": "Test"}
        )


def test_edit_tags(tool_context: Mock) -> None:
    """Test editing tags on a node."""
    # Add a claim
    add(label="C1", ctx=tool_context, node_options={"proposition": "Test"})
    
    # Add a tag
    result = edit(
        label="C1",
        field="tags",
        ctx=tool_context,
        edit_options={"new_value": "important"}
    )
    
    assert not result.isError


def test_edit_metadata(tool_context: Mock) -> None:
    """Test editing metadata on a node."""
    # Add a claim
    add(label="C1", ctx=tool_context, node_options={"proposition": "Test"})
    
    # Add metadata
    result = edit(
        label="C1",
        field="metadata",
        ctx=tool_context,
        edit_options={"key": "source", "new_value": "paper.pdf"}
    )
    
    assert not result.isError
