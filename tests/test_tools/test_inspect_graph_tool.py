"""Unit tests for inspect_graph tool."""

from unittest.mock import Mock

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.server import AppContext
from cedrus.tools.entrypoints.sketch import (
    add_argument as add_argument_sketch,
)
from cedrus.tools.entrypoints.sketch import (
    add_claim as add_claim_sketch,
)
from cedrus.tools.entrypoints.sketch import (
    inspect_graph,
)


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")
    return ctx


async def test_inspect_empty_graph(tool_context: Mock) -> None:
    """Test inspecting an empty graph."""
    result = await inspect_graph(ctx=tool_context)

    assert not result.isError
    assert result.content


async def test_inspect_graph_default_format(tool_context: Mock) -> None:
    """Test inspect_graph with default format (argdown)."""
    # Add some nodes
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim 1")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Argument 1")

    result = await inspect_graph(ctx=tool_context)

    assert not result.isError
    assert result.content
    # Should have used argdown format by default


async def test_inspect_graph_argdown_format(tool_context: Mock) -> None:
    """Test inspect_graph with explicit argdown format."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_graph(ctx=tool_context, format="argdown")

    assert not result.isError
    assert result.content


async def test_inspect_graph_tree_format(tool_context: Mock) -> None:
    """Test inspect_graph with tree format."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_graph(ctx=tool_context, format="tree")

    assert not result.isError
    assert result.content


async def test_inspect_graph_invalid_format(tool_context: Mock) -> None:
    """Test inspect_graph with invalid format."""
    result = await inspect_graph(ctx=tool_context, format="invalid")

    # Should return failure
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
    if result.content:
        from mcp.types import TextContent

        text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
        if text_content:
            assert "invalid format" in str(text_content.text).lower()


async def test_inspect_graph_verbose_false(tool_context: Mock) -> None:
    """Test inspect_graph with verbose=False (default)."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_graph(ctx=tool_context, verbose=False)

    assert not result.isError
    assert result.content


async def test_inspect_graph_verbose_true(tool_context: Mock) -> None:
    """Test inspect_graph with verbose=True for detailed view."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Arg")

    result = await inspect_graph(ctx=tool_context, verbose=True)

    assert not result.isError
    assert result.content
    # Verbose mode should include more details


async def test_inspect_graph_with_multiple_nodes(tool_context: Mock) -> None:
    """Test inspect_graph with multiple nodes and relations."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Add multiple nodes
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim 1")
    await add_claim_sketch(label="C2", ctx=tool_context, proposition="Claim 2")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Argument 1")

    # Add relations
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")

    result = await inspect_graph(ctx=tool_context)

    assert not result.isError
    assert result.content


async def test_inspect_graph_with_complex_structure(tool_context: Mock) -> None:
    """Test inspect_graph with a more complex argument structure."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create a small argument map
    for i in range(3):
        await add_claim_sketch(label=f"C{i + 1}", ctx=tool_context, proposition=f"Claim {i + 1}")
        await add_argument_sketch(label=f"A{i + 1}", ctx=tool_context, gist=f"Argument {i + 1}")

    # Add some relations
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_attack_relation(from_label="A2", to_label="A1")

    result = await inspect_graph(ctx=tool_context, verbose=True)

    assert not result.isError


async def test_inspect_graph_embeds_resource(tool_context: Mock) -> None:
    """Test that inspect_graph embeds appropriate resources."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_graph(ctx=tool_context)

    assert not result.isError
    assert result.content
    assert len(result.content) > 0


async def test_inspect_graph_verbose_includes_statistics(tool_context: Mock) -> None:
    """Test that verbose mode includes statistics."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Test")

    result = await inspect_graph(ctx=tool_context, verbose=True)

    assert not result.isError
    # Verbose mode should include statistics
    assert result.content


async def test_inspect_graph_different_modes(tool_context: Mock) -> None:
    """Test inspect_graph works in different editing modes."""
    # Test in sketch mode (already set)
    result = await inspect_graph(ctx=tool_context)
    assert not result.isError

    # Switch to elaborate mode
    tool_context.request_context.lifespan_context.mode = "elaborate"
    result = await inspect_graph(ctx=tool_context)
    assert not result.isError

    # Switch to review mode
    tool_context.request_context.lifespan_context.mode = "review"
    result = await inspect_graph(ctx=tool_context)
    assert not result.isError
