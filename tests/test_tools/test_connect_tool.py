"""Unit tests for connect tool."""

import pytest
from unittest.mock import Mock
from cedrus.tools.entrypoints.sketch import (
    add_claim as add_claim_sketch,
    add_argument as add_argument_sketch,
    connect as connect_sketch,
)
from cedrus.tools.entrypoints.elaborate import (
    add_claim as add_claim_elaborate,
    add_argument as add_argument_elaborate,
    connect as connect_elaborate,
)
from cedrus.server import AppContext
from cedrus.graph.argument_map import ArgumentMap


@pytest.fixture
def tool_context_sketch(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for sketch mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")
    return ctx


@pytest.fixture
def tool_context_elaborate(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for elaborate mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="elaborate")
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
        relation_type="attack",
        ctx=tool_context_sketch,
    )

    assert not result.isError
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "attack"


async def test_connect_elaborate_with_grounding(tool_context_elaborate: Mock) -> None:
    """Test creating a relation with grounding in elaborate mode."""
    arg_map = tool_context_elaborate.request_context.lifespan_context.arg_map

    # Add two nodes
    await add_claim_elaborate(label="C1", ctx=tool_context_elaborate, proposition="Claim")
    await add_argument_elaborate(
        label="A1", ctx=tool_context_elaborate, gist="Arg", premises=["P1", "P2"], conclusion="C"
    )

    # Connect with grounding strategy
    result = await connect_elaborate(
        source="C1",
        target="A1",
        relation_type="support",
        grounding_strategy="copy_conclusion",
        ctx=tool_context_elaborate,
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
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
