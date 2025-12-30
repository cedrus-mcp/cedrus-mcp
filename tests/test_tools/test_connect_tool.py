"""Unit tests for connect tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import add_claim, add_argument, connect
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


async def test_connect_support_relation(tool_context: Mock) -> None:
    """Test creating a support relation."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add two nodes
    await add_claim(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument(label="A1", ctx=tool_context, gist="Arg")
    
    # Connect them
    result = connect(
        from_label="A1",
        to_label="C1",
        ctx=tool_context,
        relation_options={"relation_type": "support"}
    )
    
    assert not result.isError
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "support"


async def test_connect_attack_relation(tool_context: Mock) -> None:
    """Test creating an attack relation."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add two nodes
    await add_claim(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument(label="A1", ctx=tool_context, gist="Arg")
    
    # Connect them
    result = connect(
        from_label="A1",
        to_label="C1",
        ctx=tool_context,
        relation_options={"relation_type": "attack"}
    )
    
    assert not result.isError
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "attack"


async def test_connect_with_grounding_in_sketch_mode(tool_context: Mock) -> None:
    """Test that grounding is ignored in sketch mode."""
    # Add two nodes
    await add_claim(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument(label="A1", ctx=tool_context, gist="Arg")
    
    # Try to connect with grounding strategy
    result = connect(
        from_label="A1",
        to_label="C1",
        ctx=tool_context,
        relation_options={
            "relation_type": "support",
            "grounding_strategy": "copy_conclusion"
        }
    )
    
    # Should succeed but ignore grounding
    assert not result.isError


def test_connect_nonexistent_nodes_fails(tool_context: Mock) -> None:
    """Test connecting non-existent nodes returns error status."""
    result = connect(
        from_label="NONEXISTENT1",
        to_label="NONEXISTENT2",
        ctx=tool_context,
        relation_options={"relation_type": "support"}
    )
    
    # Check that error is indicated in structured content
    assert result.structuredContent["status"] == "failure"
