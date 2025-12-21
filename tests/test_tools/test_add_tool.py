"""Unit tests for add tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import add
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


def test_add_claim_basic(tool_context: Mock) -> None:
    """Test adding a basic claim."""
    result = add(
        label="C1",
        ctx=tool_context,
        node_options={"proposition": "Test claim"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    assert node is not None
    # Get the proposition from the graph
    prop = arg_map.get_proposition(node.proposition_id)
    assert prop is not None
    assert prop.content == "Test claim"


def test_add_argument_basic(tool_context: Mock) -> None:
    """Test adding a basic argument."""
    result = add(
        label="A1",
        ctx=tool_context,
        node_options={
            "node_type": "argument",
            "gist": "Test argument"
        }
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    assert node is not None
    assert node.gist == "Test argument"


def test_add_with_relation(tool_context: Mock) -> None:
    """Test adding a node with simultaneous relation creation."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add first node
    add(label="C1", ctx=tool_context, node_options={"proposition": "Claim 1"})
    
    # Add second node with relation
    result = add(
        label="A1",
        ctx=tool_context,
        node_options={"node_type": "argument", "gist": "Argument"},
        relation_options={"to_label": "C1", "relation_type": "support"}
    )
    
    assert not result.isError
    assert arg_map.get_dialectic_relation("A1", "C1") is not None


def test_add_empty_label_fails(tool_context: Mock) -> None:
    """Test that empty label raises ValueError."""
    with pytest.raises(ValueError, match="Label must be a non-empty string"):
        add(
            label="",
            ctx=tool_context,
            node_options={"proposition": "Test"}
        )


def test_add_duplicate_label_gets_unique(tool_context: Mock) -> None:
    """Test that duplicate labels are made unique."""
    # Add first node
    add(label="C1", ctx=tool_context, node_options={"proposition": "First"})
    
    # Try to add with same label
    result = add(label="C1", ctx=tool_context, node_options={"proposition": "Second"})
    
    # Should succeed with modified label
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    # Original should still exist
    assert arg_map.get_node("C1") is not None
