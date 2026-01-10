"""Inspection-related MCP tool implementations.

This module hosts the core implementations for graph inspection tools,
refactored out of :mod:`cedrus.tools.tools`.

The functions here intentionally mirror the behavior of the legacy
``inspect_graph``, ``inspect_neighborhood`` and ``inspect_node``
functions. The goal for this first step is a mechanical move with
no semantic changes – the logic is copied as-is so that tests can
validate equivalence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult
from pydantic import AnyUrl

from cedrus.backend.models import NodeLabel
from cedrus.tools.runtime import tool_context

if TYPE_CHECKING:
    from cedrus.server import AppContext


logger = get_logger("cedrus.tools.impl.inspection")


async def inspect_graph_core(
    *,
    ctx: Context[ServerSession, AppContext],
    verbose: bool = False,
    format: Literal["argdown", "tree"] = "argdown",
) -> CallToolResult:
    """Show an overview representation of the current argumentation graph.

    This is a direct port of :func:`cedrus.tools.tools.inspect_graph` with
    unchanged behavior.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if format not in ["argdown", "tree"]:
            return tc.failure(
                f"Invalid format '{format}'. Supported formats are 'argdown' and 'tree'.",
                error="InvalidFormat",
            ).build()

        # embed graph
        try:
            import cedrus.resources

            if verbose:
                text = await cedrus.resources.graph_views.graph_details_resource(format=format)
                uri = AnyUrl(f"argmap://graph/details/{format}")
            else:
                text = await cedrus.resources.graph_views.graph_thin_resource(format=format)
                uri = AnyUrl(f"argmap://graph/thin/{format}")
            tc.embed_resource(uri=uri, text=text)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error showing graph representation: {str(e)}")
            return tc.failure(
                f"✗ Failed to show graph representation: {str(e)}", error=str(e)
            ).build()

        # embed statistics
        try:
            if verbose:
                stats = await cedrus.resources.summaries.statistics_resource()
                text = f"# Graph Statistics\n\n{stats}"
                tc.embed_resource(uri=AnyUrl("argmap://statistics"), text=text)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error showing graph statistics: {str(e)}")
            tc.issue("warning", f"✗ Failed to show graph statistics: {str(e)}", error=str(e))

    tc.success("✓ Printed graph representation.")
    return tc.build()


async def inspect_neighborhood_core(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
    k: int = 2,
) -> CallToolResult:
    """Show detailed information about the k-neighborhood of a node.

    Direct port of :func:`cedrus.tools.tools.inspect_neighborhood`.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if not arg_map.is_node(label):
            most_similar_label, _ = next(arg_map.most_similar_labels(label), (None, 0))
            msg = f"Node '{label}' does not exist."
            if most_similar_label:
                msg += f" Did you mean '{most_similar_label}'?"
            return tc.failure(msg, error="NonExistentNode").build()
        if k < 1:
            return tc.failure(
                f"Invalid neighborhood radius k={k}. Must be a positive integer.",
                error="InvalidKValue",
            ).build()

        try:
            import cedrus.resources

            uri = f"argmap://neighborhood/{label}/{k}"
            text = await cedrus.resources.graph_views.neighborhood_details_resource(label, k)
            tc.embed_resource(uri=AnyUrl(uri), text=text)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error showing neighborhood of node '{label}': {str(e)}")
            return tc.failure(
                f"✗ Failed to show neighborhood of node '{label}': {str(e)}", error=str(e)
            ).build()

    tc.success(f"✓ Printed {k}-neighborhood of node '{label}'.")
    return tc.build()


async def inspect_node_core(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
) -> CallToolResult:
    """Show detailed information about a specific node in the argument map.

    Direct port of :func:`cedrus.tools.tools.inspect_node`.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if not arg_map.is_node(label):
            most_similar_label, _ = next(arg_map.most_similar_labels(label), (None, 0))
            msg = f"Node '{label}' does not exist."
            if most_similar_label:
                msg += f" Did you mean '{most_similar_label}'?"
            return tc.failure(msg, error="NonExistentNode").build()

        try:
            import cedrus.resources

            uri = f"argmap://node/details/{label}"
            text = await cedrus.resources.node_details.node_details_resource(label)
            tc.embed_resource(uri=AnyUrl(uri), text=text)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error showing details of node '{label}': {str(e)}")
            return tc.failure(f"✗ Failed to show details of node '{label}'.", error=str(e)).build()

    tc.success(f"✓ Printed details of node '{label}'.")
    return tc.build()


__all__ = [
    "inspect_graph_core",
    "inspect_neighborhood_core",
    "inspect_node_core",
]
