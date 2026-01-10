"""Meta-level MCP tool implementations (mode & graph lifecycle).

This module hosts core implementations for tools that manage the overall
graph lifecycle and mode switching, refactored out of
 :mod:`cedrus.tools.tools`.

The goal is to keep these concerns separate from editing/inspection/
validation logic, while preserving existing semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from cedrus.models.base import Mode
from cedrus.tools.runtime import tool_context
from cedrus.tools.tool_registry import TOOL_REGISTRY

if TYPE_CHECKING:
    from cedrus.server import AppContext


logger = get_logger("cedrus.tools.impl.meta")


async def update_tools_for_mode_core(
    *,
    ctx: Context[ServerSession, AppContext],
    old_mode: Mode,
    new_mode: Mode,
) -> None:
    """Update available tools when switching modes.

    This is a direct port of ``_update_tools_for_mode`` from
    :mod:`cedrus.tools.tools`, with the same algorithm and logging,
    but renamed and moved into the implementation layer.
    """

    # Import canonical tool order from the public tools facade
    from cedrus.tools import TOOL_ORDER

    mcp_server = ctx.fastmcp

    # Get tool name sets for each mode
    old_tools = TOOL_REGISTRY.get_tool_names_for_mode(old_mode)
    new_tools = TOOL_REGISTRY.get_tool_names_for_mode(new_mode)

    # Remove all old tools to rebuild list in canonical order
    for tool_name in old_tools:
        try:
            mcp_server.remove_tool(tool_name)
            logger.debug(
                "Removed tool '%s' when switching from '%s' to '%s'",
                tool_name,
                old_mode,
                new_mode,
            )
        except Exception as e:  # pragma: no cover - defensive logging
            logger.warning(f"Failed to remove tool '{tool_name}': {e}")

    # Add tools for new mode in canonical order
    for tool_name in TOOL_ORDER:
        if tool_name in new_tools:
            variant = TOOL_REGISTRY.get_variant_for_mode(tool_name, new_mode)
            if variant:
                try:
                    mcp_server.add_tool(
                        variant.fn,
                        name=variant.name,
                        description=variant.description,
                        **variant.metadata,
                    )
                    logger.debug(
                        "Added tool '%s' for mode '%s'",
                        tool_name,
                        new_mode,
                    )
                except Exception as e:  # pragma: no cover - defensive logging
                    logger.warning(f"Failed to add tool '{tool_name}': {e}")

    # Notify client of tool list changes
    try:
        await ctx.session.send_tool_list_changed()
        logger.debug("Sent tool_list_changed notification for mode switch to '%s'", new_mode)
    except Exception as e:  # pragma: no cover - defensive logging
        logger.warning(f"Failed to send tool_list_changed notification: {e}")


async def reset_graph_core(
    *,
    ctx: Context[ServerSession, AppContext],
    confirm: bool = False,
) -> CallToolResult:
    """Reset the entire reasoning graph to start fresh.

    This is a direct port of :func:`cedrus.tools.tools.reset_graph` with
    unchanged semantics, but delegates to :func:`update_tools_for_mode_core`
    for tool list updates.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        # Safety check
        if not confirm:
            node_count = len(arg_map.argument_graph.nodes)
            if node_count == 0:
                return tc.failure(
                    "Graph is already empty. Nothing to reset.",
                    error="EmptyGraph",
                ).build()

            tc.issue(
                "warning",
                f"⚠️  This will permanently delete {node_count} nodes and all relations.",
            )
            tc.issue(
                "info",
                "Call reset_graph(confirm=True) to proceed with reset.",
            )
            return tc.build()

        # Gather statistics before clearing
        claims = arg_map.list_claims()
        arguments = arg_map.list_arguments()
        edge_count = arg_map.argument_graph.number_of_edges()
        prop_count = arg_map.proposition_graph.number_of_nodes()

        # Perform reset
        arg_map.argument_graph.clear()
        arg_map.proposition_graph.clear()

        # Reset mode to sketch
        old_mode = ctx.request_context.lifespan_context.mode
        ctx.request_context.lifespan_context.mode = "sketch"

        # Update tools if mode changed
        if old_mode != "sketch":
            await update_tools_for_mode_core(ctx=ctx, old_mode=old_mode, new_mode="sketch")

        # Build response
        tc.success(
            f"✓ Reset complete: Cleared {len(claims)} claims, "
            f"{len(arguments)} arguments, {edge_count} relations, "
            f"and {prop_count} propositions."
        )
        tc.issue("info", "Mode reset to `sketch`.")
        tc.suggest(
            "get_instructions",
            {},
            "Get guidance for starting your new deliberation.",
            action_type="help",
        )

        return tc.build()


async def switch_mode_core(
    *,
    ctx: Context[ServerSession, AppContext],
    new_mode: Mode,
) -> CallToolResult:
    """Switch the argument map editing mode.

    Direct port of :func:`cedrus.tools.tools.switch_mode`, delegating
    to :func:`update_tools_for_mode_core` for tool list updates.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    old_mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, new_mode) as tc:
        if new_mode not in ["sketch", "elaborate", "review"]:
            return tc.failure(
                f"Invalid mode `{new_mode}`. Valid modes are `sketch`, `elaborate`, and `review`.",
                error="InvalidMode",
            ).build()

        # Update mode first
        ctx.request_context.lifespan_context.mode = new_mode

        # Perform dynamic tool swapping if mode actually changed
        if old_mode != new_mode:
            try:
                await update_tools_for_mode_core(ctx=ctx, old_mode=old_mode, new_mode=new_mode)
            except Exception as e:  # pragma: no cover - defensive logging
                logger.error(f"Error updating tools for mode switch: {str(e)}")
                tc.issue("warning", f"Tool list may not be fully updated: {str(e)}")

        tc.success(f"✓ Switched mode from '{old_mode}' to '{new_mode}'.")
        tc.suggest(
            "get_instructions",
            {},
            f"Run 'get_instructions' to get important guidance and hints for '{new_mode}' mode.",
            action_type="help",
        )
        return tc.build()


__all__ = [
    "update_tools_for_mode_core",
    "reset_graph_core",
    "switch_mode_core",
]
