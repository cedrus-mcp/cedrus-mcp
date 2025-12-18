"""KOALA MCP server instance with lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from koala.config.settings import settings
from koala.graph.argument_map import ArgumentMap
from koala.graph.persistence import load_graph, save_graph
from koala.models.base import Mode


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


# Create the MCP server instance
mcp = FastMCP(
    "KOALA Argument Mapper",
    lifespan=app_lifespan,
    stateless_http=False,
)
