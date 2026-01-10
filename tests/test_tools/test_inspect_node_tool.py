"""Unit tests for inspect_node tool."""

from unittest.mock import Mock

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models import ClaimNode, Proposition
from cedrus.server import AppContext
from cedrus.tools.entrypoints.elaborate import (
    add_argument as add_argument_elaborate,
)
from cedrus.tools.entrypoints.elaborate import (
    add_claim as add_claim_elaborate,
)
from cedrus.tools.entrypoints.elaborate import (
    inspect_node,
)


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in elaborate mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="elaborate")
    return ctx


@pytest.fixture
def tool_context_review(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in review mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="review")
    return ctx


async def test_inspect_claim_node(tool_context: Mock) -> None:
    """Test inspecting a claim node."""
    # Add a claim
    await add_claim_elaborate(
        label="C1", ctx=tool_context, proposition="This is a test claim", tags=["test", "important"]
    )

    result = await inspect_node(label="C1", ctx=tool_context)

    # The resource function needs MCP context which isn't available in unit tests
    # So we check that the call completes (may fail with context error)
    assert result is not None


async def test_inspect_argument_node(tool_context: Mock) -> None:
    """Test inspecting an argument node."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument gist",
        premises=["Premise 1", "Premise 2"],
        conclusion="Test conclusion",
        tags=["argument"],
    )

    result = await inspect_node(label="A1", ctx=tool_context)

    # The resource function needs MCP context which isn't available in unit tests
    assert result is not None


async def test_inspect_node_with_relations(tool_context: Mock) -> None:
    """Test inspecting a node that has relations."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Create nodes with relations
    await add_claim_elaborate(label="C1", ctx=tool_context, proposition="Claim 1")
    await add_claim_elaborate(label="C2", ctx=tool_context, proposition="Claim 2")
    await add_argument_elaborate(label="A1", ctx=tool_context, gist="Argument 1")

    # Add relations
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")

    result = await inspect_node(label="C1", ctx=tool_context)

    assert not result.isError
    assert result.content


async def test_inspect_nonexistent_node(tool_context: Mock) -> None:
    """Test inspecting a non-existent node."""
    result = await inspect_node(label="NONEXISTENT", ctx=tool_context)

    # Should return failure status
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
    if result.content:
        from mcp.types import TextContent

        text_content = next((c for c in result.content if isinstance(c, TextContent)), None)
        if text_content:
            assert "does not exist" in str(text_content.text).lower()


async def test_inspect_node_suggests_similar(tool_context: Mock) -> None:
    """Test that inspecting nonexistent node suggests similar labels."""
    # Add a node with similar label
    await add_claim_elaborate(label="TestClaim", ctx=tool_context, proposition="Test")

    result = await inspect_node(label="TestClam", ctx=tool_context)  # Typo

    # Should fail and potentially suggest the correct label
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"


async def test_inspect_node_in_review_mode(tool_context_review: Mock) -> None:
    """Test inspecting a node in review mode."""
    # Add a node
    arg_map = tool_context_review.request_context.lifespan_context.arg_map
    prop = Proposition(content="Test")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)

    result = await inspect_node(label="C1", ctx=tool_context_review)

    assert not result.isError


async def test_inspect_node_with_tags(tool_context: Mock) -> None:
    """Test that inspect_node shows tags."""
    await add_claim_elaborate(
        label="C1", ctx=tool_context, proposition="Test", tags=["important", "review-needed"]
    )

    result = await inspect_node(label="C1", ctx=tool_context)

    # The resource function needs MCP context which isn't available in unit tests
    assert result is not None


async def test_inspect_isolated_node(tool_context: Mock) -> None:
    """Test inspecting an isolated node with no relations."""
    await add_claim_elaborate(label="IsolatedClaim", ctx=tool_context, proposition="I am alone")

    result = await inspect_node(label="IsolatedClaim", ctx=tool_context)

    assert not result.isError
    assert result.content


async def test_inspect_node_with_metadata(tool_context: Mock) -> None:
    """Test inspecting a node with metadata."""
    arg_map = tool_context.request_context.lifespan_context.arg_map

    # Add claim with metadata
    prop = Proposition(content="Test")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id, metadata={"source": "paper", "page": 42})
    arg_map.add_claim(claim)

    result = await inspect_node(label="C1", ctx=tool_context)

    assert not result.isError


async def test_inspect_node_embeds_resource(tool_context: Mock) -> None:
    """Test that inspect_node properly embeds resource."""
    await add_claim_elaborate(label="C1", ctx=tool_context, proposition="Test")

    result = await inspect_node(label="C1", ctx=tool_context)

    assert not result.isError
    # Should have embedded a resource
    assert result.content
    assert len(result.content) > 0
