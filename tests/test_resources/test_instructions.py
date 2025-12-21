"""Unit tests for instructions resource."""

import pytest
from unittest.mock import Mock, patch
from koala.resources.instructions import instruction_resource
from koala.server import mcp, AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def mock_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock MCP context."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


@pytest.mark.asyncio
async def test_instructions_in_sketch_mode(mock_context: Mock) -> None:
    """Test instruction resource for sketch mode."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await instruction_resource(mode="sketch")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "sketch" in result.lower()


@pytest.mark.asyncio
async def test_instruction_author_mode(mock_context: Mock) -> None:
    """Test instruction resource for author mode."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await instruction_resource(mode="author")
        
        assert isinstance(result, str)
        assert "author" in result.lower()


@pytest.mark.asyncio
async def test_instruction_review_mode(mock_context: Mock) -> None:
    """Test instruction resource for review mode."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await instruction_resource(mode="review")
        
        assert isinstance(result, str)
        assert "review" in result.lower()


@pytest.mark.asyncio
async def test_instruction_all_modes_different() -> None:
    """Test that instructions differ by mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=ArgumentMap(),
        mode="sketch"
    )
    
    with patch.object(mcp, 'get_context', return_value=ctx):
        sketch = await instruction_resource(mode="sketch")
        author = await instruction_resource(mode="author")
        review = await instruction_resource(mode="review")
    
    # Each should be different
    assert sketch != author
    assert author != review
    assert sketch != review
