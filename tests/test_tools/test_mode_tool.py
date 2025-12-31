"""Unit tests for mode tool."""

import pytest
from unittest.mock import Mock
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
    return ctx


def test_mode_switch_to_author(tool_context: Mock) -> None:
    """Test switching to author mode."""
    assert tool_context.request_context.lifespan_context.mode == "sketch"
    
    result = set_mode(mode="author", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "author"


def test_mode_switch_to_review(tool_context: Mock) -> None:
    """Test switching to review mode."""
    result = set_mode(mode="review", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "review"


def test_mode_switch_to_sketch(tool_context: Mock) -> None:
    """Test switching to sketch mode."""
    tool_context.request_context.lifespan_context.mode = "author"
    
    result = set_mode(mode="sketch", ctx=tool_context)
    
    assert not result.isError
    assert tool_context.request_context.lifespan_context.mode == "sketch"


def test_mode_invalid_mode_fails(tool_context: Mock) -> None:
    """Test that invalid mode returns error status."""
    result = set_mode(mode="invalid", ctx=tool_context)
    
    # Check that error is indicated in structured content
    assert result.structuredContent["status"] == "failure"
    # Mode should remain unchanged
    assert tool_context.request_context.lifespan_context.mode == "sketch"
