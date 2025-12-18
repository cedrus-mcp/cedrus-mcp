"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from typing import Literal

from mcp.types import CallToolResult

from koala.graph.argument_map import ArgumentMap
from koala.models import (
    NodeLabel,
)
from koala.tools.tool_context import ToolContext
from koala.tools import utils
from koala.tools.grounding import maybe_ground_relation


def new_support_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    target_premise_idx: int | None,
    grounding_strategy: Literal["define_equivalence", "copy_premise", "copy_conclusion"]
    | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Create a new support relation.

    Creates new support relation between two existing nodes. Optionally grounds the relation
    according to the specified strategy, e.g. by adding premises or conclusions.

    Args:
        from_label: The label of the source node.
        to_label: The label of the target node.
        target_premise_idx: If specified, the index of the premise to target for grounding, requires to_label to be an ArgumentNode.
        grounding_strategy: The strategy to use for grounding the relation.
    Returns:
        Textual feedback and next step suggestions.
    """

    if not arg_map.is_node(from_label):
        return tc.failure(
            f"Source node '{from_label}' does not exist.",
            error="NonExistentNode",
        ).build()
    if not arg_map.is_node(to_label):
        return tc.failure(
            f"Target node '{to_label}' does not exist.",
            error="NonExistentNode",
        ).build()
    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is not None:
        return tc.failure(
            f"A {rel.relation_type}-relation from '{from_label}' to '{to_label}' already exists.",
            error="RelationAlreadyExists",
        ).build()

    if target_premise_idx is not None and not utils.validate_target_premise_idx(
        to_label, target_premise_idx, arg_map
    ):
        tc.issue(
            "warning",
            f"Invalid target premise index {target_premise_idx} for argument '{to_label}'. Will ignore target premise.",
        )
        target_premise_idx = None

    arg_map.add_support_relation(from_label, to_label, target_premise_idx=target_premise_idx)

    success = True
    if grounding_strategy is not None:
        success = maybe_ground_relation(
            from_label, to_label, "support", target_premise_idx, grounding_strategy, arg_map, tc
        )
    if success:
        tc.success(f"✓ Support relation created from '{from_label}' to '{to_label}'.")

    return tc.build()


def new_attack_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    target_premise_idx: int | None,
    grounding_strategy: Literal["define_negation", "negate_premise", "negate_conclusion"] | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Create a new attack relation.
    
    Creates new attack relation between two existing nodes. Optionally grounds the relation
    according to the specified strategy, e.g. by adding premises or conclusions.

    Args:
        from_label: The label of the source node.
        to_label: The label of the target node.
        target_premise_idx: If specified, the index of the premise to target for grounding, requires to_label to be an ArgumentNode.
        grounding_strategy: The strategy to use for grounding the relation.
    Returns:
        Textual feedback and next step suggestions.    
    """

    if not arg_map.is_node(from_label):
        return tc.failure(
            f"Source node '{from_label}' does not exist.",
            error="NonExistentNode",
        ).build()
    if not arg_map.is_node(to_label):
        return tc.failure(
            f"Target node '{to_label}' does not exist.",
            error="NonExistentNode",
        ).build()
    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is not None:
        return tc.failure(
            f"A {rel.relation_type}-relation from '{from_label}' to '{to_label}' already exists.",
            error="RelationAlreadyExists",
        ).build()

    if target_premise_idx is not None and not utils.validate_target_premise_idx(
        to_label, target_premise_idx, arg_map
    ):
        tc.issue(
            "warning",
            f"Invalid target premise index {target_premise_idx} for argument '{to_label}'. Will ignore target premise.",
        )
        target_premise_idx = None

    arg_map.add_attack_relation(from_label, to_label, target_premise_idx=target_premise_idx)

    success = True
    if grounding_strategy is not None:
        success = maybe_ground_relation(
            from_label, to_label, "attack", target_premise_idx, grounding_strategy, arg_map, tc
        )
    if success:
        tc.success(f"✓ Attack relation created from '{from_label}' to '{to_label}'.")

    return tc.build()

def ground_support_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    strategy: Literal["define_equivalence", "copy_premise", "copy_conclusion"],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Ground an existing support relation.
    
    Grounds an existing support relation according to the specified strategy.
    
    Args:
        from_label: The label of the source node.
        to_label: The label of the target node.
        strategy: The strategy to use for grounding the relation.
    Returns:
        Textual feedback and next step suggestions.
    """

    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is None:
        return tc.failure(
            f"No relation exists from '{from_label}' to '{to_label}'.",
            error="NonExistentRelation",
        ).build()
    if rel.relation_type != "support":
        return tc.failure(
            f"The relation from '{from_label}' to '{to_label}' is not a support relation.",
            error="InvalidRelationType",
        ).build()

    success = utils.maybe_ground_relation(
        from_label, to_label, "support", rel.target_premise_idx, strategy, arg_map, tc
    )
    if success:
        tc.success(f"✓ Support relation from '{from_label}' to '{to_label}' grounded using strategy '{strategy}'.")

    return tc.build()


def ground_attack_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    strategy: Literal["define_negation", "negate_premise", "negate_conclusion"],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Ground an existing attack relation.
    
    Grounds an existing attack relation according to the specified strategy.
    
    Args:
        from_label: The label of the source node.
        to_label: The label of the target node.
        ctx: The context of the call.
        strategy: The strategy to use for grounding the relation.
    Returns:
        Textual feedback and next step suggestions.
    """
    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is None:
        return tc.failure(
            f"No relation exists from '{from_label}' to '{to_label}'.",
            error="NonExistentRelation",
        ).build()
    if rel.relation_type != "attack":
        return tc.failure(
            f"The relation from '{from_label}' to '{to_label}' is not an attack relation.",
            error="InvalidRelationType",
        ).build()

    success = utils.maybe_ground_relation(
        from_label, to_label, "attack", rel.target_premise_idx, strategy, arg_map, tc
    )
    if success:
        tc.success(f"✓ Attack relation from '{from_label}' to '{to_label}' grounded using strategy '{strategy}'.")

    return tc.build()


def delete_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete an existing dialectical relation.
    
    Deletes an existing dialectical relation between two nodes.

    Args:
        from_label: The label of the source node.
        to_label: The label of the target node.
    Returns:
        Textual feedback and next step suggestions.
    """
    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is None:
        return tc.failure(
            f"No relation exists from '{from_label}' to '{to_label}'.",
            error="NonExistentRelation",
        ).build()

    arg_map.delete_relation(from_label, to_label)

    return tc.success(f"✓ {rel.relation_type.capitalize()} relation deleted from '{from_label}' to '{to_label}'.").build()

