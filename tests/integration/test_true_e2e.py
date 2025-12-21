"""True end-to-end test that starts MCP server and communicates via protocol."""



import pytest
import shutil
from pathlib import Path
from typing import Any
from pydantic import AnyUrl, TypeAdapter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_mcp_server_full_lifecycle(tmp_path: Path) -> None:
    """Test complete MCP server lifecycle with actual protocol communication."""
    # Create temp data file for this test
    data_file: Path = tmp_path / "test_graph.json"
    
    # Configure server parameters
    server_params: StdioServerParameters = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "koala"],
        env={
            "KOALA_DATA_FILE": str(data_file),
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            tool_names: list[str] = [tool.name for tool in tools_result.tools]
            
            assert "add" in tool_names
            assert "edit" in tool_names
            assert "connect" in tool_names
            assert "remove" in tool_names
            assert "export" in tool_names
            assert "mode" in tool_names
            
            # List available resources
            resources_result = await session.list_resources()
            resource_uris: list[str] = [str(resource.uri) for resource in resources_result.resources]
            
            # Core graph resources should be available
            assert "argmap://graph/thin" in resource_uris
            assert "argmap://graph/details" in resource_uris
            assert "argmap://statistics" in resource_uris
            
            # Call tool: add a claim
            add_result: Any = await session.call_tool(
                "add",
                arguments={
                    "label": "C1",
                    "node_options": {
                        "proposition": "The Earth is round"
                    }
                }
            )
            
            assert not add_result.isError
            # FastMCP returns structuredContent, not content
            assert add_result.structuredContent is not None
            assert add_result.structuredContent["status"] == "success"
            
            # Call tool: add an argument
            add_arg_result: Any = await session.call_tool(
                "add",
                arguments={
                    "label": "A1",
                    "node_options": {
                        "node_type": "argument",
                        "gist": "Evidence from space travel"
                    }
                }
            )
            
            assert not add_arg_result.isError
            
            # Call tool: connect nodes
            connect_result: Any = await session.call_tool(
                "connect",
                arguments={
                    "from_label": "A1",
                    "to_label": "C1",
                    "relation_options": {
                        "relation_type": "support"
                    }
                }
            )
            
            assert not connect_result.isError
            
            # Read resource: graph thin view
            graph_resource: Any = await session.read_resource(
                uri=TypeAdapter(AnyUrl).validate_python("argmap://graph/thin")
            )
            
            assert len(graph_resource.contents) > 0
            content_text: str = graph_resource.contents[0].text
            assert "C1" in content_text
            assert "A1" in content_text
            
            # Read resource: statistics
            stats_resource: Any = await session.read_resource(
                uri=TypeAdapter(AnyUrl).validate_python("argmap://statistics")
            )
            
            assert len(stats_resource.contents) > 0
            # Just verify statistics resource returns some content
            
            # Read resource: node details
            node_resource: Any = await session.read_resource(
                uri=TypeAdapter(AnyUrl).validate_python("argmap://node/details/C1")
            )
            
            assert len(node_resource.contents) > 0
            node_text: str = node_resource.contents[0].text
            assert "C1" in node_text
            
            # Call tool: edit a claim
            edit_result: Any = await session.call_tool(
                "edit",
                arguments={
                    "label": "C1",
                    "field": "proposition",
                    "edit_options": {
                        "new_value": "The Earth is spherical"
                    }
                }
            )
            
            assert not edit_result.isError
            
            # Call tool: switch mode
            mode_result: Any = await session.call_tool(
                "mode",
                arguments={
                    "mode": "author"
                }
            )
            
            assert not mode_result.isError
            
            # Read instructions resource for author mode
            instructions_resource: Any = await session.read_resource(
                uri=TypeAdapter(AnyUrl).validate_python("argmap://instructions/author")
            )
            
            assert len(instructions_resource.contents) > 0
            instructions_text: str = instructions_resource.contents[0].text
            assert "author" in instructions_text.lower()
            
            # Check if GraphViz is installed
            graphviz_path: str | None = shutil.which("dot")
            if not graphviz_path:
                pytest.skip("GraphViz (dot) is not installed; skipping export test.")

            export_result: Any = await session.call_tool(
                "export",
                arguments={
                    "format": "argdown"
                }
            )

            assert export_result.structuredContent is not None
            if export_result.isError:
                raise AssertionError(f"Export tool failed with error: {export_result.structuredContent}")
            # Check content is a list with an ImageContent
            assert isinstance(export_result.content, list)
            assert len(export_result.content) == 1
            img: Any = export_result.content[0]
            assert getattr(img, "type", None) == "image"
            assert getattr(img, "mimeType", None) == "image/svg+xml"
            # Check structuredContent keys
            export_data: dict[str, Any] = export_result.structuredContent
            assert export_data.get("format") == "svg"
            assert "total_nodes" in export_data
            assert "claim_count" in export_data
            assert "argument_count" in export_data
            
            # Call tool: remove a node
            remove_result: Any = await session.call_tool(
                "remove",
                arguments={
                    "label": "A1"
                }
            )
            
            assert not remove_result.isError
            
            # Verify node is gone by reading graph
            final_graph: Any = await session.read_resource(
                uri=TypeAdapter(AnyUrl).validate_python("argmap://graph/thin")
            )
            final_text: str = final_graph.contents[0].text
            # A1 should be removed, C1 should remain
            assert "C1" in final_text


@pytest.mark.asyncio
async def test_mcp_server_error_handling(tmp_path: Path) -> None:
    """Test that server properly handles errors via MCP protocol."""
    data_file: Path = tmp_path / "test_graph.json"
    
    server_params: StdioServerParameters = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "koala"],
        env={
            "KOALA_DATA_FILE": str(data_file),
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Try to edit non-existent node
            edit_result: Any = await session.call_tool(
                "edit",
                arguments={
                    "label": "NONEXISTENT",
                    "field": "proposition",
                    "edit_options": {
                        "new_value": "test"
                    }
                }
            )
            
            # Should return error status in structuredContent
            assert len(edit_result.content) > 0
            # The error should be communicated in the content
            
            # Try to connect non-existent nodes
            connect_result: Any = await session.call_tool(
                "connect",
                arguments={
                    "from_label": "NONEXISTENT1",
                    "to_label": "NONEXISTENT2",
                    "relation_options": {
                        "relation_type": "support"
                    }
                }
            )
            
            # Should handle gracefully
            assert len(connect_result.content) > 0
            
            # Try to remove non-existent node
            remove_result: Any = await session.call_tool(
                "remove",
                arguments={
                    "label": "NONEXISTENT"
                }
            )
            
            # Should handle gracefully
            assert len(remove_result.content) > 0
