"""KOALA MCP server main entry point."""

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.utilities.logging import get_logger, configure_logging

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Literal
import json

from koala.config.settings import settings
from koala.graph.argument_map import ArgumentMap
from koala.graph.persistence import load_graph, save_graph
from koala.models.base import Mode

configure_logging(level="INFO")
logger = get_logger("koala")  # Creates 'FastMCP.koala' logger


# === Application Context ===

@dataclass
class AppContext:
    """Application state containing the argument map."""
    arg_map: ArgumentMap
    mode: Mode


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle - load and save argument map."""
    data_file = settings.data_file
    
    # Load argument map on startup
    try:
        arg_map = load_graph(data_file)
        print(f"Loaded argument map from {data_file}")
    except FileNotFoundError:
        arg_map = ArgumentMap()
        print("Created new argument map")
    
    try:
        yield AppContext(arg_map=arg_map, mode="sketch")
    finally:
        # Save on shutdown
        save_graph(arg_map, data_file)
        print(f"Saved argument map to {data_file}")


# === Server Initialization ===

mcp = FastMCP(
    "KOALA Argument Mapper",
    lifespan=app_lifespan,
    stateless_http=False  # Stateful server with persistent graph
)


# === Entry Point ===

def main() -> None:
    """Run the KOALA MCP server."""
    import sys
    
    # Import tools/resources/prompts to register them
    import koala.tools  # noqa: F401
    from koala.resources import graph_views  # noqa: F401
    from koala.prompts import analysis  # noqa: F401
    
    # Determine transport from command line or default to stdio
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        transport = "streamable-http"
    
    print(f"Starting KOALA MCP server with {transport} transport...")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

