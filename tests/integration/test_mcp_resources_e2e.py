"""End-to-end integration tests for MCP resources via protocol."""

import pytest
from unittest.mock import Mock, patch
from koala.models.base import Mode
from koala.resources.graph_views import graph_thin_resource, graph_details_resource, neighborhood_details_resource
from koala.resources.node_details import node_details_resource
from koala.resources.summaries import statistics_resource
from koala.resources.instructions import instruction_resource
from koala.server import mcp, AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def mock_mcp_context(sample_arg_map: ArgumentMap, mode: Mode = "sketch") -> Mock:
    """Mock MCP get_context for resource testing."""
    mock_ctx = Mock()
    mock_ctx.request_context.lifespan_context = AppContext(
        arg_map=sample_arg_map,
        mode=mode
    )
    return mock_ctx


@pytest.mark.asyncio
async def test_graph_thin_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test graph thin resource returns argdown format."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await graph_thin_resource()
        
        assert isinstance(result, str)
        assert "```argdown" in result
        assert "C1" in result or "C2" in result


@pytest.mark.asyncio
async def test_graph_details_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test graph details resource returns detailed argdown."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await graph_details_resource()
        
        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_neighborhood_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test neighborhood resource for specific node."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await neighborhood_details_resource(label="C1", k=1)
        
        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_node_details_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test node details resource for specific node."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await node_details_resource(label="C1")
        
        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_statistics_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test statistics resource returns graph metrics."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await statistics_resource()
        
        assert isinstance(result, dict)
        assert "num_nodes" in result
        assert "num_claims" in result
        assert "num_arguments" in result
        assert result["num_nodes"] == 3
        assert result["active_editing_mode"] == "sketch"


@pytest.mark.asyncio
async def test_instructions_resource_sketch(mock_mcp_context: Mock, mode = "sketch") -> None:
    """Test instruction resource for sketch mode."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "sketch" in result.lower()


@pytest.mark.asyncio
async def test_instructions_resource_author(mock_mcp_context: Mock, mode = "author") -> None:
    """Test instruction resource for author mode."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        mcp.get_context().request_context.lifespan_context.mode = mode
        result = await instruction_resource()
        
        assert isinstance(result, str)
        assert "author" in result.lower()


@pytest.mark.asyncio
async def test_instructions_resource_review(mock_mcp_context: Mock, mode = "review") -> None:
    """Test instruction resource for review mode."""
    with patch.object(mcp, 'get_context', return_value=mock_mcp_context):
        mcp.get_context().request_context.lifespan_context.mode = mode
        result = await instruction_resource()
        
        assert isinstance(result, str)
        assert "review" in result.lower()
