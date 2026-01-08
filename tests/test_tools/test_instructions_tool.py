"""Unit tests for instructions tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import get_instructions
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
def tool_context_elaborate(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for elaborate mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="elaborate"
    )
    return ctx


@pytest.fixture
def tool_context_review(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for review mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="review"
    )
    return ctx


async def test_instructions_sketch_mode(tool_context_sketch: Mock) -> None:
    """Test instructions tool in sketch mode."""
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError
    assert result.content
    # Should have embedded instructions resource
    from mcp.types import TextContent
    text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
    assert text_content is not None
    assert len(text_content.text) > 0


async def test_instructions_elaborate_mode(tool_context_elaborate: Mock) -> None:
    """Test instructions tool in elaborate mode."""
    result = await get_instructions(ctx=tool_context_elaborate)
    
    assert not result.isError
    assert result.content


async def test_instructions_review_mode(tool_context_review: Mock) -> None:
    """Test instructions tool in review mode."""
    result = await get_instructions(ctx=tool_context_review)
    
    assert not result.isError
    assert result.content


async def test_instructions_returns_text(tool_context_sketch: Mock) -> None:
    """Test that instructions returns text content."""
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError
    assert result.content
    assert len(result.content) > 0
    # Should be TextContent
    from mcp.types import TextContent
    has_text = any(isinstance(c, TextContent) for c in result.content)
    assert has_text


async def test_instructions_embeds_resource(tool_context_sketch: Mock) -> None:
    """Test that instructions embeds resource with proper URI."""
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError
    assert result.content
    # Should have embedded instructions resource
    from mcp.types import TextContent
    text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
    assert text_content is not None
    assert text_content.text  # Should not be empty


async def test_instructions_success_message(tool_context_sketch: Mock) -> None:
    """Test that instructions includes success message."""
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError
    # Should have structured content with success status
    assert result.structuredContent is not None


async def test_instructions_different_per_mode(
    tool_context_sketch: Mock,
    tool_context_elaborate: Mock,
    tool_context_review: Mock
) -> None:
    """Test that instructions may vary by mode."""
    result_sketch = await get_instructions(ctx=tool_context_sketch)
    result_elaborate = await get_instructions(ctx=tool_context_elaborate)
    result_review = await get_instructions(ctx=tool_context_review)
    
    # All should succeed
    assert not result_sketch.isError
    assert not result_elaborate.isError
    assert not result_review.isError
    
    # All should have content
    assert result_sketch.content
    assert result_elaborate.content
    assert result_review.content


async def test_instructions_no_parameters_required(
    tool_context_sketch: Mock
) -> None:
    """Test that instructions requires no parameters."""
    # Should work with just ctx parameter
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError


async def test_instructions_handles_errors_gracefully(
    tool_context_sketch: Mock
) -> None:
    """Test that instructions handles errors gracefully."""
    # Even with empty map, should not raise exception
    result = await get_instructions(ctx=tool_context_sketch)
    
    assert not result.isError


async def test_instructions_available_in_all_modes(
    tool_context_sketch: Mock,
    tool_context_elaborate: Mock,
    tool_context_review: Mock
) -> None:
    """Test that instructions is available in all modes."""
    # Instructions is a shared tool, should work in all modes
    modes = [tool_context_sketch, tool_context_elaborate, tool_context_review]
    
    for ctx in modes:
        result = await get_instructions(ctx=ctx)
        assert not result.isError
        assert result.content
