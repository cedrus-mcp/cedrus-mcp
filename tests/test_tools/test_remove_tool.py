"""Unit tests for remove tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import add_claim_sketch, add_argument_sketch, connect_sketch, remove
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


async def test_remove_claim_node(tool_context: Mock) -> None:
    """Test removing a claim node."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add a claim
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")
    assert arg_map.get_node("C1") is not None
    
    # Remove it
    result = remove(label="C1", ctx=tool_context)
    
    assert not result.isError
    with pytest.raises(KeyError):
        arg_map.get_node("C1")


async def test_remove_argument_node(tool_context: Mock) -> None:
    """Test removing an argument node."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add an argument
    await add_argument_sketch(
        label="A1",
        ctx=tool_context,
        gist="Test"
    )
    assert arg_map.get_node("A1") is not None
    
    # Remove it
    result = remove(label="A1", ctx=tool_context)
    
    assert not result.isError
    with pytest.raises(KeyError):
        arg_map.get_node("A1")


async def test_remove_relation(tool_context: Mock) -> None:
    """Test removing a relation between nodes."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add nodes and connect them
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Arg")
    await connect_sketch(
        source="A1",
        target="C1",
        relation_type="support",
        ctx=tool_context,
    )
    
    assert arg_map.get_dialectic_relation("A1", "C1") is not None
    
    # Remove the relation
    result = remove(
        source="A1", target="C1",
        ctx=tool_context
    )
    
    assert not result.isError
    assert arg_map.get_dialectic_relation("A1", "C1") is None
    # Nodes should still exist
    assert arg_map.get_node("A1") is not None
    assert arg_map.get_node("C1") is not None


def test_remove_nonexistent_node_fails(tool_context: Mock) -> None:
    """Test removing a non-existent node raises KeyError."""
    result = remove(label="NONEXISTENT", ctx=tool_context)
    assert result.structuredContent["status"] == "failure"


async def test_remove_with_both_label_and_relation_prioritizes_label(tool_context: Mock) -> None:
    """Test that providing both label and relation uses label."""
    # Add a node
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")
    
    # Call remove with both (should fail)
    result = remove(
        label="C1",
        source="A1", target="C2",
        ctx=tool_context
    )
    
    # Should fail
    assert result.structuredContent["status"] == "failure"