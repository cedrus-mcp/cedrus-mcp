"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult #, ImageContent
from pydantic import AnyUrl

from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.base import Mode
import koala.resources
from koala.server import AppContext, mcp
from koala.tools import relation_authoring, suggestions, utils
from koala.tools import node_creation, node_updates, node_deletion
from koala.tools.tool_args import parse_tool_args
from koala.tools.tool_context import tool_context
from koala.validation import validate_argument_map

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


# @mcp.tool()
# def add(
#     label: NodeLabel,
#     ctx: Context[ServerSession, AppContext],
#     node_options: dict[str, Any] | None = None,
#     relation_options: dict[str, Any] | None = None,
# ) -> CallToolResult:
#     """Create a new node (claim or argument) in the argument map.
    
#     To create an argument, provide a "gist" in node_options or set node_type to "argument".

#     Args:
#         label: Succinct and informative title (serves as unique identifier for the node)
#         node_options: Node configuration (proposition, gist, conclusion, premises, node_type, tags, metadata)
#         relation_options: Optional relation to create (to_label, from_label, relation_type, target_premise_idx)

#     Example usage:

#         add(
#             label="MY-NEW-CLAIM",
#             node_options={"proposition": "This is a new claim."},
#             relation_options={"from_label": "EXISTING-ARGUMENT-TITLE", "relation_type": "support"}
#         )

#     Take care to use succinct and informative labels instead of placeholders like "CLAIM_1".
#     """
#     arg_map = ctx.request_context.lifespan_context.arg_map
#     mode = ctx.request_context.lifespan_context.mode

#     with tool_context(arg_map, mode) as tc:

#         if not label or not label.strip():
#             raise ValueError("Label must be a non-empty string.")
        
#         # Ensure label is unique
#         label = utils.ensure_label_is_unique(label, arg_map, tc)

#         # Merge node_options and relation_options
#         kwargs = {}
#         if node_options:
#             kwargs.update(node_options)
#         if relation_options:
#             kwargs.update(relation_options)

#         args = parse_tool_args("add", tc, arg_map, **kwargs)

#         try:
#             if args.node_type == "claim":
#                 # Adding a claim node
#                 node_creation.new_claim(
#                     label=label,
#                     proposition=args.proposition,
#                     to_label=args.to_label,
#                     from_label=args.from_label,
#                     relation_type=args.relation_type or "support",
#                     target_premise_idx=args.target_premise_idx,
#                     tags=args.tags,
#                     metadata=args.metadata,
#                     arg_map=arg_map,
#                     tc=tc,
#                 )
#             elif args.node_type == "argument":
#                 # Adding an argument node
#                 node_creation.new_argument(
#                     label=label,
#                     gist=args.gist,
#                     to_label=args.to_label,
#                     from_label=args.from_label,
#                     relation_type=args.relation_type or "support",
#                     target_premise_idx=args.target_premise_idx,
#                     premises=args.premises,
#                     conclusion=args.conclusion,
#                     tags=args.tags,
#                     metadata=args.metadata,
#                     arg_map=arg_map,
#                     tc=tc,
#                 )
#         except Exception as e:
#             return tc.failure(
#                 f"✗ Failed to create {args.node_type} `{label}`: {str(e)}", error=str(e)
#             ).build()
#         suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
#         return tc.build()
    

