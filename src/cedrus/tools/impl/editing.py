"""Editing-related MCP tool implementations.

This module hosts the core implementations for graph editing tools,
refactored out of :mod:`cedrus.tools.tools`.

The functions here intentionally mirror the behavior of the legacy
``_add_claim_impl``, ``_add_argument_impl``, ``_connect_impl``,
``edit`` and ``remove`` functions. The goal for this first step is a
mechanical move with no semantic changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult
from pydantic import AnyUrl

from cedrus.models import ArgumentNode, ClaimNode, NodeLabel
from cedrus.models.relations import DialecticalRelationType, GroundingStrategy
from cedrus.tools.backend import nodes, relations
from cedrus.tools.runtime import (
    suggestions,
    tool_args,
    tool_context,
)

if TYPE_CHECKING:
    from cedrus.server import AppContext

logger = get_logger("cedrus.tools.impl.editing")


async def add_claim_core(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Core implementation for adding a claim.

    This is a direct port of ``_add_claim_impl`` from
    :mod:`cedrus.tools.tools` with the same behavior.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")

        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            import cedrus.resources

            argdown = await cedrus.resources.graph_views.graph_thin_resource()
            tc.embed_resource(AnyUrl("argmap://graph/thin/argdown"), argdown, 0.9)
            params: dict[str, Any] = {"label": f"Revised-{label}"}
            if proposition:
                params["proposition"] = proposition
            tc.suggest(
                "add_claim",
                params,
                "Make sure this claim is distinct from the existing one, and add the claim again with a new unique label.",
                action_type="expand",
            )

        try:
            nodes.new_claim(
                label=label,
                proposition=proposition,
                to_label=None,
                from_label=None,
                relation_type="support",
                target_premise_idx=None,
                tags=tags,
                metadata=None,
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error creating claim `{label}`: {str(e)}")
            return tc.failure(f"✗ Failed to create claim `{label}`: {str(e)}", error=str(e)).build()

        try:
            suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error adding suggestions after creating claim `{label}`: {str(e)}")

        return tc.build()


async def add_argument_core(
    *,
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Core implementation for adding an argument.

    Direct port of ``_add_argument_impl`` from :mod:`cedrus.tools.tools`.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")

        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            import cedrus.resources

            argdown = await cedrus.resources.graph_views.graph_thin_resource()
            tc.embed_resource(AnyUrl("argmap://graph/thin/argdown"), argdown, 0.9)
            params: dict[str, Any] = {"label": f"Revised-{label}"}
            if gist:
                params["gist"] = gist
            tc.suggest(
                "add_argument",
                params,
                "Make sure this argument is distinct from the existing one, and add the argument again with a new unique label.",
                action_type="expand",
            )
            return tc.build()

        try:
            nodes.new_argument(
                label=label,
                gist=gist,
                premises=premises,
                conclusion=conclusion,
                to_label=None,
                from_label=None,
                relation_type="support",
                target_premise_idx=None,
                tags=tags,
                metadata=None,
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                "Error creating argument `%s` (gist=%s, premises=%s, conclusion=%s): %s",
                label,
                gist,
                premises,
                conclusion,
                str(e),
            )
            return tc.failure(
                f"✗ Failed to create argument `{label}`: {str(e)}", error=str(e)
            ).build()

        try:
            suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error adding suggestions after creating argument `{label}`: {str(e)}")

        return tc.build()


async def connect_core(
    *,
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    grounding_strategy: GroundingStrategy | None = None,
) -> CallToolResult:
    """Core implementation for creating dialectical relations.

    Direct port of ``_connect_impl`` from :mod:`cedrus.tools.tools`.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if mode == "sketch":
            if grounding_strategy is not None:
                tc.issue(
                    "warning",
                    "Ignoring grounding strategies in `sketch` mode.",
                    priority=0.2,
                ).suggest(
                    "switch_mode",
                    {"mode": "elaborate"},
                    "Switch to `elaborate` mode to use grounding strategies.",
                )
                grounding_strategy = None
            if target_premise_idx is not None:
                tc.issue(
                    "warning",
                    "Ignoring target_premise_idx in `sketch` mode.",
                    priority=0.2,
                ).suggest(
                    "switch_mode",
                    {"mode": "elaborate"},
                    "Switch to `elaborate` mode to specify target premise index.",
                )
                target_premise_idx = None
        elif mode == "review":
            tc.issue(
                "info",
                "Creating new relations in `review` mode. Consider switching mode.",
            ).suggest(
                "switch_mode",
                {"mode": "elaborate"},
                "Switch to `elaborate` mode to create new relations.",
            ).suggest(
                "validate",
                {},
                "Run validation to check the argument map.",
            )

        args = tool_args.parse_tool_args(
            "connect",
            tc,
            arg_map,
            source=source,
            target=target,
            relation_type=relation_type,
            target_premise_idx=target_premise_idx,
            grounding_strategy=grounding_strategy,
        )

        try:
            if not arg_map.get_dialectic_relation(args.source, args.target):
                match args.relation_type:
                    case "support":
                        return relations.new_support_relation(
                            from_label=args.source,
                            to_label=args.target,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore[arg-type]
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "attack":
                        return relations.new_attack_relation(
                            from_label=args.source,
                            to_label=args.target,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore[arg-type]
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case _:
                        return tc.failure(
                            f"Invalid relation type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
            elif mode != "elaborate":
                return (
                    tc.failure(
                        f"Cannot ground existing relation from `{args.source}` to `{args.target}` in '{mode}' mode.",
                        error="RelationAlreadyExists",
                    )
                    .suggest(
                        "switch_mode",
                        {"mode": "elaborate"},
                        "Switch to `elaborate` mode to ground existing relations.",
                    )
                    .build()
                )
            else:
                match args.relation_type:
                    case "support":
                        for try_grounding_strategy in [
                            "define_equivalence",
                            "copy_conclusion",
                            "copy_premise",
                        ]:
                            try:
                                return relations.ground_support_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore[arg-type]
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception:  # pragma: no cover - best-effort fallthrough
                                pass
                        return tc.failure(
                            f"✗ Failed to ground support relation from `{args.source}` to `{args.target}`.",
                            error="GroundingFailed",
                        ).build()
                    case "attack":
                        for try_grounding_strategy in [
                            "define_negation",
                            "negate_conclusion",
                            "negate_premise",
                        ]:
                            try:
                                return relations.ground_attack_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore[arg-type]
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception:  # pragma: no cover - best-effort fallthrough
                                pass
                        return tc.failure(
                            f"✗ Failed to ground attack relation from `{args.source}` to `{args.target}`.",
                            error="GroundingFailed",
                        ).build()
                    case _:
                        return tc.failure(
                            f"Invalid relation type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                "Error creating %s relation from `%s` to `%s`: %s",
                args.relation_type,
                args.source,
                args.target,
                str(e),
            )
            return tc.failure(
                f"✗ Failed to create {args.relation_type} relation from `{args.source}` to `{args.target}`: {str(e)}",
                error=str(e),
            ).build()


def edit_core(
    *,
    label: NodeLabel,
    field: Literal[
        "label",
        "proposition",
        "gist",
        "conclusion",
        "premises",
        "tags",
        "metadata",
    ],
    ctx: Context[ServerSession, AppContext],
    edit_options: dict[str, Any] | None = None,
) -> CallToolResult:
    """Core implementation for editing nodes.

    Direct port of :func:`cedrus.tools.tools.edit`.
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

        node = arg_map.get_node(label)

        kwargs = dict(edit_options or {})
        kwargs["field"] = field

        node_type = "claim" if isinstance(node, ClaimNode) else "argument"
        args = tool_args.parse_tool_args("edit", tc, arg_map, node_type=node_type, **kwargs)

        try:
            match args.field:
                case "tags":
                    return nodes.update_tags(
                        label=label,
                        old_value=args.old_value,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )
                case "metadata":
                    return nodes.update_metadata(
                        label=label,
                        key=args.key,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )

            if isinstance(node, ClaimNode):
                match args.field:
                    case "label" | "proposition":
                        return nodes.update_claim(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
            elif isinstance(node, ArgumentNode):
                match args.field:
                    case "label" | "gist" | "conclusion":
                        return nodes.update_argument(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "premises":
                        return nodes.update_premises(
                            label=label,
                            old_value=args.old_value,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                "Error editing field '%s' of %s node `%s`: %s",
                args.field,
                args.node_type,
                label,
                str(e),
            )
            return tc.failure(f"✗ Failed to edit node `{label}`: {str(e)}", error=str(e)).build()

        logger.error(
            "Unhandled case when editing field '%s' of %s node `%s`.",
            args.field,
            args.node_type,
            label,
        )
        return tc.failure(
            f"✗ Failed to edit field '{args.field}' of {args.node_type} node `{label}`."
        ).build()


def remove_core(
    *,
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel | None = None,
    source: NodeLabel | None = None,
    target: NodeLabel | None = None,
) -> CallToolResult:
    """Core implementation for removing nodes or relations.

    Direct port of :func:`cedrus.tools.tools.remove`.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        # Validate mutually exclusive parameters
        if label and label.strip() and (source or target):
            return (
                tc.failure(
                    "Provide either 'label' (to remove a node) OR 'source' and 'target' (to remove a relation), but not all.",
                    error="InvalidParameters",
                )
                .suggest(
                    "remove",
                    {
                        "label": label,
                    },
                    f"Remove the node `{label}` by specifying its label.",
                )
                .build()
            )

        try:
            # Validate that we have exactly one operation
            if label and label.strip():
                # Node removal - label is valid
                pass
            elif source and source.strip() and target and target.strip():
                # Relation removal - both source and target are valid
                pass
            else:
                return (
                    tc.issue(
                        "error",
                        "To remove a node, provide a non-empty 'label'. To remove a relation, provide non-empty 'source' and 'target'.",
                    )
                    .suggest(
                        "remove",
                        {
                            "label": "NODE_LABEL",
                        },
                        "Remove a node by specifying its label.",
                    )
                    .suggest(
                        "remove",
                        {
                            "source": "SOURCE_NODE_LABEL",
                            "target": "TARGET_NODE_LABEL",
                        },
                        "Remove a relation by specifying source and target node labels in relation dict.",
                    )
                    .build()
                )

            if label:
                if not arg_map.is_node(label):
                    most_similar_label, _ = next(arg_map.most_similar_labels(label), (None, 0))
                    msg = f"Node '{label}' does not exist."
                    if most_similar_label:
                        msg += f" Did you mean '{most_similar_label}'?"
                    return tc.failure(msg, error="NonExistentNode").build()

                node = arg_map.get_node(label)

                if isinstance(node, ClaimNode):
                    return nodes.delete_claim(
                        label=label,
                        arg_map=arg_map,
                        tc=tc,
                    )
                else:
                    return nodes.delete_argument(
                        label=label,
                        arg_map=arg_map,
                        tc=tc,
                    )
            elif source and target:
                return relations.delete_relation(
                    from_label=source,
                    to_label=target,
                    arg_map=arg_map,
                    tc=tc,
                )
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error removing node/relation: {str(e)}")
            return tc.failure(f"✗ Failed to remove node/relation: {str(e)}", error=str(e)).build()

        logger.error("Unhandled case in remove tool.")
        raise ValueError("Internal Error: Unhandled case in remove tool.")


__all__ = [
    "add_claim_core",
    "add_argument_core",
    "connect_core",
    "edit_core",
    "remove_core",
]
