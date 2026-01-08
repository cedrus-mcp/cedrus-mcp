"""KOALA MCP server instance with lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from koala.config.settings import settings
from koala.graph.argument_map import ArgumentMap
from koala.models.base import Mode


@dataclass
class AppContext:
    """Application state containing the argument map."""

    arg_map: ArgumentMap
    mode: Mode


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle - load and save argument map."""
    # data_file = settings.data_file
    #
    # # Load argument map on startup
    # try:
    #     arg_map = load_graph(data_file)
    #     print(f"Loaded argument map from {data_file}")
    # except FileNotFoundError:
    #     arg_map = ArgumentMap()
    #     print("Created new argument map")
    # 
    # try:
    #     yield AppContext(arg_map=arg_map, mode="sketch")
    # finally:
    #     # Save on shutdown
    #     save_graph(arg_map, data_file)
    #     print(f"Saved argument map to {data_file}")

    print(f"Settings: {settings}")

    yield AppContext(arg_map=ArgumentMap(), mode="sketch")

instructions="""\
The KOALA MCP server equips AI agents with tools to structure their internal thinking. \
It allows agents to organize heterogeneous and conflicting reasoning in a structured \
argumentation graph, and provides capabilities to sketch, refine and review such argumentation \
graphs.\
"""

# Create the MCP server instance
mcp = FastMCP(
    "KOALA Structured Thinking MCP Server",
    instructions=instructions,
    lifespan=app_lifespan,
    stateless_http=False,
)


# Register tools for initial mode (sketch)
def _register_initial_tools() -> None:
    """Register tools available in the initial mode (sketch).
    
    Called once at server startup to populate the MCP server with tools
    appropriate for the default mode. As users switch modes, tools are
    dynamically added/removed via the tool registry system.
    
    Flow:
        1. Import TOOL_REGISTRY (triggers tool variant registration in tools.py)
        2. Get all tool variants for initial mode ("sketch")
        3. Register each variant with the MCP server via mcp.add_tool()
        4. Log the number of tools registered
    
    Initial Mode:
        Default mode is "sketch" for rapid prototyping:
        - add_claim (simplified)
        - add_argument (simplified)
        - connect (no grounding)
        - remove
        - Shared tools (instructions, inspect_graph, etc.)
    
    Notes:
        - This function must be called AFTER the tool registry is populated
          (which happens on import of koala.tools.tools)
        - Subsequent mode changes use _update_tools_for_mode() in tools.py
        - The MCP server's tool list is modified in-place via add_tool()
    
    See Also:
        - koala.tools.tools._update_tools_for_mode(): Dynamic tool swapping
        - koala.tools.tool_registry.ToolRegistry: Registry infrastructure
    """
    from koala.tools.tool_registry import TOOL_REGISTRY
    from koala.models.base import Mode
    
    # Get all tools for sketch mode
    initial_mode: Mode = "sketch"
    for variant in TOOL_REGISTRY.get_all_tools_for_mode(initial_mode):
        mcp.add_tool(
            variant.fn,
            name=variant.name,
            description=variant.description,
            **variant.metadata
        )
    
    print(f"Registered {len(TOOL_REGISTRY.get_tool_names_for_mode(initial_mode))} tools for '{initial_mode}' mode")


# This will be called when tools module is imported
# (which happens when the tool_registry is initialized)
_register_initial_tools()
