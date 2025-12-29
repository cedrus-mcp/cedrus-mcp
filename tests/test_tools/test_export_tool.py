"""Unit tests for export tool."""

import pytest
from unittest.mock import Mock, patch
from koala.tools.tools import add, export_svg
from koala.server import AppContext
from koala.graph.argument_map import ArgumentMap
from mcp.types import ImageContent


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


@pytest.mark.asyncio
async def test_export_svg_basic(tool_context: Mock) -> None:
    """Test exporting SVG with basic graph."""
    # Add some nodes
    add(label="C1", ctx=tool_context, node_options={"proposition": "Claim 1"})
    add(label="C2", ctx=tool_context, node_options={"proposition": "Claim 2"})
    
    # Mock the export_svg function to avoid GraphViz dependency
    with patch('koala.tools.tools.export_svg') as mock_export:
        mock_export.return_value = '<svg>test</svg>'
        
        result = await export_svg(ctx=tool_context)
        
        assert not result.isError
        assert len(result.content) > 0
        assert isinstance(result.content[0], ImageContent)
        assert result.content[0].mimeType == "image/svg+xml"


@pytest.mark.asyncio
async def test_export_includes_metadata(tool_context: Mock) -> None:
    """Test that export includes structured metadata."""
    # Add nodes
    add(label="C1", ctx=tool_context, node_options={"proposition": "Claim"})
    add(label="A1", ctx=tool_context, node_options={"node_type": "argument", "gist": "Arg"})
    
    with patch('koala.tools.tools.export_svg') as mock_export:
        mock_export.return_value = '<svg>test</svg>'
        
        result = await export_svg(ctx=tool_context)
        
        assert not result.isError
        assert result.structuredContent is not None
        assert "total_nodes" in result.structuredContent
        assert "claim_count" in result.structuredContent
        assert "argument_count" in result.structuredContent


@pytest.mark.asyncio
async def test_export_handles_graphviz_error(tool_context: Mock) -> None:
    """Test that export handles GraphViz errors gracefully."""
    with patch('koala.graph.svg_export.export_svg') as mock_export:
        mock_export.side_effect = RuntimeError("GraphViz not installed")
        result = await export_svg(ctx=tool_context)
        
        # Error is indicated in structured content, not isError flag
        assert result.structuredContent["status"] == "failure"
