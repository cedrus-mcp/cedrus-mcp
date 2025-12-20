"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from koala.graph.argument_map import ArgumentMap
from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.base import Mode
from koala.server import AppContext, mcp
from koala.tools import relation_authoring, suggestions, utils
from koala.tools import node_creation, node_updates, node_deletion
from koala.tools.tool_args import parse_tool_args
from koala.tools.tool_context import ToolContext, tool_context

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


@mcp.tool()
def add(label: NodeLabel, ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Create a new node in the argument map.

    Example usage:

        add(label="CLAIM_1", proposition="This is a new claim.")
    """


    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")
        
        # Ensure label is unique
        label = utils.ensure_label_is_unique(label, arg_map, tc)

        # Handle MCP Inspector format where kwargs might be nested
        if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
            kwargs = kwargs["kwargs"]

        args = parse_tool_args("add", tc, arg_map, **kwargs)

        try:
            if args.node_type == "claim":
                # Adding a claim node
                node_creation.new_claim(
                    label=label,
                    proposition=args.proposition,
                    to_label=args.to_label,
                    from_label=args.from_label,
                    relation_type=args.relation_type or "support",
                    target_premise_idx=args.target_premise_idx,
                    tags=args.tags,
                    metadata=args.metadata,
                    arg_map=arg_map,
                    tc=tc,
                )
            elif args.node_type == "argument":
                # Adding an argument node
                node_creation.new_argument(
                    label=label,
                    gist=args.gist,
                    to_label=args.to_label,
                    from_label=args.from_label,
                    relation_type=args.relation_type or "support",
                    target_premise_idx=args.target_premise_idx,
                    premises=args.premises,
                    conclusion=args.conclusion,
                    tags=args.tags,
                    metadata=args.metadata,
                    arg_map=arg_map,
                    tc=tc,
                )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create {args.node_type} `{label}`: {str(e)}", error=str(e)
            ).build()

        suggestions.add_suggestions_after_adding_node(label, arg_map, tc)

        return tc.build()
    

@mcp.tool()
def edit(label: NodeLabel, ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Edit an existing node in the argument map.

    Example usage:

        edit(label="CLAIM_1", proposition="This is the updated claim content.")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        node = arg_map.get_node(label)
        if node is None:
            return tc.failure(
                f"Node '{label}' does not exist.",
                error="NonExistentNode",
            ).build()

        # Handle MCP Inspector format where kwargs might be nested
        if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
            kwargs = kwargs["kwargs"]

        node_type = "claim" if isinstance(node, ClaimNode) else "argument"
        args = parse_tool_args("edit", tc, arg_map, node_type=node_type, **kwargs)

        try:
            match args.field:
                case "tags":
                    return node_updates.update_tags(
                        label=label,
                        old_value=args.old_value,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )
                case "metadata":
                    return node_updates.update_metadata(
                        label=label,
                        key=args.key,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )

            if isinstance(node, ClaimNode):
                match args.field:
                    case "label" | "proposition":
                        return node_updates.update_claim(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
            elif isinstance(node, ArgumentNode):
                match args.field:
                    case "label" | "gist" | "conclusion":
                        return node_updates.update_argument(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "premises":
                        return node_updates.update_premises(
                            label=label,
                            premise_idx=args.premise_idx,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to edit node `{label}`: {str(e)}", error=str(e)
            ).build()
        
        return tc.failure(
            f"✗ Failed to edit field '{args.field}' of {args.node_type} node `{label}`."
        ).build()


@mcp.tool()
def connect(from_label: str, to_label: str, ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Create a new dialectical relation between two existing nodes.

    Example usage:

        connect(
            from_label="ARGUMENT_1",
            to_label="CLAIM_1",
            relation_type="support"
        )
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        # Handle MCP Inspector format where kwargs might be nested
        if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
            kwargs = kwargs["kwargs"]

        if mode == "sketch":
            if kwargs.get("grounding_strategy") is not None:
                tc.note(
                    "Ignoring grounding strategies in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to use grounding strategies."
                )
                kwargs["grounding_strategy"] = None
            if kwargs.get("target_premise_idx") is not None:
                tc.note(
                    "Ignoring target_premise_idx in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to specify target premise index."
                )
                kwargs["target_premise_idx"] = None
        elif mode == "review":
            tc.note(
                "Creating new relations in 'review' mode. Consider switching mode."
            ).suggest(
                "mode", {"mode": "author"}, "Switch to 'author' mode to create new relations."
            )

        args = parse_tool_args("connect", tc, arg_map, from_label=from_label, to_label=to_label, **kwargs)

        try:
            if not arg_map.get_dialectic_relation(args.from_label, args.to_label):
                match args.relation_type:
                    case "support":
                        return relation_authoring.new_support_relation(
                            from_label=args.from_label,
                            to_label=args.to_label,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "attack":
                        return relation_authoring.new_attack_relation(
                            from_label=args.from_label,
                            to_label=args.to_label,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case _:
                        return tc.failure(
                            f"Invalid relation_type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
            elif mode != "author":
                return tc.failure(
                    f"Cannot ground existing relation from `{args.from_label}` to `{args.to_label}` in '{mode}' mode.",
                    error="RelationAlreadyExists",
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to ground existing relations."
                ).build()
            else:
                match args.relation_type:
                    case "support":
                        for grounding_strategy in ["define_equivalence", "copy_conclusion", "copy_premise"]:
                            try:
                                return relation_authoring.ground_support_relation(
                                    from_label=args.from_label,
                                    to_label=args.to_label,
                                    strategy=grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.note(f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
                        return tc.failure(
                            f"✗ Failed to ground support relation from `{args.from_label}` to `{args.to_label}`.",
                            error="GroundingFailed",
                        ).build()                    
                    case "attack":
                        for grounding_strategy in ["define_negation", "negate_conclusion", "negate_premise"]:
                            try:
                                return relation_authoring.ground_attack_relation(
                                    from_label=args.from_label,
                                    to_label=args.to_label,
                                    strategy=grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.note(f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
                        return tc.failure(
                            f"✗ Failed to ground attack relation from `{args.from_label}` to `{args.to_label}`.",
                            error="GroundingFailed",
                        ).build()
                    case _:
                        return tc.failure(
                            f"Invalid relation_type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create {args.relation_type} relation from `{args.from_label}` to `{args.to_label}`: {str(e)}", error=str(e)
            ).build()
        
        raise RuntimeError(f"Internal Error: Unhandled case when creating relation from `{args.from_label}` to `{args.to_label}`.")


@mcp.tool()
def remove(ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Remove an existing node or relation from the argument map.

    Example usage:

        remove(label="CLAIM_1")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        # Handle MCP Inspector format where kwargs might be nested
        if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
            kwargs = kwargs["kwargs"]

        # validate kwargs
        label = kwargs.get("label")
        to_label = kwargs.get("to_label")
        from_label = kwargs.get("from_label")
        if label and label.strip():
            if to_label is not None:
                tc.note("Ignoring to_label when removing a node.", priority=.2)
            if from_label is not None:
                tc.note("Ignoring from_label when removing a node.", priority=.2)
        elif to_label and to_label.strip() and from_label and from_label.strip():
            if label is not None:
                tc.note("Ignoring label when removing a relation.", priority=.2)
        else:
            return tc.issue(
                "error",
                "To remove a node, provide a non-empty 'label'. To remove a relation, provide non-empty 'from_label' and 'to_label'.",
            ).suggest(
                "remove",
                {
                    "label": "NODE_LABEL",
                },
                "Remove a node by specifying its label.",
            ).suggest(
                "remove",
                {
                    "from_label": "SOURCE_NODE_LABEL",
                    "to_label": "TARGET_NODE_LABEL",
                },
                "Remove a relation by specifying source and target node labels.",
            ).build()

        if label:
            node = arg_map.get_node(label)
            if node is None:
                return tc.failure(
                    f"Node '{label}' does not exist.",
                    error="NonExistentNode",
                ).build()

            if isinstance(node, ClaimNode):
                return node_deletion.delete_claim(
                    label=label,
                    arg_map=arg_map,
                    tc=tc,
                )
            else:
                return node_deletion.delete_argument(
                    label=label,
                    arg_map=arg_map,
                    tc=tc,
                )
        elif to_label and from_label:
            return relation_authoring.delete_relation(
                from_label=from_label,
                to_label=to_label,
                arg_map=arg_map,
                tc=tc,
            )

        raise ValueError("Internal Error: Unhandled case in remove tool.")

@mcp.tool()
def mode(
    mode: Mode,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Switch the argument map editing mode.

    Example usage:

        mode("author")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    old_mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if mode not in ["sketch", "author", "review"]:
            return tc.failure(
                f"Invalid mode '{mode}'. Valid modes are 'sketch', 'author', and 'review'.",
                error="InvalidMode",
            ).build()

        ctx.request_context.lifespan_context.mode = mode
        tc.success(f"✓ Switched mode from '{old_mode}' to '{mode}'.")
        return tc.build()