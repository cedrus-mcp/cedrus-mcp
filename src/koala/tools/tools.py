"""MCP tool implementations with mode-aware dynamic registration.

This module defines all MCP tools for the KOALA argument mapping server.
Tools are organized into mode-specific variants that expose different signatures
based on the current editing mode (sketch, elaborate, review).

Tool Organization:
    **Core Implementations**: Private functions (_*_impl) that contain the
    actual business logic. These accept all possible parameters and are called
    by mode-specific wrappers.
    
    **Mode-Specific Wrappers**: Public async functions that provide simplified
    signatures for each mode. For example:
    
    - add_argument_sketch(label, gist) - Minimal parameters for quick prototyping
    - add_argument_elaborate(label, gist, premises, conclusion, tags) - Full detail
    
    **Shared Tools**: Tools available in all modes with consistent signatures
    (e.g., get_instructions, inspect_graph).

Mode System:
    - **sketch**: Rapid prototyping with minimal detail
      Tools: add_claim, add_argument, connect, remove + shared
      Simple parameters, no tags, no grounding
    
    - **elaborate**: Detailed argumentation with full structure
      Tools: add_claim, add_argument, connect, edit, remove, inspect_node + shared
      Full parameters including tags, premises, conclusion, grounding strategies
    
    - **review**: Validation and quality assurance
      Tools: validate, inspect_node + shared
      Focus on checking consistency and completeness

Dynamic Tool Management:
    Tools are registered and swapped dynamically when the mode changes:
    
    1. Mode-specific variants are registered in _register_tool_variants()
    2. Initial tools are registered at server startup (server.py)
    3. When set_mode() is called:
       a. Tools exclusive to old mode are removed via mcp.remove_tool()
       b. Tools exclusive to new mode are added via mcp.add_tool()
       c. Client is notified via ctx.session.send_tool_list_changed()

Implementation Pattern:
    For tools with mode-specific variants:
    
        # 1. Core implementation with all parameters
        async def _my_tool_impl(
            required_arg: str,
            ctx: Context,
            optional_arg: str | None = None,
        ) -> CallToolResult:
            # Implementation here
        
        # 2. Mode-specific wrappers with subset of parameters
        async def my_tool_sketch(
            required_arg: str,
            ctx: Context,
        ) -> CallToolResult:
            return await _my_tool_impl(required_arg, ctx)
        
        async def my_tool_elaborate(
            required_arg: str,
            ctx: Context,
            optional_arg: str | None = None,
        ) -> CallToolResult:
            return await _my_tool_impl(required_arg, ctx, optional_arg)
        
        # 3. Register variants in _register_tool_variants()
        TOOL_REGISTRY.register_variant(ToolVariant(
            fn=my_tool_sketch,
            name="my_tool",  # Same external name
            internal_name="my_tool_sketch",
            modes=["sketch"]
        ))

See Also:
    - koala.tools.tool_registry: Registry infrastructure for tool variants
    - koala.server: Server initialization and startup tool registration
    - koala.models.base: Mode type definition
"""

from typing import Any, Callable, Literal, cast
from textwrap import dedent

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
from koala.server import AppContext
from koala.tools import relation_elaborating, suggestions
from koala.tools import node_creation, node_updates, node_deletion
from koala.tools.tool_args import parse_tool_args
from koala.tools.tool_context import tool_context
from koala.tools.tool_registry import TOOL_REGISTRY, ToolVariant
from koala.validation import validate_argument_map

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


##############################################
# Core tool implementations (private)
##############################################
# These functions contain the actual business logic for tools.
# They accept ALL possible parameters for maximum flexibility.
# Mode-specific wrappers (below) call these with appropriate subsets.
#
# Naming convention: _<tool_name>_impl
# Example: _add_claim_impl, _add_argument_impl, _connect_impl


