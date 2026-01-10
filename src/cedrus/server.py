"""CEDRUS MCP server instance with lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from cedrus.config.settings import settings
from cedrus.graph.argument_map import ArgumentMap
from cedrus.models.base import Mode


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
The `reasoning-graph` MCP server equips AI agents with tools to structure their internal \
thinking. It allows you to organize heterogeneous and conflicting reasoning as structured \
argumentation, and provides capabilities to outline, elaborate, validate, and revise such \
reasoning graphs.

Depending on your needs, you can operate the `reasoning-graph` MCP server in different \
**modes**.

The availability, signature and functionality of tools depends on the current mode of operation.

- `sketch` mode: simple tools for basic argument mapping
- `elaborate` mode: tools for advanced argumentation analysis
- `review` mode: focus on validation and review tools

> CALLOUT NOTE
> Take care to study updated tool lists after switching mode.

The server provides conceptual guidance and technical documentation that can be dynamically \
retrieved via corresponding tools. It also suggests next actions that help AI agents to organize \
and structure their thinking.\
"""

# Create the MCP server instance
mcp = FastMCP(
    "reasoning-graph",
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
        1. Import TOOL_REGISTRY and TOOL_ORDER (triggers tool variant registration)
        2. Iterate through tools in TOOL_ORDER
        3. For each tool available in initial mode, register it with MCP server
        4. Log the number of tools registered
    
    Initial Mode:
        Default mode is "sketch" for rapid prototyping:
        - add_claim (simplified)
        - add_argument (simplified)
        - connect (no grounding)
        - remove
        - Shared tools (instructions, inspect_graph, etc.)
    
    Tool Ordering:
        Tools are registered in the order defined by TOOL_ORDER to ensure
        consistent presentation to clients. This order groups tools logically:
        creation → modification → connection → inspection → utilities.
    
    Notes:
        - This function must be called AFTER the tool registry is populated
          (which happens on import of cedrus.tools.tools)
        - Subsequent mode changes use _update_tools_for_mode() in tools.py
        - The MCP server's tool list is modified in-place via add_tool()
    
    See Also:
        - cedrus.tools.tools._update_tools_for_mode(): Dynamic tool swapping
        - cedrus.tools.tools.TOOL_ORDER: Canonical tool ordering
        - cedrus.tools.tool_registry.ToolRegistry: Registry infrastructure
    """
    from cedrus.tools.tool_registry import TOOL_REGISTRY
    from cedrus.tools.tools import TOOL_ORDER
    from cedrus.models.base import Mode
    
    # Get initial mode and available tools
    initial_mode: Mode = "sketch"
    available_tools = TOOL_REGISTRY.get_tool_names_for_mode(initial_mode)
    
    # Register tools in canonical order
    for tool_name in TOOL_ORDER:
        if tool_name in available_tools:
            variant = TOOL_REGISTRY.get_variant_for_mode(tool_name, initial_mode)
            if variant:
                mcp.add_tool(
                    variant.fn,
                    name=variant.name,
                    description=variant.description,
                    **variant.metadata
                )
    
    print(f"Registered {len(available_tools)} tools for '{initial_mode}' mode")


# This will be called when tools module is imported
# (which happens when the tool_registry is initialized)
_register_initial_tools()
