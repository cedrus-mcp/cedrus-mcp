"""Sketch-mode MCP tool entrypoints.

These functions are the MCP-visible tools when the server is in
``sketch`` mode. They provide simplified signatures appropriate for
rapid prototyping and delegate to shared ``*_core`` implementations
in :mod:`cedrus.tools.impl`.
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from cedrus.backend.models import NodeLabel
from cedrus.backend.models.base import Format, Mode
from cedrus.backend.models.relations import DialecticalRelationType
from cedrus.tools.impl import editing, guidance, inspection, meta
from cedrus.tools.tool_registry import TOOL_REGISTRY, ToolVariant

if TYPE_CHECKING:
    from cedrus.server import AppContext
else:
    AppContext = Any


# Public MCP tools – names match external tool names


async def add_claim(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
) -> CallToolResult:
    """Add a new claim (sketch mode – no tags)."""

    return await editing.add_claim_core(
        label=label,
        ctx=ctx,
        proposition=proposition,
        tags=None,
    )


async def add_argument(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
) -> CallToolResult:
    """Add a new argument (sketch mode – gist only)."""

    return await editing.add_argument_core(
        label=label,
        ctx=ctx,
        gist=gist,
        premises=None,
        conclusion=None,
        tags=None,
    )


async def connect(
    *,
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
) -> CallToolResult:
    """Create a relation (sketch mode – no grounding)."""

    return await editing.connect_core(
        source=source,
        target=target,
        ctx=ctx,
        relation_type=relation_type,
        target_premise_idx=None,
        grounding_strategy=None,
    )


async def remove(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel | None = None,
    source: NodeLabel | None = None,
    target: NodeLabel | None = None,
) -> CallToolResult:
    """Remove a node or relation (sketch & elaborate semantics are shared)."""

    return editing.remove_core(ctx=ctx, label=label, source=source, target=target)


async def inspect_graph(
    *,
    ctx: Context[ServerSession, AppContext],
    verbose: bool = False,
    format: Format = "argdown",
) -> CallToolResult:
    return await inspection.inspect_graph_core(ctx=ctx, verbose=verbose, format=format)


async def inspect_neighborhood(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
    k: int = 2,
    format: Format = "argdown",
) -> CallToolResult:
    return await inspection.inspect_neighborhood_core(
        ctx=ctx,
        label=label,
        k=k,
        format=format,
    )


async def get_instructions(
    *,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Show instructions and usage hints for sketch mode."""

    return await guidance.get_instructions_core(ctx=ctx, topic=None, mode="sketch")


async def switch_mode(
    *,
    mode: Mode,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    return await meta.switch_mode_core(ctx=ctx, new_mode=mode)


async def reset_graph(
    *,
    ctx: Context[ServerSession, AppContext],
    confirm: bool = False,
) -> CallToolResult:
    return await meta.reset_graph_core(ctx=ctx, confirm=confirm)


def register_sketch_tools() -> None:
    """Register sketch-mode tool variants in TOOL_REGISTRY."""

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=add_claim,
            name="add_claim",
            internal_name="add_claim__sketch",
            modes=["sketch"],
            description=dedent(
                """Add a new claim node to your argumentation graph.

                A claim represents a single proposition. By adding a claim, you're not ascertaining its
                truth, but rather introducing it as a point for discussion within your argument map.
                Try to keep claims clear, unambiguous, and focused on a single idea. Provide a succinct
                and informative label that captures the essence of the claim and helps you to refer to
                it easily later on.

                Args:
                    label: Succinct and informative title for the claim (serving as unique identifier).
                    proposition: The content of the claim (what is being asserted).
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=add_argument,
            name="add_argument",
            internal_name="add_argument__sketch",
            modes=["sketch"],
            description=dedent(
                """Add a new argument node to your argumentation graph.

                An argument represents a justification or an objection. Provide a 'gist' to summarize the
                key idea of the argument. Be clear and concise in your descriptions. Provide a succinct and
                informative label that captures the essence of the argument and helps you to refer to it
                easily later on.

                By adding an argument, you're not necessarily asserting it.

                Args:
                    label: Succinct and informative title for the argument (serving as unique identifier).
                    gist: A brief summary of the argument's key idea.
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=connect,
            name="connect",
            internal_name="connect__sketch",
            modes=["sketch"],
            description=dedent(
                """Connect two nodes in your argumentation graph.

                Args:
                    source: Label of the source node (argument or claim).
                    target: Label of the target node (argument or claim).
                    relation_type: Type of relation ("supports" or "attacks").
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=remove,
            name="remove",
            internal_name="remove__sketch",
            modes=["sketch"],
            description=dedent(
                """Remove an existing node or relation from the argument map.

                Provide either `label` (to remove a node) OR `source` and `target` (to remove a relation),
                but not all.

                Args:
                    label: Label of the node to remove (for node removal).
                    source: Source node label of the relation to remove (for relation removal).
                    target: Target node label of the relation to remove (for relation removal).
                """
            ),
        )
    )

    # Shared tools that are available across modes but whose implementations
    # are identical in all modes.
    for fn, name, description in [
        (inspect_graph, "inspect_graph", "Show an overview of the argumentation graph"),
        (
            inspect_neighborhood,
            "inspect_neighborhood",
            "Show k-neighborhood of a node",
        ),
        (switch_mode, "switch_mode", "Switch the argument map editing mode"),
        (reset_graph, "reset_graph", "Reset the entire argument map to start fresh"),
        (
            get_instructions,
            "get_instructions",
            "Show instructions and usage hints for current mode",
        ),
    ]:
        TOOL_REGISTRY.register_variant(
            ToolVariant(
                fn=fn,  # type: ignore[arg-type]
                name=name,
                internal_name=f"{name}__sketch",
                modes=["sketch"],
                description=description,
            )
        )


__all__ = [
    "add_claim",
    "add_argument",
    "connect",
    "remove",
    "inspect_graph",
    "inspect_neighborhood",
    "get_instructions",
    "switch_mode",
    "reset_graph",
    "register_sketch_tools",
]