async def _add_claim_impl(
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


async def _add_argument_impl(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new argument node to your argumentation graph.

    An argument represents a justification or an objection. In `sketch` mode, provide a 'gist' to summarize the
    key idea of the argument. In `elaborate` mode, use premises and conclusion to detail its structure. Be clear and
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

        try:
            node_creation.new_argument(
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
        except Exception as e:
            logger.error(f"Error creating argument `{label}` (gist={gist}, premises={premises}, conclusion={conclusion}): {str(e)}")
            return tc.failure(
                f"✗ Failed to create argument `{label}`: {str(e)}", error=str(e)
            ).build()

        try:
            suggestions.add_suggestions_after_adding_node(label, arg_map, tc)
        except Exception as e:
            logger.error(f"Error adding suggestions after creating argument `{label}`: {str(e)}")

        return tc.build()


async def _connect_impl(
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    grounding_strategy: GroundingStrategy | None = None,
) -> CallToolResult:
    """Core implementation for creating dialectical relations.
    
    Creates a support or attack relation between two nodes in the argument map.
    Handles relation grounding (connecting to specific premises of target arguments)
    when appropriate parameters are provided.
    
    Args:
        source: Label of the source node (supporter/attacker).
        target: Label of the target node (being supported/attacked).
        ctx: FastMCP context (auto-injected).
        relation_type: Type of dialectical relation ("support" or "attack").
        target_premise_idx: Index of specific premise to ground to (elaborate mode only).
        grounding_strategy: Strategy for automatic grounding (elaborate mode only).
    
    Returns:
        CallToolResult with success/failure status and created relation details.
    
    Mode Variants:
        - **Sketch**: ``connect_sketch(source, target, relation_type)`` - no grounding
        - **Elaborate**: ``connect_elaborate(source, target, relation_type, target_premise_idx, grounding_strategy)`` - with grounding
    
    Grounding Behavior:
        - If target is an ArgumentNode and grounding parameters provided:
          
          - ``target_premise_idx``: Ground to specific premise
          - ``grounding_strategy``: Use heuristic to find best premise match
        
        - Otherwise: Create ungrounded relation
    
    Example:
        Called by sketch mode wrapper::
        
            return await _connect_impl(source, target, ctx, relation_type=relation_type)
        
        Called by elaborate mode wrapper::
        
            return await _connect_impl(
                source, target, ctx,
                relation_type=relation_type,
                target_premise_idx=target_premise_idx,
                grounding_strategy=grounding_strategy
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
                    "set_mode",
                    {"mode": "elaborate"},
                    "Switch to 'elaborate' mode to use grounding strategies.",
                )
                grounding_strategy = None
            if target_premise_idx is not None:
                tc.issue(
                    "warning", "Ignoring target_premise_idx in 'sketch' mode.", priority=0.2
                ).suggest(
                    "set_mode",
                    {"mode": "elaborate"},
                    "Switch to 'elaborate' mode to specify target premise index.",
                )
                target_premise_idx = None
        elif mode == "review":
            tc.issue(
                "info", "Creating new relations in 'review' mode. Consider switching mode."
            ).suggest(
                "set_mode", {"mode": "elaborate"}, "Switch to 'elaborate' mode to create new relations."
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
                        return relation_elaborating.new_support_relation(
                            from_label=args.source,
                            to_label=args.target,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "attack":
                        return relation_elaborating.new_attack_relation(
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
            elif mode != "elaborate":
                return (
                    tc.failure(
                        f"Cannot ground existing relation from `{args.source}` to `{args.target}` in '{mode}' mode.",
                        error="RelationAlreadyExists",
                    )
                    .suggest(
                        "set_mode",
                        {"mode": "elaborate"},
                        "Switch to 'elaborate' mode to ground existing relations.",
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
                                return relation_elaborating.ground_support_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception:
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
                                return relation_elaborating.ground_attack_relation(
                                    from_label=args.source,
                                    to_label=args.target,
                                    strategy=try_grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception:
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


##############################################
# Mode-specific tool wrappers
##############################################
# These functions provide mode-appropriate signatures for core implementations.
# Each wrapper calls its corresponding _*_impl function with a subset of parameters.
#
# Pattern for variants:
#   - <tool>_sketch: Minimal parameters for rapid prototyping
#   - <tool>_elaborate: Full parameters for detailed elaborating
#
# These wrappers are registered with TOOL_REGISTRY under the SAME external name
# (e.g., both add_claim_sketch and add_claim_elaborate register as "add_claim").
# When mode changes, the registry swaps which variant is active.

# add_claim variants
async def add_claim_sketch(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
) -> CallToolResult:
    """Add a new claim node (sketch mode - no tags).

    Args:
        label: Succinct and informative title
        proposition: The content of the claim
    """
    return await _add_claim_impl(label, ctx, proposition=proposition, tags=None)


async def add_claim_elaborate(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new claim node (elaborate mode - with tags).

    Args:
        label: Succinct and informative title
        proposition: The content of the claim
        tags: Optional list of tags for the claim
    """
    return await _add_claim_impl(label, ctx, proposition=proposition, tags=tags)


# add_argument variants
async def add_argument_sketch(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
) -> CallToolResult:
    """Add a new argument node (sketch mode - gist only).

    Args:
        label: Succinct and informative title
        gist: A brief summary of the argument
    """
    return await _add_argument_impl(label, ctx, gist=gist)


async def add_argument_elaborate(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
) -> CallToolResult:
    """Add a new argument node (elaborate mode - full structure).

    Args:
        label: Succinct and informative title
        gist: A brief summary of the argument
        premises: List of premises supporting the argument
        conclusion: Conclusion drawn from the premises
        tags: Optional list of tags for the argument
    """
    return await _add_argument_impl(
        label, ctx, gist=gist, premises=premises, conclusion=conclusion, tags=tags
    )


# connect variants
async def connect_sketch(
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
) -> CallToolResult:
    """Create a relation (sketch mode - no grounding).

    Args:
        source: Source node label
        target: Target node label
        relation_type: Type of relation (support or attack)
    """
    return await _connect_impl(source, target, ctx, relation_type=relation_type)


async def connect_elaborate(
    source: str,
    target: str,
    ctx: Context[ServerSession, AppContext],
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    grounding_strategy: GroundingStrategy | None = None,
) -> CallToolResult:
    """Create a relation (elaborate mode - with grounding).

    Args:
        source: Source node label
        target: Target node label
        relation_type: Type of relation (support or attack)
        target_premise_idx: Index of the premise to ground to
        grounding_strategy: Strategy for grounding the relation
    """
    return await _connect_impl(
        source, target, ctx,
        relation_type=relation_type,
        target_premise_idx=target_premise_idx,
        grounding_strategy=grounding_strategy
    )


##############################################
# Tools that remain the same across modes
##############################################
# These tools have consistent signatures across all modes (or specific subsets).
# They don't need variants - the same function is used regardless of mode.
# Examples: edit (elaborate only), validate (review only), get_instructions (all modes)

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
            - For premises/tags: new_value (to add), old_value (to remove), or both
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
            edit_options={"old_value": "This is the original first premise.", "new_value": "This is the revised first premise."}
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
                            old_value=args.old_value,
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
                return relation_elaborating.delete_relation(
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


async def get_instructions(ctx: Context[ServerSession, AppContext]) -> CallToolResult:
    """Show instructions for current mode.

    Example usage:

        get_instructions()
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

async def get_instructions_elaborate(ctx: Context[ServerSession, AppContext], topic: Literal["grounding", "validity"] | None = None) -> CallToolResult:
    """Show detailed instructions for elaborate mode.

    Args:
        topic: Specific topic to get instructions for (e.g., "grounding" or "validity").
    """

    if topic is None:
        return await get_instructions(ctx)

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        try:
            if topic == "grounding":
                text = koala.resources.instructions.instructions_grounding()
                return tc.success("✓ Providing grounding instructions.", result=text).build()
            elif topic == "validity":
                text = koala.resources.instructions.instructions_validity()
                return tc.success("✓ Providing validity instructions.", result=text).build()
            else:
                return tc.failure(
                    f"Unknown topic '{topic}' for elaborate instructions. Available topics: 'grounding', 'validity'.", error="UnknownTopic"
                ).build()
        except Exception as e:
            logger.error(f"Error providing elaborate instructions for topic '{topic}': {str(e)}")
            return tc.failure(
                f"✗ Error providing `elaborate` instructions for topic '{topic}'", error=str(e)
            ).build()



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


async def set_mode(
    mode: Mode,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Switch the argument map editing mode.

    Args:
        mode: The mode to switch to ("sketch", "elaborate", or "review").

    Example usage:

        set_mode("elaborate")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    old_mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:
        if mode not in ["sketch", "elaborate", "review"]:
            return tc.failure(
                f"Invalid mode '{mode}'. Valid modes are 'sketch', 'elaborate', and 'review'.",
                error="InvalidMode",
            ).build()

        # Update mode first
        ctx.request_context.lifespan_context.mode = mode
        
        # Perform dynamic tool swapping if mode actually changed
        if old_mode != mode:
            try:
                await _update_tools_for_mode(ctx, old_mode, mode)
            except Exception as e:
                logger.error(f"Error updating tools for mode switch: {str(e)}")
                tc.issue("warning", f"Tool list may not be fully updated: {str(e)}")
        
        tc.success(f"✓ Switched mode from '{old_mode}' to '{mode}'.")
        tc.suggest(
            "get_instructions",
            {},
            f"Run 'get_instructions' to see guidelines for '{mode}' mode.",
            action_type="help",
        )
        return tc.build()


async def _update_tools_for_mode(
    ctx: Context[ServerSession, AppContext],
    old_mode: Mode,
    new_mode: Mode,
) -> None:
    """Update available tools when switching modes.
    
    Performs the dynamic tool swapping by rebuilding the tool list in canonical
    order. Maintains the order defined in TOOL_ORDER by removing all tools and
    re-registering them in the correct sequence. Also sends a notification to
    the MCP client that the tool list has changed.
    
    Algorithm:
        1. Get tool name sets for old and new modes from TOOL_REGISTRY
        2. Remove ALL old tools via ``mcp_server.remove_tool()``
        3. Iterate through TOOL_ORDER and add tools for new mode in sequence
        4. Send ``tools/list_changed`` notification to client
    
    Args:
        ctx: FastMCP context providing access to server and session.
        old_mode: The mode being switched from.
        new_mode: The mode being switched to.
    
    Raises:
        Exception: Propagates exceptions from tool add/remove operations.
                  Individual failures are logged as warnings but don't stop
                  the overall process.
    
    Example:
        Switching from sketch to elaborate mode::
        
            # Sketch tools: {add_claim, add_argument, connect, remove, ...shared}
            # Elaborate tools: {add_claim, add_argument, connect, edit, remove, inspect_node, ...shared}
            
            # Process in TOOL_ORDER:
            # 1. Remove all old tools (add_claim, add_argument, connect, remove, inspect_graph, ...)
            # 2. Add tools in TOOL_ORDER that are in elaborate mode:
            #    - add_claim (elaborate variant)
            #    - add_argument (elaborate variant)
            #    - edit (new)
            #    - remove (same as before)
            #    - connect (elaborate variant)
            #    - inspect_graph (same as before)
            #    - inspect_neighborhood (same as before)
            #    - inspect_node (new)
            #    - get_instructions (elaborate variant)
            #    - set_mode (same as before)
            
            # Result: tools in canonical TOOL_ORDER sequence
    
    Notes:
        - Tool order is maintained by completely rebuilding the tool list rather
          than selectively adding/removing tools.
        - This ensures consistent ordering even when tools are shared between modes.
        - For tools with variants (e.g., add_argument), both the function and
          description are updated by the rebuild.
        - Failures to add/remove individual tools are logged as warnings but
          don't stop the overall mode switch.
        - Client notification failures are also logged but non-fatal.
    """
    mcp_server = ctx.fastmcp
    
    # Get tool name sets for each mode
    old_tools = TOOL_REGISTRY.get_tool_names_for_mode(old_mode)
    new_tools = TOOL_REGISTRY.get_tool_names_for_mode(new_mode)
    
    # Remove all old tools to rebuild list in canonical order
    for tool_name in old_tools:
        try:
            mcp_server.remove_tool(tool_name)
            logger.debug(f"Removed tool '{tool_name}' when switching from '{old_mode}' to '{new_mode}'")
        except Exception as e:
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
                        **variant.metadata
                    )
                    logger.debug(f"Added tool '{tool_name}' for mode '{new_mode}'")
                except Exception as e:
                    logger.warning(f"Failed to add tool '{tool_name}': {e}")
    
    # Notify client of tool list changes
    try:
        await ctx.session.send_tool_list_changed()
        logger.debug(f"Sent tool_list_changed notification for mode switch to '{new_mode}'")
    except Exception as e:
        logger.warning(f"Failed to send tool_list_changed notification: {e}")


##############################################
# Tool ordering
##############################################

# Canonical order for tool presentation to clients.
# This order reflects the typical workflow and groups related tools together.
# Maintained during mode switches to ensure consistent client experience.
TOOL_ORDER = [
    # Creation tools - for building the argument map
    "add_claim",
    "add_argument",
    
    # Modification tools - for editing and removing nodes/relations
    "edit",
    "remove",
    
    # Connection tools - for creating relations
    "connect",
    
    # Inspection tools - for viewing the argument map
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    
    # Utility tools - for guidance, validation, and mode switching
    "get_instructions",
    "validate",
    "set_mode",
]


##############################################
# Tool variant registration
##############################################

# Register tool variants for each mode
def _register_tool_variants() -> None:
    """Register all tool variants with the tool registry.
    
    Called once at module load time to populate TOOL_REGISTRY with all
    available tool variants and their mode associations.
    
    Tool Distribution by Mode:
        **Sketch Mode** (rapid prototyping):
            - add_claim (simplified: label, proposition)
            - add_argument (simplified: label, gist)
            - connect (simplified: source, target, relation_type)
            - remove (full)
            - *All shared tools*
        
        **Elaborate Mode** (detailed elaborating):
            - add_claim (full: label, proposition, tags)
            - add_argument (full: label, gist, premises, conclusion, tags)
            - connect (full: source, target, relation_type, target_premise_idx, grounding_strategy)
            - edit (full)
            - remove (full)
            - inspect_node (full)
            - *All shared tools*
        
        **Review Mode** (validation):
            - validate (full: fix, max_issues)
            - inspect_node (full)
            - *All shared tools*
        
        **Shared Tools** (all modes):
            - get_instructions
            - inspect_graph
            - inspect_neighborhood
            - set_mode
    
    Registration Pattern:
        Each tool variant is registered with:
        
        - ``fn``: The actual function to call
        - ``name``: External name exposed to clients (e.g., "add_argument")
        - ``internal_name``: Internal identifier (e.g., "add_argument_sketch")
        - ``modes``: List of modes where this variant is available
        - ``description``: User-facing description of what the tool does
    
    Notes:
        - Tools with the same ``name`` but different ``modes`` create variants
          that swap when modes change.
        - Tools with ``modes=["sketch", "elaborate", "review"]`` are shared across
          all modes and never swapped.
        - This function is idempotent and safe to call multiple times (though
          currently only called once at module import).
    
    Example:
        A tool with mode-specific variants::
        
            # Sketch variant
            TOOL_REGISTRY.register_variant(ToolVariant(
                fn=add_argument_sketch,
                name="add_argument",        # Same name
                internal_name="add_argument_sketch",
                modes=["sketch"],
                description="Add argument (sketch mode - gist only)"
            ))
            
            # Elaborate variant
            TOOL_REGISTRY.register_variant(ToolVariant(
                fn=add_argument_elaborate,
                name="add_argument",        # Same name
                internal_name="add_argument_elaborate",
                modes=["elaborate"],
                description="Add argument (elaborate mode - full structure)"
            ))
    """
    
    # add_claim variants (sketch and elaborate)
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=add_claim_sketch,
        name="add_claim",
        internal_name="add_claim_sketch",
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
        )
    ))
    
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=add_claim_elaborate,
        name="add_claim",
        internal_name="add_claim_elaborate",
        modes=["elaborate"],
        description=dedent(
            """Add a new claim node to your argumentation graph.

            A claim represents a single proposition. By adding a claim, you're not ascertaining its
            truth, but rather introducing it as a point for discussion within your argument map.
            Claims are also useful for highlighting shared premises among multiple arguments.
            Try to keep claims clear, unambiguous, and focused on a single idea. Provide a succinct 
            and informative label that captures the essence of the claim and helps you to refer to
            it easily later on. You can also optionally add tags to categorize or annotate the claim.

            Args:
                label: Succinct and informative title for the claim (serving as unique identifier).
                proposition: The content of the claim (what is being asserted).
                tags: Optional list of tags for the claim (e.g., "important", "to-review").
            """
        )
    ))
    
    # add_argument variants (sketch and elaborate)
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=add_argument_sketch,
        name="add_argument",
        internal_name="add_argument_sketch",
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
        )
    ))
    
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=add_argument_elaborate,
        name="add_argument",
        internal_name="add_argument_elaborate",
        modes=["elaborate"],
        description=dedent(
            """Add a new argument node to your argumentation graph.

            An argument consists of a set of premises that jointly support the conclusion.
            
            Besides premises and conclusion, you can provide a 'gist' that summarizes the key idea of 
            the argument. Be clear and concise in your descriptions. Provide a succinct and 
            informative label that captures the essence of the argument and helps you to refer to it 
            easily later on.

            By adding an argument, you're not necessarily asserting its premises or conclusion as true.

            Args:
                label: Succinct and informative title for the argument (serving as unique identifier).
                gist: A brief summary of the argument's key idea.
                conclusion: The main claim that the argument is supporting or attacking.
                premises: List of premises supporting the conclusion.
                tags: Optional list of tags for the argument (e.g., "needs-backup", "to-review").
            """
        )
    ))
    
    # connect variants (sketch and elaborate)
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=connect_sketch,
        name="connect",
        internal_name="connect_sketch",
        modes=["sketch"],
        description=dedent(
            """Connect two nodes in your argumentation graph

            Args:
                source: Label of the source node (argument or claim).
                target: Label of the target node (argument or claim).
                relation_type: Type of relation ("supports" or "attacks").            
            """
        )
    ))
    
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=connect_elaborate,
        name="connect",
        internal_name="connect_elaborate",
        modes=["elaborate"],
        description=dedent(
            """Connect two nodes in your argumentation graph and optionally ground the dialectical relation.

            A dialectical relation (support or attack) is grounded in case it reflects the actual structure of the
            adjacent nodes. Available grounding strategies are

            for `support` relations:

                'define_equivalence': The conclusion of the supporting argument is defined as equivalent to the
                premise (target_premise_idx) of the supported argument.
                'copy_premise': A copy of the premise (target_premise_idx) of the supported argument is used as
                conclusion of the supporting argument.
                'copy_conclusion': A copy of the conclusion of the supporting argument is used as premise of the
                supported argument.

            for `attack` relations:

                'define_negation': The conclusion of the attacking argument is defined as the negation of the
                premise (target_premise_idx) of the attacked argument.
                'negate_premise': A negation of the premise (target_premise_idx) of the attacked argument is used
                as conclusion of the attacking argument.
                'negate_conclusion': The negation of the conclusion of the attacking argument is used as premise
                of the attacked argument.

            Args:
                source: Label of the source node (argument or claim).
                target: Label of the target node (argument or claim).
                relation_type: Type of relation ("supports" or "attacks").
                target_premise_idx: (For arguments as targets) Index of the premise being supported/attacked.
                grounding_strategy: Strategy for grounding the relation .
            """
        )
    ))
    
    # edit - elaborate mode only
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=edit,
        name="edit",
        internal_name="edit",
        modes=["elaborate"],
        description=dedent("""Edit an existing node in the argument map.

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
                )"""
        )
    ))
    
    # remove - sketch and elaborate modes
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=remove,
        name="remove",
        internal_name="remove",
        modes=["sketch", "elaborate"],
        description=dedent(
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
        )
    ))
    
    # inspect_node - elaborate and review modes
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=inspect_node,
        name="inspect_node",
        internal_name="inspect_node",
        modes=["elaborate", "review"],
        description=dedent(
            """Show detailed information about a specific node in the argument map.
            
            Args:
                label: The label of the node to inspect.
            """
        )
    ))
    
    # validate - review mode only
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=validate,
        name="validate",
        internal_name="validate",
        modes=["review"],
        description="Validate the current argument map for consistency and completeness"
    ))

    # get_instruction - sketch, elaborate and review modes
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=get_instructions_elaborate,
        name="get_instructions",
        internal_name="get_instructions_elaborate",
        modes=["elaborate"],
        description=dedent(
            """Show general advice or detailed topic-specific instructions for how to elaborate an argumentation graph.

            Args:
                topic: Specific topic to get instructions for ("grounding" or "validity"). Defaults to None for general instructions.
            """)
    ))
    TOOL_REGISTRY.register_variant(ToolVariant(
        fn=get_instructions,
        name="get_instructions",
        internal_name="get_instructions",
        modes=["sketch", "review"],
        description="Show instructions and usage hints for current mode"
    ))

    
    # Shared tools (all modes)
    for shared_tool_fn, tool_name, description in [
        (inspect_graph, "inspect_graph", "Show an overview of the argumentation graph"),
        (inspect_neighborhood, "inspect_neighborhood", "Show k-neighborhood of a node"),
        (set_mode, "set_mode", "Switch the argument map editing mode"),
    ]:
        TOOL_REGISTRY.register_variant(ToolVariant(
            fn=cast(Callable[..., Any], shared_tool_fn),
            name=tool_name,
            internal_name=tool_name,
            modes=["sketch", "elaborate", "review"],
            description=description
        ))


# Register all tool variants on module load
_register_tool_variants()
