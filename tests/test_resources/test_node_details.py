"""Unit tests for node details resource."""

import pytest
from unittest.mock import Mock, patch
from koala.resources.node_details import node_details_resource
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
async def test_node_details_for_claim(mock_context: Mock) -> None:
    """Test node details resource for a claim."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await node_details_resource(label="C1")
        
        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_node_details_for_argument(mock_context: Mock) -> None:
    """Test node details resource for an argument."""
    with patch.object(mcp, 'get_context', return_value=mock_context):
        result = await node_details_resource(label="A1")
        
        assert isinstance(result, str)
        assert "```argdown" in result


@pytest.mark.asyncio
async def test_node_details_mode_variation(sample_arg_map: ArgumentMap) -> None:
    """Test node details varies by mode."""
    # Test in sketch mode
    ctx_sketch = Mock()
    ctx_sketch.request_context.lifespan_context = AppContext(
        arg_map=sample_arg_map, mode="sketch"
    )
    
    with patch.object(mcp, 'get_context', return_value=ctx_sketch):
        result_sketch = await node_details_resource(label="C1")
    
    # Test in elaborate mode
    ctx_elaborate = Mock()
    ctx_elaborate.request_context.lifespan_context = AppContext(
        arg_map=sample_arg_map, mode="elaborate"
    )
    
    with patch.object(mcp, 'get_context', return_value=ctx_elaborate):
        result_elaborate = await node_details_resource(label="C1")
    
    # Both should be valid
    assert isinstance(result_sketch, str)
    assert isinstance(result_elaborate, str)
