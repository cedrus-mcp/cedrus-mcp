"""KOALA MCP server entry point.

This module serves as the main entry point for running the KOALA MCP server.
It imports and registers all tools, resources, and prompts, then starts the
FastMCP server with the specified transport.

Usage:
    # Run with stdio transport (default, for MCP clients):
    python -m koala
    
    # Run with HTTP transport (for debugging/testing):
    python -m koala --http
    
    # Using uv:
    uv run python -m koala

The server provides tools for creating and managing informal argument maps,
including claims, arguments, and dialectical relations between them.
"""

import sys
from typing import Literal

from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger

from koala.server import mcp

configure_logging(level="INFO")
logger = get_logger("koala")  # Creates 'FastMCP.koala' logger


# === Register Tools/Resources/Prompts ===
# Import at module level to ensure decorators execute before mcp.run()
import koala.tools  # noqa: F401
from koala.prompts import analysis  # noqa: F401
from koala.resources import graph_views  # noqa: F401


# === Entry Point ===

def main() -> None:
    """Run the KOALA MCP server."""
    # Determine transport from command line or default to stdio
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        transport = "streamable-http"

    print(f"Starting KOALA MCP server with {transport} transport...")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

