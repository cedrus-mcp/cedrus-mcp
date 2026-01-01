"""Unit tests for connect tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import (
    add_claim_sketch,
    add_claim_author,
    add_argument_sketch,
    add_argument_author,
    connect_sketch,
    connect_author,
)
from koala.server import AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def tool_context_sketch(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for sketch mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


@pytest.fixture
def tool_context_author(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for author mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="author"
    )
    return ctx


async def test_connect_support_relation_sketch(tool_context_sketch: Mock) -> None:
    """Test creating a support relation in sketch mode."""
    arg_map = tool_context_sketch.request_context.lifespan_context.arg_map
    
    # Add two nodes
    await add_claim_sketch(label="C1", ctx=tool_context_sketch, proposition="Claim")
    await add_argument_sketch(label="A1", ctx=tool_context_sketch, gist="Arg")
    
    # Connect them
    result = await connect_sketch(
        source="A1",
        target="C1",
        relation_type="support",
        ctx=tool_context_sketch,
    )
    
    assert not result.isError
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "support"


async def test_connect_attack_relation_sketch(tool_context_sketch: Mock) -> None:
    """Test creating an attack relation in sketch mode."""
    arg_map = tool_context_sketch.request_context.lifespan_context.arg_map
    
    # Add two nodes
    await add_claim_sketch(label="C1", ctx=tool_context_sketch, proposition="Claim")
    await add_argument_sketch(label="A1", ctx=tool_context_sketch, gist="Arg")
    
    # Connect them
    result = await connect_sketch(
        source="A1",
        target="C1",
        relation_type ="attack",
        ctx=tool_context_sketch,
    )
    
    assert not result.isError
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "attack"


async def test_connect_author_with_grounding(tool_context_author: Mock) -> None:
    """Test creating a relation with grounding in author mode."""
    arg_map = tool_context_author.request_context.lifespan_context.arg_map
    
    # Add two nodes
    await add_claim_author(label="C1", ctx=tool_context_author, proposition="Claim")
    await add_argument_author(
        label="A1",
        ctx=tool_context_author,
        gist="Arg",
        premises=["P1", "P2"],
        conclusion="C"
    )
    
    # Connect with grounding strategy
    result = await connect_author(
        source="C1",
        target="A1",
        relation_type="support",
        grounding_strategy="copy_conclusion",
        ctx=tool_context_author,
    )
    
    # Should succeed and create grounded relation
    assert not result.isError
    rel = arg_map.get_dialectic_relation("C1", "A1")
    assert rel is not None
    assert not result.isError


async def test_connect_nonexistent_nodes_fails(tool_context_sketch: Mock) -> None:
    """Test connecting non-existent nodes returns error status."""
    result = await connect_sketch(
        source="NONEXISTENT1",
        target="NONEXISTENT2",
        relation_type="support",
        ctx=tool_context_sketch,
    )
    
    # Check that error is indicated in structured content
    assert result.structuredContent["status"] == "failure"
