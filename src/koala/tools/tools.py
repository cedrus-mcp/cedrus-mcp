"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from typing import Any, Literal

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult  # , ImageContent
from pydantic import AnyUrl

from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.base import Mode
from koala.models.relations import DialecticalRelationType, GroundingStrategy
import koala.resources
from koala.server import AppContext, mcp
from koala.tools import relation_authoring, suggestions, utils
from koala.tools import node_creation, node_updates, node_deletion
from koala.tools.tool_args import parse_tool_args
from koala.tools.tool_context import tool_context
from koala.validation import validate_argument_map

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


@mcp.tool()
async def add_claim(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new claim node to your argumentation graph.

    A claim represents a single proposition. By adding a claim, you're not ascertaining its truth,
    but rather introducing it as a point for discussion within your argument map. Try to keep claims clear,
    unambiguous, and focused on a single idea. Provide a succinct and informative label that captures
    the essence of the claim and helps you to refer to it easily later on.

    Args:
        label: Succinct and informative title (serves as unique identifier for the claim)
        proposition: The content of the claim
        tags: Optional list of tags for the claim

    Example usage:

        add_claim(
            label="My-New-Claim",
            proposition="The Earth is round.",
            tags=["geography", "science"]
        )

    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")

        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            argdown = await koala.resources.graph_views.graph_thin_resource()
            tc.embed_resource(AnyUrl("argmap://graph/thin/argdown"), argdown, 0.9)
            params = {"label": f"Revised-{label}"}
            if proposition:
                params["proposition"] = proposition
            tc.suggest(
                "add_claim",
                params,
                "Make sure this claim is distinct from the existing one, and add the claim again with a new unique label.",
                action_type="expand",
            )

        try:
            node_creation.new_claim(
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
        except Exception as e:
            logger.error(f"Error creating claim `{label}`: {str(e)}")
            return tc.failure(f"✗ Failed to create claim `{label}`: {str(e)}", error=str(e)).build()

        try:
            suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
        except Exception as e:
            logger.error(f"Error adding suggestions after creating claim `{label}`: {str(e)}")

        return tc.build()


@mcp.tool()
async def add_argument(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new argument node to your argumentation graph.

    An argument represents a justification or an objection. In `sketch` mode, provide a 'gist' to summarize the
    key idea of the argument. In `author` mode, use premises and conclusion to detail its structure. Be clear and
    concise in your descriptions. Provide a succinct and informative label that captures
    the essence of the argument and helps you to refer to it easily later on.

    By adding an argument, you're not necessarily asserting its premises or conclusion as true.

    Args:
        label: Succinct and informative title (serves as unique identifier for the argument)
        gist: A brief summary of the argument
        premises: List of premises supporting the argument
        conclusion: Conclusion drawn from the premises
        tags: Optional list of tags for the argument

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
            conclusion="This statement can be concluded.",
            tags=["some topic"]
        )
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")

        if label in arg_map.list_node_labels():
            tc.failure(
                f"Node with label '{label}' already exists.",
                error="DuplicateLabel",
            )
            argdown = await koala.resources.graph_views.graph_thin_resource()
            tc.embed_resource(AnyUrl("argmap://graph/thin/argdown"), argdown, 0.9)
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

        kwargs = {
            "gist": gist,
            "premises": premises,
            "conclusion": conclusion,
            "to_label": None,
            "from_label": None,
            "relation_type": "support",
            "target_premise_idx": None,
            "tags": tags,
        }
        try:
            node_creation.new_argument(
                label=label,
                **kwargs,
                metadata=None,
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:
            logger.error(f"Error creating argument `{label}` ({kwargs}): {str(e)}")
            return tc.failure(
                f"✗ Failed to create argument `{label}`: {str(e)}", error=str(e)
            ).build()

        try:
            suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
        except Exception as e:
            logger.error(f"Error adding suggestions after creating argument `{label}`: {str(e)}")

        return tc.build()


@mcp.tool()
def edit(
    label: NodeLabel,
    field: Literal["label", "proposition", "gist", "conclusion", "premises", "tags", "metadata"],
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

        edit(
            label="Existing-Argument",
            field="premises",
            edit_options={"premise_idx": 1, "new_value": "This is the revised first premise."}
        )
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if not arg_map.is_node(label):
            most_similar_label, _ = next(arg_map.most_similar_labels(label), (None, 0))
            msg = f"Node '{label}' does not exist."
            if most_similar_label:
                msg += f" Did you mean '{most_similar_label}'?"
            return tc.failure(msg, error="NonExistentNode").build()

        node = arg_map.get_node(label)

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
            logger.error(
                f"Error editing field '{args.field}' of {args.node_type} node `{label}`: {str(e)}"
            )
            return tc.failure(f"✗ Failed to edit node `{label}`: {str(e)}", error=str(e)).build()

        logger.error(
            f"Unhandled case when editing field '{args.field}' of {args.node_type} node `{label}`."
        )
        return tc.failure(
            f"✗ Failed to edit field '{args.field}' of {args.node_type} node `{label}`."
        ).build()


@mcp.tool()
def connect(
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    grounding_strategy: GroundingStrategy | None = None,
) -> CallToolResult:
    """Create a new dialectical relation between two existing nodes.

    Args:
        source: Source node label
        target: Target node label
        relation_type: Type of relation (support or attack). Default is support.
        target_premise_idx: (Optional) Index of the premise in the target argument (will be used to "ground" the relation)
        grounding_strategy: (Optional) Strategy for grounding the relation in the internal logical structure of the nodes

    Example usage:

        # Basic usage:
        connect(
            source="Existing-Argument-Title",
            target="Existing-Claim-Title",
            relation_type="support"
        )

        # Advanced usage (with grounding strategy):
        connect(
            source="Some-Argument",
            target="Another-Argument",
            relation_type="attack",
            target_premise_idx=2,
            grounding_strategy="define_negation"  # Declares that the source argument's conclusion negates the 2nd premise of the target argument
        )
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if mode == "sketch":
            if grounding_strategy is not None:
                tc.issue(
                    "warning", "Ignoring grounding strategies in 'sketch' mode.", priority=0.2
                ).suggest(
                    "mode",
                    {"mode": "author"},
                    "Switch to 'author' mode to use grounding strategies.",
                )
                grounding_strategy = None
            if target_premise_idx is not None:
                tc.issue(
                    "warning", "Ignoring target_premise_idx in 'sketch' mode.", priority=0.2
                ).suggest(
                    "mode",
                    {"mode": "author"},
                    "Switch to 'author' mode to specify target premise index.",
                )
                target_premise_idx = None
        elif mode == "review":
            tc.issue(
                "info", "Creating new relations in 'review' mode. Consider switching mode."
            ).suggest(
                "mode", {"mode": "author"}, "Switch to 'author' mode to create new relations."
            ).suggest(
                "validate",
                {},
                "Run 'validate' to check the argument map.",
            )

        args = parse_tool_args(
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
                        return relation_authoring.new_support_relation(
                            from_label=args.source,
                            to_label=args.target,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "attack":
                        return relation_authoring.new_attack_relation(
                            from_label=args.source,
                            to_label=args.target,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case _:
                        return tc.failure(
                            f"Invalid relation type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
            elif mode != "author":
                return (
                    tc.failure(
                        f"Cannot ground existing relation from `{args.source}` to `{args.target}` in '{mode}' mode.",
                        error="RelationAlreadyExists",
                    )
                    .suggest(
                        "mode",
                        {"mode": "author"},
                        "Switch to 'author' mode to ground existing relations.",
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
                                return relation_authoring.ground_support_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.issue(
                                    "warning",
                                    f"Failed to ground with strategy '{try_grounding_strategy}': {str(e)}",
                                    priority=0.1,
                                )
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
                                return relation_authoring.ground_attack_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.issue(
                                    "warning",
                                    f"Failed to ground with strategy '{try_grounding_strategy}': {str(e)}",
                                    priority=0.1,
                                )
                        return tc.failure(
                            f"✗ Failed to ground attack relation from `{args.source}` to `{args.target}`.",
                            error="GroundingFailed",
                        ).build()
                    case _:
                        return tc.failure(
                            f"Invalid relation type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
        except Exception as e:
            logger.error(
                f"Error creating {args.relation_type} relation from `{args.source}` to `{args.target}`: {str(e)}"
            )
            return tc.failure(
                f"✗ Failed to create {args.relation_type} relation from `{args.source}` to `{args.target}`: {str(e)}",
                error=str(e),
            ).build()

        logger.error(
            f"Unhandled case when creating relation from `{args.source}` to `{args.target}`."
        )
        raise RuntimeError(
            f"Internal Error: Unhandled case when creating relation from `{args.source}` to `{args.target}`."
        )


@mcp.tool()
def remove(
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel | None = None,
    source: NodeLabel | None = None,
    target: NodeLabel | None = None,
) -> CallToolResult:
    """Remove an existing node or relation from the argument map.

    Provide either `label` (to remove a node) OR `source` and `target` (to remove a relation),
    but not all.

    Args:
        label: Label of the node to remove (for node removal).
        source: Source node label of the relation to remove (for relation removal).
        target: Target node label of the relation to remove (for relation removal).
        ctx: Tool context (auto-injected).

    Example usage:

        # Remove a node
        remove(label="Existing-Node-Title")

        # Remove a relation
        remove(source="Existing-Argument", target="Existing-Claim")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        # Validate mutually exclusive parameters
        if label and label.strip() and (source or target):
            return tc.failure(
                "Provide either 'label' (to remove a node) OR 'source' and 'target' (to remove a relation), but not all.",
                error="InvalidParameters",
            ).suggest(
                "remove",
                {
                    "label": label,
                },
                f"Remove the node `{label}` by specifying its label.",
            ).build()

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
                            "target": "TARGET_NODE_LABEL"
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
            elif source and target:
                return relation_authoring.delete_relation(
                    from_label=source,
                    to_label=target,
                    arg_map=arg_map,
                    tc=tc,
                )
        except Exception as e:
            logger.error(f"Error removing node/relation: {str(e)}")
            return tc.failure(f"✗ Failed to remove node/relation: {str(e)}", error=str(e)).build()
        logger.error("Unhandled case in remove tool.")
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
        try:
            text = await koala.resources.instructions.instruction_resource()
            tc.embed_resource(uri=AnyUrl("argmap://instructions"), text=text)
        except Exception as e:
            logger.error(f"Error embedding instructions resource: {str(e)}")
            return tc.failure(
                f"✗ Failed to embed instructions resource: {str(e)}", error=str(e)
            ).build()

    tc.success("✓ Printed instructions.")
    return tc.build()


@mcp.tool()
async def inspect_graph(
    ctx: Context[ServerSession, AppContext],
    verbose: bool = False,
    format: Literal["argdown", "tree"] = "argdown",
) -> CallToolResult:
    """Show an overview representation of the current argumentation graph.

    Args:
        verbose: If True, include detailed information about each node.
        format: The format of the graph representation ("argdown" or "tree").
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if format not in ["argdown", "tree"]:
            return tc.failure(
                f"Invalid format '{format}'. Supported formats are 'argdown' and 'tree'.",
                error="InvalidFormat",
            ).build()

        # embed graph
        try:
            if verbose:
                text = await koala.resources.graph_views.graph_details_resource(format=format)
                uri = AnyUrl(f"argmap://graph/details/{format}")
            else:
                text = await koala.resources.graph_views.graph_thin_resource(format=format)
                uri = AnyUrl(f"argmap://graph/thin/{format}")
            tc.embed_resource(uri=uri, text=text)
        except Exception as e:
            logger.error(f"Error showing graph representation: {str(e)}")
            return tc.failure(
                f"✗ Failed to show graph representation: {str(e)}", error=str(e)
            ).build()

        # embed statistics
        try:
            if verbose:
                stats = await koala.resources.summaries.statistics_resource()
                text = f"# Graph Statistics\n\n{stats}"
                tc.embed_resource(uri=AnyUrl("argmap://statistics"), text=text)
        except Exception as e:
            logger.error(f"Error showing graph statistics: {str(e)}")
            tc.issue("warning", f"✗ Failed to show graph statistics: {str(e)}", error=str(e))

    tc.success("✓ Printed graph representation.")
    return tc.build()


@mcp.tool()
async def inspect_neighborhood(
    ctx: Context[ServerSession, AppContext],
    label: NodeLabel,
    k: int = 2,
) -> CallToolResult:
    """Show detailed information about the k-neighborhood of a specific node in the argument map.

    Args:
        label: The label of the node whose neighborhood to inspect.
        k: The radius of the neighborhood to include.
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
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
            uri = f"argmap://neighborhood/{label}/{k}"
            text = await koala.resources.graph_views.neighborhood_details_resource(label, k)
            tc.embed_resource(uri=AnyUrl(uri), text=text)
        except Exception as e:
            logger.error(f"Error showing neighborhood of node '{label}': {str(e)}")
            return tc.failure(
                f"✗ Failed to show neighborhood of node '{label}': {str(e)}", error=str(e)
            ).build()

    tc.success(f"✓ Printed {k}-neighborhood of node '{label}'.")
    return tc.build()


@mcp.tool()
async def inspect_node(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Show detailed information about a specific node in the argument map.

    Args:
        label: The label of the node to inspect.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if not arg_map.is_node(label):
            most_similar_label, _ = next(arg_map.most_similar_labels(label), (None, 0))
            msg = f"Node '{label}' does not exist."
            if most_similar_label:
                msg += f" Did you mean '{most_similar_label}'?"
            return tc.failure(msg, error="NonExistentNode").build()

        try:
            uri = f"argmap://node/details/{label}"
            text = await koala.resources.node_details.node_details_resource(label)
            tc.embed_resource(uri=AnyUrl(uri), text=text)
        except Exception as e:
            logger.error(f"Error showing details of node '{label}': {str(e)}")
            return tc.failure(
                f"✗ Failed to show details of node '{label}': {str(e)}", error=str(e)
            ).build()

    tc.success(f"✓ Printed details of node '{label}'.")
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
            tc.issue("info", "Validation may be limited in 'sketch' mode.")

        try:
            issues_found = validate_argument_map(arg_map, tc, fix=fix, max_issues=max_issues)
        except Exception as e:
            logger.error(f"Error during argument map validation: {str(e)}")
            return tc.failure(f"✗ Failed to validate argument map: {str(e)}", error=str(e)).build()

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

    Args:
        mode: The mode to switch to ("sketch", "author", or "review").

    Example usage:

        mode("author")
    """

    # TODO: Dynamically add and remove tools based on mode
    # See also: https://github.com/modelcontextprotocol/python-sdk/issues/1429#issuecomment-3669447896
    # For sketch mode:
    # - add_claim(label, proposition)
    # - add_argument(label, gist)
    # - connect(source, target, relation_type)
    # - remove(label, source, target)
    #
    # For author mode:
    # - add_claim(label, proposition, tags)
    # - add_argument(label, gist, premises, conclusion, tags)
    # - edit(label, field, edit_options)
    # - connect(source, target, relation_type, target_premise_idx, grounding_strategy)
    # - remove(label, source, target)
    # - inspect_node(label)
    #
    # For review mode:
    # - validate(fix, max_issues)
    # - inspect_node(label)
    #
    # Shared tools:
    # - instructions()
    # - inspect_graph(verbose, format)
    # - inspect_neighborhood(label, k)
    # - mode(mode)


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
