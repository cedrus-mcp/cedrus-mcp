"""CEDRUS MCP server entry point.

This module serves as the main entry point for running the CEDRUS MCP server.
It imports and registers all tools, resources, and prompts, then starts the
FastMCP server with the specified transport.

Usage:
    # Run with stdio transport (default, for MCP clients):
    python -m cedrus

    # Run with HTTP transport (for debugging/testing):
    python -m cedrus --http

    # Using uv:
    uv run python -m cedrus

The server provides tools for creating and managing informal argument maps,
including claims, arguments, and dialectical relations between them.
"""

import argparse
import sys
from typing import Literal

from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger

# === Register Tools/Resources/Prompts ===
# Import at module level to ensure decorators execute before mcp.run()
import cedrus.prompts  # noqa: F401
import cedrus.resources  # noqa: F401
import cedrus.tools  # noqa: F401
from cedrus.server import mcp

# === Logging ===

configure_logging(level="INFO")
logger = get_logger("cedrus")  # Creates 'FastMCP.cedrus' logger


# === Entry Point ===


def main() -> None:
    """Run the CEDRUS MCP server."""
    # Determine transport from command line or default to stdio

    parser = argparse.ArgumentParser(description="CEDRUS MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Use HTTP transport instead of stdio",
    )
    args = parser.parse_args()

    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    if args.http:
        transport = "streamable-http"

    logger.info(f"Starting CEDRUS MCP server with {transport} transport ...")
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
