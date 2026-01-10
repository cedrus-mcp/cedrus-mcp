"""Unit tests for graph view resources."""

from unittest.mock import Mock, patch

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.resources.graph_views import (
    graph_details_resource,
    graph_thin_resource,
    neighborhood_details_resource,
)
from cedrus.server import AppContext, mcp


@pytest.fixture
def mock_context(sample_arg_map: ArgumentMap) -> Mock:
    """Create mock MCP context."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=sample_arg_map, mode="sketch")
    return ctx


@pytest.mark.asyncio
async def test_graph_thin_resource_format(mock_context: Mock) -> None:
    """Test graph thin resource returns correct format."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        result = await graph_thin_resource()

        assert isinstance(result, str)
        assert result.startswith("```argdown")
        assert result.endswith("```")


@pytest.mark.asyncio
async def test_graph_details_resource_format(mock_context: Mock) -> None:
    """Test graph details resource returns correct format."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        result = await graph_details_resource()

        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_graph_details_mode_variation(sample_arg_map: ArgumentMap) -> None:
    """Test graph details varies by mode."""
    # Test in sketch mode
    ctx_sketch = Mock()
    ctx_sketch.request_context.lifespan_context = AppContext(arg_map=sample_arg_map, mode="sketch")

    with patch.object(mcp, "get_context", return_value=ctx_sketch):
        result_sketch = await graph_details_resource()

    # Test in elaborate mode
    ctx_elaborate = Mock()
    ctx_elaborate.request_context.lifespan_context = AppContext(
        arg_map=sample_arg_map, mode="elaborate"
    )

    with patch.object(mcp, "get_context", return_value=ctx_elaborate):
        result_elaborate = await graph_details_resource()

    # Both should be valid argdown
    assert "```argdown" in result_sketch
    assert "```argdown" in result_elaborate


@pytest.mark.asyncio
async def test_neighborhood_resource_k1(mock_context: Mock) -> None:
    """Test neighborhood resource with k=1."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        result = await neighborhood_details_resource(label="C1", k=1)

        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_neighborhood_resource_k2(mock_context: Mock) -> None:
    """Test neighborhood resource with k=2."""
    with patch.object(mcp, "get_context", return_value=mock_context):
        result = await neighborhood_details_resource(label="C1", k=2)

        assert isinstance(result, str)
        assert "```argdown" in result
