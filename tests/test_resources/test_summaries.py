"""Unit tests for statistics/summaries resource."""

import pytest
from unittest.mock import Mock, patch
from koala.resources.summaries import statistics_resource
from koala.server import mcp, AppContext
from koala.graph.argument_map import ArgumentMap


@pytest.fixture
def mock_context(sample_arg_map: ArgumentMap) -> Mock:
    """Create mock MCP context."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=sample_arg_map,
        mode="sketch"
    )
    return ctx


@pytest.mark.asyncio
async def test_statistics_returns_dict(mock_context: Mock) -> None:
    """Test statistics resource returns a dictionary."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await statistics_resource()
        
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_statistics_has_required_fields(mock_context: Mock) -> None:
    """Test statistics includes all required fields."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await statistics_resource()
        
        assert "num_nodes" in result
        assert "num_claims" in result
        assert "num_arguments" in result
        assert "num_roots" in result
        assert "num_connected_components" in result
        assert "is_acyclic" in result
        assert "longest_path_length" in result
        assert "active_editing_mode" in result


@pytest.mark.asyncio
async def test_statistics_values_correct(mock_context: Mock) -> None:
    """Test statistics values are correct for sample graph."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await statistics_resource()
        
        # Sample graph has 2 claims, 1 argument = 3 nodes
        assert result["num_nodes"] == 3
        assert result["num_claims"] == 2
        assert result["num_arguments"] == 1
        assert result["active_editing_mode"] == "sketch"


@pytest.mark.asyncio
async def test_statistics_reflects_mode(empty_arg_map: ArgumentMap) -> None:
    """Test statistics reflects current mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="review"
    )
    
    with patch.object(mcp, 'get_context', return_value=ctx):
        result = await statistics_resource()
        
        assert result["active_editing_mode"] == "review"
