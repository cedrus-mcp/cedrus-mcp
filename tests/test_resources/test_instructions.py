"""Unit tests for instructions resource."""

from unittest.mock import Mock, patch

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.resources.instructions import instruction_resource
from cedrus.server import AppContext, mcp


@pytest.fixture
def mock_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock MCP context."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")
    return ctx


@pytest.mark.asyncio
async def test_instructions_in_sketch_mode(mock_context: Mock) -> None:
    """Test instruction resource for sketch mode."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        mcp.get_context().request_context.lifespan_context.mode = "sketch"
        result = await instruction_resource()

        assert isinstance(result, str)
        assert len(result) > 0
        assert "sketch" in result.lower()


@pytest.mark.asyncio
async def test_instruction_elaborate_mode(mock_context: Mock) -> None:
    """Test instruction resource for elaborate mode."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        mcp.get_context().request_context.lifespan_context.mode = "elaborate"
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "elaborate" in result.lower()


@pytest.mark.asyncio
async def test_instruction_review_mode(mock_context: Mock) -> None:
    """Test instruction resource for review mode."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        mcp.get_context().request_context.lifespan_context.mode = "review"
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "review" in result.lower()


@pytest.mark.asyncio
async def test_instruction_all_modes_different() -> None:
    """Test that instructions differ by mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=ArgumentMap(), mode="sketch")

    with patch.object(mcp, "get_context", return_value=ctx):
        mcp.get_context().request_context.lifespan_context.mode = "sketch"
        sketch = await instruction_resource()
        mcp.get_context().request_context.lifespan_context.mode = "elaborate"
        elaborate = await instruction_resource()
        mcp.get_context().request_context.lifespan_context.mode = "review"
        review = await instruction_resource()

    # Each should be different
    assert sketch != elaborate
    assert elaborate != review
    assert sketch != review
