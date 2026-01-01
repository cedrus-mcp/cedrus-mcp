"""End-to-end integration tests for MCP tools via protocol."""

import pytest
from unittest.mock import Mock
from mcp.types import CallToolResult
from koala.tools.tools import (
    add_claim_sketch,
    add_argument_sketch,
    edit,
    connect_sketch,
    remove,
    set_mode,
)
from koala.server import AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def mock_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create a mock MCP context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


async def test_add_tool_creates_claim(mock_context: Mock) -> None:
    """Test adding a claim via add tool."""
    result = await add_claim_sketch(
        label="C1",
        ctx=mock_context,
        proposition="Test claim"
    )
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    assert mock_context.request_context.lifespan_context.arg_map.get_node("C1") is not None


async def test_add_tool_creates_argument(mock_context: Mock) -> None:
    """Test adding an argument via add tool."""
    result = await add_argument_sketch(
        label="A1",
        ctx=mock_context,
        gist="Test argument"
    )
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    assert mock_context.request_context.lifespan_context.arg_map.get_node("A1") is not None


async def test_connect_tool_creates_relation(mock_context: Mock) -> None:
    """Test creating a relation via connect tool."""
    arg_map = mock_context.request_context.lifespan_context.arg_map
    
    # Add nodes first
    await add_claim_sketch(label="C1", ctx=mock_context, proposition="Claim 1")
    await add_argument_sketch(label="A1", ctx=mock_context, gist="Arg 1")
    
    # Connect them
    result = await connect_sketch(
        source="A1",
        target="C1",
        relation_type="support",
        ctx=mock_context,
    )
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    assert arg_map.get_dialectic_relation("A1", "C1") is not None


async def test_edit_tool_updates_claim(mock_context: Mock) -> None:
    """Test editing a claim via edit tool."""
    # Add a claim first in sketch mode
    await add_claim_sketch(label="C1", ctx=mock_context, proposition="Original")
    
    # Switch to author mode for editing
    mock_context.request_context.lifespan_context.mode = "author"
    
    # Edit it (edit is a shared tool, and is synchronous)
    result = edit(
        label="C1",
        field="proposition",
        ctx=mock_context,
        edit_options={"new_value": "Updated"}
    )
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    arg_map = mock_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    prop = arg_map.get_proposition(node.proposition_id)
    assert prop.content == "Updated"


async def test_remove_tool_deletes_node(mock_context: Mock) -> None:
    """Test removing a node via remove tool."""
    # Add a claim first
    await add_claim_sketch(label="C1", ctx=mock_context, proposition="Test")
    
    # Remove it (remove is a shared tool, and is synchronous)
    result = remove(label="C1", ctx=mock_context)
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    # After removal, node should not exist
    with pytest.raises(KeyError):
        mock_context.request_context.lifespan_context.arg_map.get_node("C1")


async def test_mode_tool_switches_mode(mock_context: Mock) -> None:
    """Test switching mode via mode tool."""
    assert mock_context.request_context.lifespan_context.mode == "sketch"
    
    result = await set_mode(mode="author", ctx=mock_context)
    
    assert isinstance(result, CallToolResult)
    assert not result.isError
    assert mock_context.request_context.lifespan_context.mode == "author"


async def test_tool_chain_workflow(mock_context: Mock) -> None:
    """Test a complete workflow: add → connect → edit."""
    arg_map = mock_context.request_context.lifespan_context.arg_map
    
    # 1. Add two claims in sketch mode
    await add_claim_sketch(label="C1", ctx=mock_context, proposition="Claim 1")
    await add_claim_sketch(label="C2", ctx=mock_context, proposition="Claim 2")
    
    # 2. Add an argument
    await add_argument_sketch(label="A1", ctx=mock_context, gist="Argument")
    
    # 3. Connect them
    await connect_sketch(source="A1", target="C1", ctx=mock_context, relation_type="support")
    
    # 4. Switch to author mode and edit a claim (edit is a shared, synchronous tool)
    mock_context.request_context.lifespan_context.mode = "author"
    edit(label="C1", field="proposition", ctx=mock_context, edit_options={"new_value": "Updated Claim 1"})
    
    # Verify final state
    assert len(arg_map.argument_graph.nodes) == 3
    c1_node = arg_map.get_node("C1")
    c1_prop = arg_map.get_proposition(c1_node.proposition_id)
    assert c1_prop.content == "Updated Claim 1"
    # Relation exists (checking directly on graph to avoid deserialization issue)
    assert arg_map.argument_graph.has_edge("A1", "C1")
