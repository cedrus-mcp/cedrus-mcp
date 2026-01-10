"""Unit tests for reset_graph tool."""

import pytest
from unittest.mock import Mock, AsyncMock
from cedrus.tools.entrypoints.sketch import (
    reset_graph,
    add_claim as add_claim_sketch,
    add_argument as add_argument_sketch,
    connect as connect_sketch,
)
from cedrus.server import AppContext
from cedrus.graph.argument_map import ArgumentMap


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")

    # Mock FastMCP server
    ctx.fastmcp = Mock()
    ctx.fastmcp.add_tool = Mock()
    ctx.fastmcp.remove_tool = Mock()

    # Mock session for notifications
    ctx.session = Mock()
    ctx.session.send_tool_list_changed = AsyncMock()

    return ctx


@pytest.mark.asyncio
async def test_reset_empty_graph_fails(tool_context: Mock) -> None:
    """Test that resetting an empty graph returns error."""
    result = await reset_graph(ctx=tool_context, confirm=False)

    # Check it's a failure status (not isError flag)
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
    assert result.structuredContent["error"] == "EmptyGraph"
    assert "already empty" in result.structuredContent["message"].lower()


@pytest.mark.asyncio
async def test_reset_requires_confirmation(tool_context: Mock) -> None:
    """Test that reset requires confirmation parameter."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Add some nodes
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")
    assert len(arg_map.argument_graph.nodes) == 1

    # First call without confirmation should warn
    result = await reset_graph(ctx=tool_context, confirm=False)

    # Should not be an error, just a warning
    assert not result.isError
    # Graph should still have the node
    assert len(arg_map.argument_graph.nodes) == 1
    # Should mention confirmation in response
    assert "confirm=True" in str(result.content)


@pytest.mark.asyncio
async def test_reset_clears_graph(tool_context: Mock) -> None:
    """Test that reset clears all nodes and relations."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Add nodes and relations
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim 1")
    await add_claim_sketch(label="C2", ctx=tool_context, proposition="Claim 2")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Argument")
    await connect_sketch(
        source="A1",
        target="C1",
        relation_type="support",
        ctx=tool_context,
    )

    assert len(arg_map.argument_graph.nodes) == 3
    assert arg_map.argument_graph.number_of_edges() == 1

    # Reset with confirmation
    result = await reset_graph(ctx=tool_context, confirm=True)

    assert not result.isError
    assert len(arg_map.argument_graph.nodes) == 0
    assert arg_map.argument_graph.number_of_edges() == 0
    assert arg_map.proposition_graph.number_of_nodes() == 0


@pytest.mark.asyncio
async def test_reset_returns_statistics(tool_context: Mock) -> None:
    """Test that reset returns statistics of what was cleared."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Add nodes
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Arg")

    # Reset
    result = await reset_graph(ctx=tool_context, confirm=True)

    assert not result.isError
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "success"
    # Check that statistics are in the message
    message = result.structuredContent["message"]
    assert "1 claim" in message.lower()
    assert "1 argument" in message.lower()


@pytest.mark.asyncio
async def test_reset_resets_mode_to_sketch(tool_context: Mock) -> None:
    """Test that reset resets mode to sketch."""
    # Start in elaborate mode
    tool_context.request_context.lifespan_context.mode = "elaborate"

    # Add a node
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    # Reset
    result = await reset_graph(ctx=tool_context, confirm=True)

    assert not result.isError
    # Mode should be reset to sketch
    assert tool_context.request_context.lifespan_context.mode == "sketch"


@pytest.mark.asyncio
async def test_reset_suggests_get_instructions(tool_context: Mock) -> None:
    """Test that reset suggests calling get_instructions."""
    # Add a node
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    # Reset
    result = await reset_graph(ctx=tool_context, confirm=True)

    assert not result.isError
    # Should suggest get_instructions
    assert result.structuredContent is not None
    next_actions = result.structuredContent.get("next_actions", [])
    assert any(action.get("tool") == "get_instructions" for action in next_actions)
