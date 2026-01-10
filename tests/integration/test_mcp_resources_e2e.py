"""End-to-end integration tests for MCP resources via protocol."""

from unittest.mock import Mock, patch

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models.base import Mode
from cedrus.resources.graph_views import (
    graph_details_resource,
    graph_thin_resource,
    neighborhood_details_resource,
)
from cedrus.resources.instructions import instruction_resource
from cedrus.resources.node_details import node_details_resource
from cedrus.resources.summaries import statistics_resource
from cedrus.server import AppContext, mcp


@pytest.fixture
def mock_mcp_context(sample_arg_map: ArgumentMap, mode: Mode = "sketch") -> Mock:
    """Mock MCP get_context for resource testing."""
    mock_ctx = Mock()
    mock_ctx.request_context.lifespan_context = AppContext(arg_map=sample_arg_map, mode=mode)
    return mock_ctx


@pytest.mark.asyncio
async def test_graph_thin_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test graph thin resource returns argdown format."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await graph_thin_resource()

        assert isinstance(result, str)
        assert "```argdown" in result
        assert "C1" in result or "C2" in result


@pytest.mark.asyncio
async def test_graph_details_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test graph details resource returns detailed argdown."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await graph_details_resource()

        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_neighborhood_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test neighborhood resource for specific node."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await neighborhood_details_resource(label="C1", k=1)

        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_node_details_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test node details resource for specific node."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await node_details_resource(label="C1")

        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_statistics_resource(mock_mcp_context: Mock, sample_arg_map: ArgumentMap) -> None:
    """Test statistics resource returns graph metrics."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await statistics_resource()

        assert isinstance(result, dict)
        assert "num_nodes" in result
        assert "num_claims" in result
        assert "num_arguments" in result
        assert result["num_nodes"] == 3
        assert result["active_editing_mode"] == "sketch"


@pytest.mark.asyncio
async def test_instructions_resource_sketch(mock_mcp_context: Mock, mode: Mode = "sketch") -> None:
    """Test instruction resource for sketch mode."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "sketch" in result.lower()


@pytest.mark.asyncio
async def test_instructions_resource_elaborate(
    mock_mcp_context: Mock, mode: Mode = "elaborate"
) -> None:
    """Test instruction resource for elaborate mode."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        mcp.get_context().request_context.lifespan_context.mode = mode
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "elaborate" in result.lower()


@pytest.mark.asyncio
async def test_instructions_resource_review(mock_mcp_context: Mock, mode: Mode = "review") -> None:
    """Test instruction resource for review mode."""
    with patch.object(mcp, "get_context", return_value=mock_mcp_context):
        mcp.get_context().request_context.lifespan_context.mode = mode
        result = await instruction_resource()

        assert isinstance(result, str)
        assert "review" in result.lower()