@mcp.tool()
def add_claim(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    relation_options: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CallToolResult:
    """Add a new claim node to your argumentation graph.

    A claim represents a single proposition. By adding a claim, you're not ascertaining its truth, 
    but rather introducing it as a point for discussion within your argument map. Try to keep claims clear, 
    unambiguous, and focused on a single idea. Provide a succinct and informative label that captures 
    the essence of the claim and helps you to refer to it easily later on.

    Args:
        label: Succinct and informative title (serves as unique identifier for the claim)
        proposition: The content of the claim
        relation_options: Optional relation to create (to_label, from_label, relation_type, target_premise_idx)
        tags: Optional list of tags for the claim
        metadata: Optional dictionary of metadata for the claim

    Example usage:

        # Basic
        add_claim(
            label="My-New-Claim",
            proposition="The Earth is round."
        )

        # Advanced
        add_claim(
            label="My-New-Claim",
            proposition="The Earth is round.",
            relation_options={"to_label": "Existing-Argument-Title", "relation_type": "support"},
            tags=["geography", "science"],
            metadata={"source": "common knowledge"}
        )
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode
    relation_options = relation_options or {}

    with tool_context(arg_map, mode) as tc:

        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")
        
        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            tc.embed_resource(AnyUrl("argmap://graph/thin"), "Current Argument Map", 0.9)
            params = {"label": f"Revised-{label}"}
            if proposition:
                params["proposition"] = proposition
            tc.suggest(
                "add_claim",
                params,
                "Make sure this claim is distinct from the existing one, and add the claim again with a new unique label.",
                action_type="expand",
            )

        # Validate relation arguments
        relation_type = relation_options.pop("relation_type", None)
        to_label, from_label, target_premise_idx = utils.sanitize_relation_args_new_node(
            arg_map=arg_map, tc=tc, **relation_options
        )
        if to_label or from_label:
            if relation_type is None:
                tc.issue("info", "Assuming 'support' relation type as default.", priority=.2)
                relation_type = "support"
            if relation_type not in ["support", "attack"]:
                return tc.failure(
                    f"Invalid relation_type '{relation_type}'. Must be 'support' or 'attack'.",
                    error="InvalidRelationType",
                ).build()

        try:
            node_creation.new_claim(
                label=label,
                proposition=proposition,
                to_label=to_label,
                from_label=from_label,
                relation_type=relation_type,
                target_premise_idx=target_premise_idx,
                tags=tags,
                metadata=metadata,
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create claim `{label}`: {str(e)}", error=str(e)
            ).build()

        suggestions.add_suggestions_after_adding_node(label, arg_map, tc)

        return tc.build()

@mcp.tool()
def add_argument(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    relation_options: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CallToolResult:
    """Add a new argument node to your argumentation graph.
    
    An argument represents a justification or an objection. Provide a 'gist' to summarize the 
    key idea of the argument. Use premises and conclusion to detail its structure. Be clear and
    concise in your descriptions. Provide a succinct and informative label that captures
    the essence of the argument and helps you to refer to it easily later on.

    By adding an argument, you're not necessarily asserting its premises or conclusion as true.

    Args:
        label: Succinct and informative title (serves as unique identifier for the argument)
        gist: A brief summary of the argument
        premises: List of premises supporting the argument
        conclusion: Conclusion drawn from the premises
        relation_options: Optional relation to create (to_label, from_label, relation_type, target_premise_idx)
        tags: Optional list of tags for the argument
        metadata: Optional dictionary of metadata for the argument

    Example usage:

        # Basic
        add_argument(
            label="My-New-Argument",
            gist="This is a brief summary of the argument."
        )

        # Advanced
        add_argument(
            label="My-New-Argument",
            gist="This is a brief summary of the argument.",
            premises=["Premise 1", "Premise 2"],
            conclusion="Therefore, the conclusion follows.",
            relation_options={"to_label": "Supported-Claim-Title", "relation_type": "support"},
            tags=["some topic"]
        )
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode
    relation_options = relation_options or {}

    with tool_context(arg_map, mode) as tc:

        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")

        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            tc.embed_resource(AnyUrl("argmap://graph/thin"), "Current Argument Map", 0.9)
            params = {"label": f"Revised-{label}"}
            if gist:
                params["gist"] = gist
            tc.suggest(
                "add_argument",
                params,
                "Make sure this argument is distinct from the existing one, and add the argument again with a new unique label.",
                action_type="expand",
            )
            return tc.build()

        # Validate relation arguments
        relation_type = relation_options.pop("relation_type", None)
        to_label, from_label, target_premise_idx = utils.sanitize_relation_args_new_node(
            arg_map=arg_map, tc=tc, **relation_options
        )
        if to_label or from_label:
            if relation_type is None:
                tc.issue("info", "Assuming 'support' relation type as default.", priority=.2)
                relation_type = "support"
            if relation_type not in ["support", "attack"]:
                return tc.failure(
                    f"Invalid relation_type '{relation_type}'. Must be 'support' or 'attack'.",
                    error="InvalidRelationType",
                ).build()

        try:
            node_creation.new_argument(
                label=label,
                gist=gist,
                premises=premises,
                conclusion=conclusion,
                to_label=to_label,
                from_label=from_label,
                relation_type=relation_type,
                target_premise_idx=target_premise_idx,
                tags=tags,
                metadata=metadata,
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create argument `{label}`: {str(e)}", error=str(e)
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
            label="Existing-Claim",
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

        # Basic usage:
        connect(
            from_label="Existing-Argument-Title",
            to_label="Existing-Claim-Title",
            relation_options={"relation_type": "support"}
        )

        # Advanced usage (with grounding strategy):
        connect(
            from_label="Some-Argument",
            to_label="Another-Argument",
            relation_options={
                "relation_type": "attack",
                "target_premise_idx": 2,
                "grounding_strategy": "define_negation"
            }
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
            ).suggest(
                "validate", {}, "Run 'validate' to check the argument map.",
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
        remove(label="Existing-Node-Title")
        
        # Remove a relation
        remove(relation={"from_label": "Existing-Argument", "to_label": "Existing-Claim"})
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


##############################################
# Exposing resources as tools
##############################################


@mcp.tool()
async def instructions(ctx: Context[ServerSession, AppContext]) -> CallToolResult:
    """Show instructions for current mode.

    Example usage:

        instructions()
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        text = await koala.resources.instructions.instruction_resource()
        tc.embed_resource(
            uri=AnyUrl("argmap://instructions"),
            text=text
        )

    tc.success("✓ Printed instructions.")
    return tc.build()        


@mcp.tool()
async def inspect(uri: str, ctx: Context[ServerSession, AppContext]) -> CallToolResult:
    """Show specific info for the current argument map, as specified by resource uri.

    Args:    
        uri: The URI of the resource / view to show.

    Available resources (URI patterns):
        - argmap://graph/thin : Thin argdown representation of the entire argument map (labels only).
        - argmap://graph/details : Detailed argdown representation of the entire argument map.
        - argmap://neighborhood/{label}/{k} : Detailed argdown representation of the k-neighborhood of node `label`.
        - argmap://node/details/{label} : Detailed argdown representation of node `label`.
        - argmap://statistics : Descriptive statistics of the argument map.

    Example usage:

        inspect("argmap://graph/thin")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if uri == "argmap://graph/thin":
            text = await koala.resources.graph_views.graph_thin_resource()
            tc.embed_resource(
                uri=AnyUrl("argmap://graph/thin"),
                text=text
            )
        elif uri == "argmap://graph/details":
            text = await koala.resources.graph_views.graph_details_resource()
            tc.embed_resource(
                uri=AnyUrl("argmap://graph/details"),
                text=text
            )
        elif uri.startswith("argmap://neighborhood/"):
            parts = uri[len("argmap://neighborhood/"):].split("/")
            if len(parts) != 2:
                return tc.failure(
                    "Invalid URI format for neighborhood resource. Expected 'argmap://neighborhood/{{label}}/{{k}}'.",
                    error="InvalidURIFormat",
                ).build()
            label = parts[0]
            try:
                k = int(parts[1])
            except ValueError:
                return tc.failure(
                    f"Invalid value for k in neighborhood resource. Expected an integer, got '{parts[1]}'.",
                    error="InvalidKValue",
                ).build()
            text = await koala.resources.graph_views.neighborhood_details_resource(label, k)
            tc.embed_resource(
                uri=AnyUrl(uri),
                text=text
            )
        elif uri.startswith("argmap://node/details/"):
            label = uri[len("argmap://node/details/"):]
            node = arg_map.get_node(label)
            if node is None:
                return tc.failure(
                    f"Node '{label}' does not exist.",
                    error="NonExistentNode",
                ).build()
            text = await koala.resources.node_details.node_details_resource(label)
            tc.embed_resource(
                uri=AnyUrl(uri),
                text=text
            )
        elif uri == "argmap://statistics":
            text = await koala.resources.summaries.statistics_resource()
            tc.embed_resource(
                uri=AnyUrl("argmap://statistics"),
                text=text
            )
        else:
            return tc.failure(
                f"Unknown resource URI '{uri}'.",
                error="UnknownResourceURI",
            ).build()

    tc.success("✓ Printed resource.")
    return tc.build()        


###############################################
# Additional tools
###############################################

@mcp.tool()
def validate(
    ctx: Context[ServerSession, AppContext],
    fix: bool = False,
    max_issues: int | None = None,
) -> CallToolResult:
    """Validate the current argument map for consistency and completeness.

    Args:
        fix: If True, attempt to automatically fix certain issues.
        max_issues: Maximum number of issues to report (defaults to None for no limit).

    Example usage:

        validate()
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if tc.mode == "sketch":
            tc.issue("info",
                "Validation may be limited in 'sketch' mode. Consider switching to 'author' mode for full validation."
            ).suggest(
                "mode", {"mode": "author"}, "Switch to 'author' mode for comprehensive validation."
            )

        issues_found = validate_argument_map(arg_map, tc, fix=fix, max_issues=max_issues)

        if not any(issue.severity == "error" for issue in tc.issues):
            tc.success("✓ Argument map is valid and consistent.")
        else:
            tc.success(
                f"✗ Argument map has {issues_found} issues.",
            )
            if not fix:
                tc.suggest(
                    "validate",
                    {"fix": True},
                    "Run validate with fix=True to attempt automatic corrections.",
                )

        return tc.build()


# @mcp.tool()
# async def export_svg(ctx: Context[ServerSession, AppContext],) -> CallToolResult:
#     """
#     Generate SVG visualization of the argument map.
    
#     Creates a visual representation of the current argument map using GraphViz.
#     Returns the SVG as an image that can be displayed directly by visual clients.
        
#     Returns:
#         CallToolResult with ImageContent containing the SVG visualization and
#         structured metadata about the graph (node counts, edge counts).
        
#     Example:
#         Call this tool to generate and visualize the current argument map.
#         The result will be displayed as an image in compatible clients.
#     """
#     arg_map = ctx.request_context.lifespan_context.arg_map
#     mode = ctx.request_context.lifespan_context.mode

#     with tool_context(arg_map, mode) as tc:
    
#         try:
#             svg_string = koala.graph.svg_export.export_svg(arg_map)
            
#             # Encode SVG as base64 for ImageContent
#             svg_base64 = base64.b64encode(svg_string.encode('utf-8')).decode('ascii')
            
#             # Count nodes by type
#             claim_nodes = arg_map.list_claims()
#             argument_nodes = arg_map.list_arguments()
            
#             return CallToolResult(
#                 content=[
#                     ImageContent(
#                         type="image",
#                         data=svg_base64,
#                         mimeType="image/svg+xml"
#                     )
#                 ],
#                 structuredContent={
#                     "format": "svg",
#                     "total_nodes": len(claim_nodes + argument_nodes),
#                     "claim_count": len(claim_nodes),
#                     "argument_count": len(argument_nodes),
#                 },
#                 isError=False
#             )
        
#         except RuntimeError as e:
#             # GraphViz not installed
#             return tc.failure(
#                 f"Cannot generate SVG because `graphviz` is not installed. (Original error message: {str(e)})", error="GraphVizNotInstalled"
#             ).build()        
#         except Exception as e:
#             # Other errors
#             return tc.failure(
#                 f"Error generating SVG: {str(e)}", error="SVGGenerationError"
#             ).build()



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
        tc.suggest(
            "instructions",
            {},
            f"Run 'instructions' to see guidelines for '{mode}' mode.",
            action_type="help",
        )
        return tc.build()