"""Unit tests for mode tool."""

import pytest
from unittest.mock import Mock, AsyncMock
from koala.tools.tools import set_mode
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
    # Mock FastMCP server for tool add/remove operations
    ctx.fastmcp = Mock()
    ctx.fastmcp.add_tool = Mock()
    ctx.fastmcp.remove_tool = Mock()
    # Mock session for tool_list_changed notification
    ctx.session = Mock()
    ctx.session.send_tool_list_changed = AsyncMock()
    return ctx


async def test_mode_switch_to_elaborate(tool_context: Mock) -> None:
    """Test switching to elaborate mode."""
    assert tool_context.request_context.lifespan_context.mode == "sketch"
    
    result = await set_mode(mode="elaborate", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "elaborate"
    # Verify tool_list_changed notification was sent
    tool_context.session.send_tool_list_changed.assert_called_once()


async def test_mode_switch_to_review(tool_context: Mock) -> None:
    """Test switching to review mode."""
    result = await set_mode(mode="review", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "review"
    tool_context.session.send_tool_list_changed.assert_called_once()


async def test_mode_switch_to_sketch(tool_context: Mock) -> None:
    """Test switching to sketch mode."""
    tool_context.request_context.lifespan_context.mode = "elaborate"
    
    result = await set_mode(mode="sketch", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "sketch"
    tool_context.session.send_tool_list_changed.assert_called_once()


async def test_mode_invalid_mode_fails(tool_context: Mock) -> None:
    """Test that invalid mode returns error status."""
    result = await set_mode(mode="invalid", ctx=tool_context)
    
    # Check that error is indicated in structured content
    assert result.structuredContent["status"] == "failure"
    # Mode should remain unchanged
    assert tool_context.request_context.lifespan_context.mode == "sketch"
    # No notification should be sent for failed mode switch
    tool_context.session.send_tool_list_changed.assert_not_called()


async def test_mode_switch_same_mode_no_tools_updated(tool_context: Mock) -> None:
    """Test that switching to the same mode doesn't trigger tool updates."""
    result = await set_mode(mode="sketch", ctx=tool_context)
    
    assert not result.isError
    # No tool changes should be made when mode doesn't actually change
    tool_context.fastmcp.add_tool.assert_not_called()
    tool_context.fastmcp.remove_tool.assert_not_called()
    tool_context.session.send_tool_list_changed.assert_not_called()
