"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

import base64
from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult, ImageContent

from koala.graph.svg_export import export_svg
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
from koala.tools.tool_context import tool_context

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


@mcp.tool()
def add(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    node_options: dict[str, Any] | None = None,
    relation_options: dict[str, Any] | None = None,
) -> CallToolResult:
    """Create a new node in the argument map.

    Args:
        label: Unique identifier for the node
        node_options: Node configuration (proposition, gist, conclusion, premises, node_type, tags, metadata)
        relation_options: Optional relation to create (to_label, from_label, relation_type, target_premise_idx)

    Example usage:

        add(
            label="CLAIM_1",
            node_options={"proposition": "This is a new claim."},
            relation_options={"from_label": "ARG_1", "relation_type": "support"}
        )
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")
        
        # Ensure label is unique
        label = utils.ensure_label_is_unique(label, arg_map, tc)

        # Merge node_options and relation_options
        kwargs = {}
        if node_options:
            kwargs.update(node_options)
        if relation_options:
            kwargs.update(relation_options)

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
def edit(
    label: NodeLabel,
    field: str,
    ctx: Context[ServerSession, AppContext],
    edit_options: dict[str, Any] | None = None,
) -> CallToolResult:
    """Edit an existing node in the argument map.

    Args:
        label: Node identifier to edit
        field: Field to edit (label, proposition, gist, conclusion, premises, tags, metadata)
        edit_options: Field-specific configuration:
            - For label/proposition/gist/conclusion: new_value
            - For premises: new_value, premise_idx
            - For tags: new_value (to add), old_value (to remove), or both
            - For metadata: key, new_value

    Example usage:

        edit(
            label="CLAIM_1",
            field="proposition",
            edit_options={"new_value": "This is the updated claim content."}
        )
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

        kwargs = edit_options or {}
        kwargs["field"] = field
        
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
def connect(
    from_label: str,
    to_label: str,
    ctx: Context[ServerSession, AppContext],
    relation_options: dict[str, Any] | None = None,
) -> CallToolResult:
    """Create a new dialectical relation between two existing nodes.

    Args:
        from_label: Source node label
        to_label: Target node label
        relation_options: Relation configuration (relation_type, target_premise_idx, grounding_strategy)

    Example usage:

        connect(
            from_label="ARGUMENT_1",
            to_label="CLAIM_1",
            relation_options={"relation_type": "support"}
        )
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        kwargs = relation_options or {}

        if mode == "sketch":
            if kwargs.get("grounding_strategy") is not None:
                tc.issue("warning",
                    "Ignoring grounding strategies in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to use grounding strategies."
                )
                kwargs["grounding_strategy"] = None
            if kwargs.get("target_premise_idx") is not None:
                tc.issue("warning", 
                    "Ignoring target_premise_idx in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to specify target premise index."
                )
                kwargs["target_premise_idx"] = None
        elif mode == "review":
            tc.issue("info", 
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
                                tc.issue("warning", f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
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
                                tc.issue("warning", f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
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
def remove(
    ctx: Context[ServerSession, AppContext],
    label: str | None = None,
    relation: dict[str, str] | None = None,
) -> CallToolResult:
    """Remove an existing node or relation from the argument map.

    Provide either `label` (to remove a node) OR `relation` (to remove a relation),
    but not both.

    Args:
        label: Label of the node to remove (for node removal).
        relation: Dictionary with `from_label` and `to_label` keys (for relation removal).
        ctx: Tool context (auto-injected).

    Example usage:

        # Remove a node
        remove(label="CLAIM_1")
        
        # Remove a relation
        remove(relation={"from_label": "ARG_1", "to_label": "CLAIM_1"})
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        # Validate mutually exclusive parameters
        if label and label.strip() and relation:
            tc.issue("info", "Ignoring relation when removing a node.", priority=.2)
            relation = None
        
        # Extract relation parameters if provided
        to_label = None
        from_label = None
        if relation:
            from_label = relation.get("from_label")
            to_label = relation.get("to_label")
        
        # Validate that we have exactly one operation
        if label and label.strip():
            # Node removal - label is valid
            pass
        elif from_label and from_label.strip() and to_label and to_label.strip():
            # Relation removal - both from_label and to_label are valid
            pass
        else:
            return tc.issue(
                "error",
                "To remove a node, provide a non-empty 'label'. To remove a relation, provide a 'relation' dict with non-empty 'from_label' and 'to_label'.",
            ).suggest(
                "remove",
                {
                    "label": "NODE_LABEL",
                },
                "Remove a node by specifying its label.",
            ).suggest(
                "remove",
                {
                    "relation": {
                        "from_label": "SOURCE_NODE_LABEL",
                        "to_label": "TARGET_NODE_LABEL",
                    }
                },
                "Remove a relation by specifying source and target node labels in relation dict.",
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
async def export(ctx: Context[ServerSession, AppContext],) -> CallToolResult:
    """
    Generate SVG visualization of the argument map.
    
    Creates a visual representation of the current argument map using GraphViz.
    Returns the SVG as an image that can be displayed directly by visual clients.
        
    Returns:
        CallToolResult with ImageContent containing the SVG visualization and
        structured metadata about the graph (node counts, edge counts).
        
    Example:
        Call this tool to generate and visualize the current argument map.
        The result will be displayed as an image in compatible clients.
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
    
        try:
            svg_string = export_svg(arg_map)
            
            # Encode SVG as base64 for ImageContent
            svg_base64 = base64.b64encode(svg_string.encode('utf-8')).decode('ascii')
            
            # Count nodes by type
            claim_nodes = arg_map.list_claims()
            argument_nodes = arg_map.list_arguments()
            
            return CallToolResult(
                content=[
                    ImageContent(
                        type="image",
                        data=svg_base64,
                        mimeType="image/svg+xml"
                    )
                ],
                structuredContent={
                    "format": "svg",
                    "total_nodes": len(claim_nodes + argument_nodes),
                    "claim_count": len(claim_nodes),
                    "argument_count": len(argument_nodes),
                },
                isError=False
            )
        
        except RuntimeError as e:
            # GraphViz not installed
            return tc.failure(
                f"Error: {str(e)}", error="GraphVizNotInstalled"
            ).build()        
        except Exception as e:
            # Other errors
            return tc.failure(
                f"Error generating SVG: {str(e)}", error="SVGGenerationError"
            ).build()



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