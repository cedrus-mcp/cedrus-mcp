"""Unit tests for add tool."""

import pytest
from unittest.mock import Mock, patch
from koala.tools.tools import (
    add_claim_sketch,
    add_claim_elaborate,
    add_argument_sketch,
    add_argument_elaborate,
)
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


async def test_add_claim_sketch(tool_context_sketch: Mock) -> None:
    """Test adding a claim in sketch mode."""
    result = await add_claim_sketch(
        label="C1",
        ctx=tool_context_sketch,
        proposition="Test claim"
    )
    
    assert not result.isError
    arg_map = tool_context_sketch.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    assert node is not None
    # Get the proposition from the graph
    prop = arg_map.get_proposition(node.proposition_id)
    assert prop is not None
    assert prop.content == "Test claim"


async def test_add_claim_elaborate(tool_context_elaborate: Mock) -> None:
    """Test adding a claim in elaborate mode with tags."""
    result = await add_claim_elaborate(
        label="C1",
        ctx=tool_context_elaborate,
        proposition="Test claim",
        tags=["tag1", "tag2"]
    )
    
    assert not result.isError
    arg_map = tool_context_elaborate.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    assert node is not None
    assert node.tags == ["tag1", "tag2"]


async def test_add_argument_sketch(tool_context_sketch: Mock) -> None:
    """Test adding an argument in sketch mode."""
    result = await add_argument_sketch(
        label="A1",
        ctx=tool_context_sketch,
        gist="Test argument"
    )
    
    assert not result.isError
    arg_map = tool_context_sketch.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    assert node is not None
    assert node.gist == "Test argument"


async def test_add_argument_elaborate(tool_context_elaborate: Mock) -> None:
    """Test adding an argument in elaborate mode with full structure."""
    result = await add_argument_elaborate(
        label="A1",
        ctx=tool_context_elaborate,
        gist="Test argument",
        premises=["Premise 1", "Premise 2"],
        conclusion="Conclusion",
        tags=["tag1"]
    )
    
    assert not result.isError
    arg_map = tool_context_elaborate.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    assert node is not None
    assert node.gist == "Test argument"
    # Check premises were created (stored as separate proposition objects)
    assert len(node.premises) == 2
    assert node.tags == ["tag1"]


# async def test_add_with_relation(tool_context: Mock) -> None:
#     """Test adding a node with simultaneous relation creation."""
#     arg_map = tool_context.request_context.lifespan_context.arg_map
    
#     # Add first node
#     await add_claim(label="C1", ctx=tool_context, proposition="Claim 1")
    
#     # Add second node with relation
#     result = await add_argument(
#         label="A1",
#         ctx=tool_context,
#         gist="Argument",
#         relation_options={"target": "C1", "relation_type": "support"}
#     )
    
#     assert arg_map.get_dialectic_relation("A1", "C1") is not None

#     # Add third node with relation using alias names
#     result = await add_argument(
#         label="A2",
#         ctx=tool_context,
#         gist="Argument",
#         relation_options={"target": "C1", "type": "support"}
#     )

#     assert arg_map.get_dialectic_relation("A2", "C1") is not None
#     assert not result.isError


async def test_add_empty_label_fails(tool_context_sketch: Mock) -> None:
    """Test that empty label raises ValueError."""
    with pytest.raises(ValueError, match="Label must be a non-empty string"):
        await add_claim_sketch(
            label="",
            ctx=tool_context_sketch,
            proposition="Test"
        )


@patch("koala.resources.graph_views.mcp.get_context")
async def test_add_duplicate_label_gets_unique(mock_get_context, tool_context_sketch: Mock) -> None:
    """Test that duplicate labels are made unique."""
    # Mock the context returned by mcp.get_context
    mock_context = Mock()
    mock_request_context = Mock()
    mock_lifespan_context = tool_context_sketch.request_context.lifespan_context

    mock_request_context.lifespan_context = mock_lifespan_context
    mock_context.request_context = mock_request_context
    mock_get_context.return_value = mock_context

    arg_map = tool_context_sketch.request_context.lifespan_context.arg_map

    # Add first node
    await add_claim_sketch(label="C1", ctx=tool_context_sketch, proposition="First")

    # Try to add with same label
    result = await add_claim_sketch(label="C1", ctx=tool_context_sketch, proposition="Second")

    # Should succeed with modified label
    assert not result.isError
    # Original should still exist
    assert arg_map.get_node("C1") is not None
