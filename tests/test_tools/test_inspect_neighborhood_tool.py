"""Unit tests for inspect_neighborhood tool."""

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
    inspect_neighborhood,
)


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")
    return ctx


async def test_inspect_neighborhood_isolated_node(tool_context: Mock) -> None:
    """Test inspecting neighborhood of an isolated node."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Isolated")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=1)

    assert not result.isError
    assert result.content


async def test_inspect_neighborhood_k1(tool_context: Mock) -> None:
    """Test inspecting 1-neighborhood (immediate neighbors)."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create connected nodes
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Central")
    await add_claim_sketch(label="C2", ctx=tool_context, proposition="Neighbor")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Supporter")

    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=1)

    assert not result.isError
    assert result.content


async def test_inspect_neighborhood_k2(tool_context: Mock) -> None:
    """Test inspecting 2-neighborhood."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create a chain: A1 -> C1 -> C2 -> C3
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Start")
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="One")
    await add_claim_sketch(label="C2", ctx=tool_context, proposition="Two")
    await add_claim_sketch(label="C3", ctx=tool_context, proposition="Three")

    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    arg_map.add_support_relation(from_label="C2", to_label="C3")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=2)

    assert not result.isError
    assert result.content
    # Should include nodes up to distance 2


async def test_inspect_neighborhood_k3(tool_context: Mock) -> None:
    """Test inspecting 3-neighborhood."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create a longer chain
    for i in range(5):
        if i % 2 == 0:
            await add_claim_sketch(label=f"C{i}", ctx=tool_context, proposition=f"Claim {i}")
        else:
            await add_argument_sketch(label=f"A{i}", ctx=tool_context, gist=f"Arg {i}")

    # Connect them in sequence
    for i in range(4):
        from_label = f"C{i}" if i % 2 == 0 else f"A{i}"
        to_label = f"A{i + 1}" if (i + 1) % 2 == 1 else f"C{i + 1}"
        arg_map.add_support_relation(from_label=from_label, to_label=to_label)

    result = await inspect_neighborhood(ctx=tool_context, label="C2", k=3)

    assert not result.isError


async def test_inspect_neighborhood_default_k(tool_context: Mock) -> None:
    """Test inspect_neighborhood with default k value (should be 2)."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_neighborhood(ctx=tool_context, label="C1")

    assert not result.isError


async def test_inspect_neighborhood_nonexistent_node(tool_context: Mock) -> None:
    """Test inspecting neighborhood of non-existent node."""
    result = await inspect_neighborhood(ctx=tool_context, label="NONEXISTENT", k=1)

    # Should return failure
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
    if result.content:
        from mcp.types import TextContent

        text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
        if text_content:
            assert "does not exist" in str(text_content.text).lower()


async def test_inspect_neighborhood_suggests_similar(tool_context: Mock) -> None:
    """Test that nonexistent node suggests similar labels."""
    await add_claim_sketch(label="TestClaim", ctx=tool_context, proposition="Test")

    result = await inspect_neighborhood(
        ctx=tool_context,
        label="TestClam",  # Typo
        k=1,
    )

    # Should fail and potentially suggest correct label
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"


async def test_inspect_neighborhood_invalid_k_zero(tool_context: Mock) -> None:
    """Test that k=0 is invalid."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=0)

    # Should return failure
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
    if result.content:
        from mcp.types import TextContent

        text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
        if text_content:
            assert "invalid" in str(text_content.text).lower()


async def test_inspect_neighborhood_invalid_k_negative(tool_context: Mock) -> None:
    """Test that negative k is invalid."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=-1)

    # Should return failure
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"


async def test_inspect_neighborhood_with_bidirectional_relations(tool_context: Mock) -> None:
    """Test neighborhood with both incoming and outgoing relations."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create nodes with bidirectional connections
    await add_claim_sketch(label="Center", ctx=tool_context, proposition="Center")
    await add_claim_sketch(label="Left", ctx=tool_context, proposition="Left")
    await add_claim_sketch(label="Right", ctx=tool_context, proposition="Right")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Support")

    # Add relations
    arg_map.add_support_relation(from_label="Left", to_label="Center")
    arg_map.add_support_relation(from_label="Center", to_label="Right")
    arg_map.add_support_relation(from_label="A1", to_label="Center")

    result = await inspect_neighborhood(ctx=tool_context, label="Center", k=1)

    assert not result.isError


async def test_inspect_neighborhood_with_attacks(tool_context: Mock) -> None:
    """Test neighborhood including attack relations."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Claim")
    await add_argument_sketch(label="A1", ctx=tool_context, gist="Support")
    await add_argument_sketch(label="A2", ctx=tool_context, gist="Attack")

    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_attack_relation(from_label="A2", to_label="C1")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=1)

    assert not result.isError


async def test_inspect_neighborhood_embeds_resource(tool_context: Mock) -> None:
    """Test that inspect_neighborhood embeds appropriate resource."""
    await add_claim_sketch(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_neighborhood(ctx=tool_context, label="C1", k=2)

    assert not result.isError
    assert result.content
    assert len(result.content) > 0
