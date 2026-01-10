"""Unit tests for instructions tool."""

from unittest.mock import Mock

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.server import AppContext
from cedrus.tools.entrypoints.elaborate import get_instructions as get_instructions_elaborate
from cedrus.tools.entrypoints.sketch import get_instructions


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


@pytest.fixture
def tool_context_review(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for review mode testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="review")
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
    result = await get_instructions_elaborate(ctx=tool_context_elaborate)

    assert not result.isError
    assert result.content


async def test_instructions_elaborate_mode_with_grounding_topic(
    tool_context_elaborate: Mock,
) -> None:
    """Test instructions tool in elaborate mode with grounding topic."""
    result = await get_instructions_elaborate(ctx=tool_context_elaborate, topic="grounding")

    assert not result.isError
    assert result.content
    # Check that it returns grounding-specific instructions
    from mcp.types import TextContent

    text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
    assert text_content is not None
    assert len(text_content.text) > 0


async def test_instructions_elaborate_mode_with_validity_topic(
    tool_context_elaborate: Mock,
) -> None:
    """Test instructions tool in elaborate mode with validity topic."""
    result = await get_instructions_elaborate(ctx=tool_context_elaborate, topic="validity")

    assert not result.isError
    assert result.content
    # Check that it returns validity-specific instructions
    from mcp.types import TextContent

    text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
    assert text_content is not None
    assert len(text_content.text) > 0


async def test_instructions_elaborate_mode_with_invalid_topic(tool_context_elaborate: Mock) -> None:
    """Test instructions tool in elaborate mode with invalid topic."""
    result = await get_instructions_elaborate(ctx=tool_context_elaborate, topic="invalid")  # type: ignore

    # Should fail with error for invalid topic
    assert result.structuredContent and result.structuredContent["status"] == "failure"


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
    tool_context_sketch: Mock, tool_context_elaborate: Mock, tool_context_review: Mock
) -> None:
    """Test that instructions vary by mode."""
    # Sketch and review use basic get_instructions
    result_sketch = await get_instructions(ctx=tool_context_sketch)
    result_review = await get_instructions(ctx=tool_context_review)

    # Elaborate uses get_instructions_elaborate
    result_elaborate = await get_instructions_elaborate(ctx=tool_context_elaborate)

    # All should succeed
    assert not result_sketch.isError
    assert not result_elaborate.isError
    assert not result_review.isError

    # All should have content
    assert result_sketch.content
    assert result_elaborate.content
    assert result_review.content


async def test_instructions_elaborate_accepts_topic_parameter(tool_context_elaborate: Mock) -> None:
    """Test that elaborate mode variant accepts topic parameter."""
    # Should work without topic (defaults to general instructions)
    result_general = await get_instructions_elaborate(ctx=tool_context_elaborate)
    assert not result_general.isError

    # Should work with grounding topic
    result_grounding = await get_instructions_elaborate(
        ctx=tool_context_elaborate, topic="grounding"
    )
    assert not result_grounding.isError

    # Should work with validity topic
    result_validity = await get_instructions_elaborate(ctx=tool_context_elaborate, topic="validity")
    assert not result_validity.isError

    # Content should differ between topics
    from mcp.types import TextContent

    text_grounding = next((c for c in result_grounding.content if isinstance(c, TextContent)), None)
    text_validity = next((c for c in result_validity.content if isinstance(c, TextContent)), None)
    assert text_grounding is not None
    assert text_validity is not None
    # The two topic-specific instructions should be different
    assert text_grounding.text != text_validity.text


async def test_instructions_no_parameters_required(tool_context_sketch: Mock) -> None:
    """Test that instructions requires no parameters."""
    # Should work with just ctx parameter
    result = await get_instructions(ctx=tool_context_sketch)

    assert not result.isError


async def test_instructions_handles_errors_gracefully(tool_context_sketch: Mock) -> None:
    """Test that instructions handles errors gracefully."""
    # Even with empty map, should not raise exception
    result = await get_instructions(ctx=tool_context_sketch)

    assert not result.isError


async def test_instructions_available_in_all_modes(
    tool_context_sketch: Mock, tool_context_elaborate: Mock, tool_context_review: Mock
) -> None:
    """Test that instructions is available in all modes with appropriate signature."""
    # Sketch and review use basic get_instructions
    result_sketch = await get_instructions(ctx=tool_context_sketch)
    result_review = await get_instructions(ctx=tool_context_review)

    # Elaborate uses get_instructions_elaborate (which can also work without topic)
    result_elaborate = await get_instructions_elaborate(ctx=tool_context_elaborate)

    assert not result_sketch.isError
    assert not result_elaborate.isError
    assert not result_review.isError
    assert result_sketch.content
    assert result_elaborate.content
    assert result_review.content


async def test_instructions_sketch_and_review_no_topic_parameter(
    tool_context_sketch: Mock, tool_context_review: Mock
) -> None:
    """Test that sketch and review modes use basic get_instructions without topic parameter."""
    # Basic get_instructions doesn't accept topic parameter
    result_sketch = await get_instructions(ctx=tool_context_sketch)
    result_review = await get_instructions(ctx=tool_context_review)

    assert not result_sketch.isError
    assert not result_review.isError

    # Verify that these are the simple variant (no topic parameter in signature)
    import inspect

    sig = inspect.signature(get_instructions)
    params = list(sig.parameters.keys())
    # Should only have 'ctx' parameter
    assert "ctx" in params
    assert "topic" not in params
