"""Elaborate-mode MCP tool entrypoints.

These functions are the MCP-visible tools when the server is in
``elaborate`` mode. They expose the full, detailed signatures for
advanced argumentation work and delegate to shared ``*_core``
implementations in :mod:`cedrus.tools.impl`.
"""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any, Literal

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from cedrus.backend.models import NodeLabel
from cedrus.backend.models.base import Mode
from cedrus.backend.models.relations import DialecticalRelationType, GroundingStrategy
from cedrus.tools.impl import editing, guidance, inspection, meta, validation
from cedrus.tools.tool_registry import TOOL_REGISTRY, ToolVariant

if TYPE_CHECKING:
    from cedrus.server import AppContext
else:
    AppContext = Any


async def add_claim(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new claim (elaborate mode – with tags)."""

    return await editing.add_claim_core(
        label=label,
        ctx=ctx,
        proposition=proposition,
        tags=tags,
    )


async def add_argument(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new argument (elaborate mode – full structure)."""

    return await editing.add_argument_core(
        label=label,
        ctx=ctx,
        gist=gist,
        premises=premises,
        conclusion=conclusion,
        tags=tags,
    )


async def connect(
    *,
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    grounding_strategy: GroundingStrategy | None = None,
) -> CallToolResult:
    """Create or ground a relation (elaborate mode – with grounding)."""

    return await editing.connect_core(
        source=source,
        target=target,
        ctx=ctx,
        relation_type=relation_type,
        target_premise_idx=target_premise_idx,
        grounding_strategy=grounding_strategy,
    )


def edit(
    *,
    label: NodeLabel,
    field: Literal["label", "proposition", "gist", "conclusion", "premises", "tags", "metadata"],
    ctx: Context[ServerSession, AppContext],
    edit_options: dict[str, Any] | None = None,
) -> CallToolResult:
    """Edit an existing node (elaborate mode only)."""

    return editing.edit_core(label=label, field=field, ctx=ctx, edit_options=edit_options)


def remove(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel | None = None,
    source: NodeLabel | None = None,
    target: NodeLabel | None = None,
) -> CallToolResult:
    """Remove a node or relation (shared semantics)."""

    return editing.remove_core(ctx=ctx, label=label, source=source, target=target)


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
    topic: Literal["grounding", "validity", "none"] | None = None,
) -> CallToolResult:
    """Show general or topic-specific instructions for elaborate mode."""

    return await guidance.get_instructions_core(ctx=ctx, topic=topic, mode="elaborate")


async def validate(
    *,
    ctx: Context[ServerSession, AppContext],
    fix: bool = False,
    max_issues: int | None = None,
) -> CallToolResult:
    """Validate the current argument map (elaborate mode convenience)."""

    return validation.validate_core(ctx=ctx, fix=fix, max_issues=max_issues)


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


def register_elaborate_tools() -> None:
    """Register elaborate-mode tool variants in TOOL_REGISTRY."""

    # Creation tools
    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=add_claim,
            name="add_claim",
            internal_name="add_claim__elaborate",
            modes=["elaborate"],
            description=dedent(
                """Add a new claim node to your argumentation graph.

                A claim represents a single proposition. Claims are useful for highlighting
                shared premises among multiple arguments.

                Args:
                    label: Succinct and informative title for the claim (serving as unique identifier).
                    proposition: The content of the claim (what is being asserted).
                    tags: Optional list of tags for the claim (e.g., "important", "to-review").
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=add_argument,
            name="add_argument",
            internal_name="add_argument__elaborate",
            modes=["elaborate"],
            description=dedent(
                """Add a new argument node to your argumentation graph.

                An argument consists of a set of premises that jointly support the conclusion.

                Args:
                    label: Succinct and informative title for the argument (serving as unique identifier).
                    gist: A brief summary of the argument's key idea.
                    conclusion: The main claim that the argument is supporting or attacking.
                    premises: List of premises supporting the conclusion.
                    tags: Optional list of tags for the argument (e.g., "needs-backup", "to-review").
                """
            ),
        )
    )

    # Connection tools
    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=connect,
            name="connect",
            internal_name="connect__elaborate",
            modes=["elaborate"],
            description=dedent(
                """Connect two nodes in your argumentation graph and optionally ground the dialectical relation.

                A dialectical relation (support or attack) is grounded in case it reflects the actual
                structure of the adjacent nodes.

                Args:
                    source: Label of the source node (argument or claim).
                    target: Label of the target node (argument or claim).
                    relation_type: Type of relation ("supports" or "attacks").
                    target_premise_idx: (For arguments as targets) Index of the premise being supported/attacked.
                    grounding_strategy: Strategy for grounding the relation.
                """
            ),
        )
    )

    # Editing tools
    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=edit,
            name="edit",
            internal_name="edit__elaborate",
            modes=["elaborate"],
            description=dedent(
                """Edit an existing node in the argument map.

                Args:
                    label: Node identifier to edit.
                    field: Field to edit (label, proposition, gist, conclusion, premises, tags, metadata).
                    edit_options: Field-specific configuration (e.g. new_value, old_value, key).
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=remove,
            name="remove",
            internal_name="remove__elaborate",
            modes=["elaborate"],
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

    # Inspection and meta tools specific to elaborate mode
    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=inspect_node,
            name="inspect_node",
            internal_name="inspect_node__elaborate",
            modes=["elaborate"],
            description="Show detailed information about a specific node in the argument map.",
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=get_instructions,
            name="get_instructions",
            internal_name="get_instructions__elaborate",
            modes=["elaborate"],
            description=dedent(
                """Show general advice or detailed topic-specific instructions for how to elaborate an argumentation graph.

                Available topics are:
                    - "grounding": Instructions on how to properly ground dialectical relations.
                    - "validity": Instructions on how to ensure argument validity and soundness.
                """
            ),
        )
    )

    TOOL_REGISTRY.register_variant(
        ToolVariant(
            fn=validate,
            name="validate",
            internal_name="validate__elaborate",
            modes=["elaborate"],
            description="Validate the current argument map for consistency and completeness.",
        )
    )

    for fn, name, description in [
        (inspect_graph, "inspect_graph", "Show an overview of the argumentation graph"),
        (inspect_neighborhood, "inspect_neighborhood", "Show k-neighborhood of a node"),
        (switch_mode, "switch_mode", "Switch the argument map editing mode"),
        (reset_graph, "reset_graph", "Reset the entire argument map to start fresh"),
    ]:
        TOOL_REGISTRY.register_variant(
            ToolVariant(
                fn=fn,  # type: ignore[arg-type]
                name=name,
                internal_name=f"{name}__elaborate",
                modes=["elaborate"],
                description=description,
            )
        )


__all__ = [
    "add_claim",
    "add_argument",
    "connect",
    "edit",
    "remove",
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    "get_instructions",
    "validate",
    "switch_mode",
    "reset_graph",
    "register_elaborate_tools",
]
