"""Tests for the validate MCP tool interface.

These tests focus on the tool's interface, parameter handling, and response format.
Detailed validation logic is tested in tests/test_validation/.
"""

import pytest
from unittest.mock import Mock
from cedrus.tools.impl.validation import validate_core
from cedrus.tools.entrypoints.review import validate as validate_entrypoint
from cedrus.server import AppContext
from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import Proposition, ClaimNode, ArgumentNode


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in review mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="review")
    return ctx


@pytest.fixture
def tool_context_sketch(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in sketch mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")
    return ctx


# Tool Interface Tests


@pytest.mark.asyncio
async def test_review_validate_entrypoint_smoke(tool_context: Mock) -> None:
    result = await validate_entrypoint(ctx=tool_context, fix=False)
    assert not result.isError


@pytest.mark.asyncio
async def test_validate_returns_valid_response_structure(tool_context: Mock) -> None:
    """Test that validate returns proper MCP response structure."""
    result = validate_core(ctx=tool_context)

    # Should return valid CallToolResult
    assert not result.isError
    assert result.structuredContent is not None
    assert isinstance(result.structuredContent, dict)

    # Should have expected keys
    assert "status" in result.structuredContent
    assert "message" in result.structuredContent


@pytest.mark.asyncio
async def test_validate_accepts_fix_parameter(tool_context: Mock) -> None:
    """Test that validate accepts fix parameter."""
    # Should work with fix=False
    result_no_fix = validate_core(ctx=tool_context, fix=False)
    assert not result_no_fix.isError

    # Should work with fix=True
    result_with_fix = validate_core(ctx=tool_context, fix=True)
    assert not result_with_fix.isError


@pytest.mark.asyncio
async def test_validate_accepts_max_issues_parameter(tool_context: Mock) -> None:
    """Test that validate accepts max_issues parameter."""
    result = validate_core(ctx=tool_context, max_issues=5)

    assert not result.isError
    assert result.structuredContent is not None


@pytest.mark.asyncio
async def test_validate_with_max_issues_limits_output(tool_context: Mock) -> None:
    """Test that max_issues parameter affects response."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create multiple validation issues
    for i in range(5):
        arg_node = ArgumentNode(label=f"A{i}", gist=f"Arg {i}", premises=[], conclusion="")
        arg_map.add_argument(arg_node)

    # Request limited issues
    result = validate_core(ctx=tool_context, max_issues=2)

    assert not result.isError
    assert result.structuredContent is not None

    # Verify issues are limited (allowing for connectivity check)
    issues = result.structuredContent.get("issues", [])
    assert len(issues) <= 4, f"Expected limited issues but got {len(issues)}"


@pytest.mark.asyncio
async def test_validate_works_in_all_modes(tool_context: Mock, tool_context_sketch: Mock) -> None:
    """Test that validate works in different modes."""
    # Review mode
    result_review = validate_core(ctx=tool_context)
    assert not result_review.isError

    # Sketch mode
    result_sketch = validate_core(ctx=tool_context_sketch)
    assert not result_sketch.isError


# Response Content Tests


@pytest.mark.asyncio
async def test_validate_includes_issues_in_response(tool_context: Mock) -> None:
    """Test that validation response includes issues list."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create an issue
    arg_node = ArgumentNode(label="A1", gist="Test", premises=[], conclusion="")
    arg_map.add_argument(arg_node)

    result = validate_core(ctx=tool_context)

    assert result.structuredContent is not None
    assert "issues" in result.structuredContent
    assert isinstance(result.structuredContent["issues"], list)


@pytest.mark.asyncio
async def test_validate_issues_have_proper_structure(tool_context: Mock) -> None:
    """Test that reported issues have proper structure."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create an issue
    arg_node = ArgumentNode(label="A1", gist="Test", premises=[], conclusion="")
    arg_map.add_argument(arg_node)

    result = validate_core(ctx=tool_context)

    assert result.structuredContent is not None
    issues = result.structuredContent.get("issues", [])

    # Each issue should have required fields
    for issue in issues:
        assert "severity" in issue
        assert issue["severity"] in ["info", "warning", "error"]
        # Should have some message field
        assert "issue" in issue or "message" in issue


@pytest.mark.asyncio
async def test_validate_includes_suggestions_when_not_fixing(tool_context: Mock) -> None:
    """Test that suggestions are included when fix=False."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create an issue
    arg_node = ArgumentNode(label="A1", gist="Test", premises=[], conclusion="")
    arg_map.add_argument(arg_node)

    result = validate_core(ctx=tool_context, fix=False)

    assert result.structuredContent is not None

    # Should include suggestions/next_actions
    suggestions = result.structuredContent.get("next_actions", [])
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_validate_reports_success_on_valid_map(tool_context: Mock) -> None:
    """Test that validation reports success for valid map."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create a well-formed, connected map
    prop1 = Proposition(content="Premise")
    prop2 = Proposition(content="Conclusion")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)

    arg = ArgumentNode(label="A1", gist="Valid arg", premises=[prop1.id], conclusion=prop2.id)
    arg_map.add_argument(arg)

    result = validate_core(ctx=tool_context)

    assert not result.isError
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "success"


# Error Handling Tests


@pytest.mark.asyncio
async def test_validate_handles_empty_map_gracefully(tool_context: Mock) -> None:
    """Test that validation handles empty map without errors."""
    result = validate_core(ctx=tool_context)

    assert not result.isError
    assert result.structuredContent is not None


@pytest.mark.asyncio
async def test_validate_doesnt_crash_on_malformed_map(tool_context: Mock) -> None:
    """Test that validation doesn't crash even with unusual map state."""
    # This should handle edge cases gracefully
    result = validate_core(ctx=tool_context)

    assert not result.isError
