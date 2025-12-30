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

import argparse

from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger

from koala.server import mcp

configure_logging(level="INFO")
logger = get_logger("koala")  # Creates 'FastMCP.koala' logger


# === Register Tools/Resources/Prompts ===
# Import at module level to ensure decorators execute before mcp.run()
import koala.tools  # noqa: F401
import koala.prompts  # noqa: F401
import koala.resources  # noqa: F401





# === Entry Point ===

def main() -> None:
    """Run the KOALA MCP server."""
    # Determine transport from command line or default to stdio

    parser = argparse.ArgumentParser(description="KOALA MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport instead of stdio",
    )
    args = parser.parse_args()

    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    if args.http:
        transport = "streamable-http"

    print(f"Starting KOALA MCP server with {transport} transport ...")
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()

