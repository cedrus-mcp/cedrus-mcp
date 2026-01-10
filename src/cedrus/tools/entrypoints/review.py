"""Review-mode MCP tool entrypoints.

These functions are the MCP-visible tools when the server is in
``review`` mode. Review mode focuses on validation and inspection,
with limited editing capabilities.
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from cedrus.models import NodeLabel
from cedrus.models.base import Mode
from cedrus.tools.impl import inspection, guidance, validation, meta
from typing import Callable
from cedrus.tools.tool_registry import TOOL_REGISTRY, ToolVariant

if TYPE_CHECKING:
    from cedrus.server import AppContext
else:
    AppContext = Any


async def validate(
    *,
    ctx: Context[ServerSession, AppContext],
    fix: bool = False,
    max_issues: int | None = None,
) -> CallToolResult:
    """Validate the current argument map."""

    return validation.validate_core(ctx=ctx, fix=fix, max_issues=max_issues)


async def inspect_graph(
    *,
    ctx: Context[ServerSession, AppContext],
    verbose: bool = False,
    format: str = "argdown",
) -> CallToolResult:
    return await inspection.inspect_graph_core(ctx=ctx, verbose=verbose, format=format)  # type: ignore[arg-type]


async def inspect_neighborhood(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
    k: int = 2,
) -> CallToolResult:
    return await inspection.inspect_neighborhood_core(ctx=ctx, label=label, k=k)


async def inspect_node(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
) -> CallToolResult:
    return await inspection.inspect_node_core(ctx=ctx, label=label)


async def get_instructions(
    *,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Show instructions and usage hints for review mode."""

    return await guidance.get_instructions_core(ctx=ctx, topic=None, mode="review")


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


def register_review_tools() -> None:
    """Register review-mode tool variants in TOOL_REGISTRY."""

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=validate,
            name="validate",
            internal_name="validate__review",
            modes=["review"],
            description="Validate the current argument map for consistency and completeness.",
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=inspect_node,
            name="inspect_node",
            internal_name="inspect_node__review",
            modes=["review"],
            description="Show detailed information about a specific node in the argument map.",
        )
    )

    for fn, name, description in [
        (inspect_graph, "inspect_graph", "Show an overview of the argumentation graph"),
        (inspect_neighborhood, "inspect_neighborhood", "Show k-neighborhood of a node"),
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
                internal_name=f"{name}__review",
                modes=["review"],
                description=description,
            )
        )


__all__ = [
    "validate",
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    "get_instructions",
    "switch_mode",
    "reset_graph",
    "register_review_tools",
]
