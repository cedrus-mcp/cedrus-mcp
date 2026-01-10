"""Relation-level operations for the argument map.

This module groups helpers for creating, grounding, and deleting
support/attack relations, as well as review flagging utilities
for relations and nodes.
"""

from __future__ import annotations

from typing import Literal

from mcp.types import CallToolResult

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models import NodeLabel
from cedrus.backend.models.base import PropositionID
from cedrus.tools.adapters.grounding import maybe_ground_relation
from cedrus.tools.runtime.tool_context import ToolContext
from cedrus.tools.util import validate_target_premise_idx


def new_support_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    target_premise_idx: int | None,
    grounding_strategy: Literal["define_equivalence", "copy_premise", "copy_conclusion"] | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Create a new support relation.

    Direct move of :func:`cedrus.tools.adapters.relations.new_support_relation`.
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

    if target_premise_idx is not None and not validate_target_premise_idx(
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

    Direct move of :func:`cedrus.tools.adapters.relations.new_attack_relation`.
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

    if target_premise_idx is not None and not validate_target_premise_idx(
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

    Direct move of :func:`cedrus.tools.adapters.relations.ground_support_relation`.
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

    success = maybe_ground_relation(
        from_label, to_label, "support", rel.target_premise_idx, strategy, arg_map, tc
    )
    if success:
        tc.success(
            f"✓ Support relation from '{from_label}' to '{to_label}' grounded using strategy '{strategy}'."
        )

    return tc.build()


def ground_attack_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    strategy: Literal["define_negation", "negate_premise", "negate_conclusion"],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Ground an existing attack relation.

    Direct move of :func:`cedrus.tools.adapters.relations.ground_attack_relation`.
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

    success = maybe_ground_relation(
        from_label, to_label, "attack", rel.target_premise_idx, strategy, arg_map, tc
    )
    if success:
        tc.success(
            f"✓ Attack relation from '{from_label}' to '{to_label}' grounded using strategy '{strategy}'."
        )

    return tc.build()


def delete_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete an existing dialectical relation.

    Direct move of :func:`cedrus.tools.adapters.relations.delete_relation`.
    """
    if (rel := arg_map.get_dialectic_relation(from_label, to_label)) is None:
        return tc.failure(
            f"No relation exists from '{from_label}' to '{to_label}'.",
            error="NonExistentRelation",
        ).build()

    arg_map.delete_relation(from_label, to_label)

    return tc.success(
        f"✓ {rel.relation_type.capitalize()} relation deleted from '{from_label}' to '{to_label}'."
    ).build()


def flag_relations_as_needing_review(
    ref_node_label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Flag all relations connected to a node as needing review.

    Direct move of :func:`cedrus.tools.adapters.relations.flag_relations_as_needing_review`.
    """

    supporters = arg_map.get_supporters(ref_node_label)
    attackers = arg_map.get_attackers(ref_node_label)
    supported = arg_map.get_supported(ref_node_label)
    attacked = arg_map.get_attacked(ref_node_label)

    for from_label in supporters + attackers:
        arg_map.update_relation(
            from_label,
            ref_node_label,
            {"needs_review_flag": True},
        )
    for to_label in supported + attacked:
        arg_map.update_relation(
            ref_node_label,
            to_label,
            {"needs_review_flag": True},
        )

    total_flagged = len(supporters) + len(attackers) + len(supported) + len(attacked)
    if total_flagged > 0:
        tc.issue(
            "info",
            f"Flagged {total_flagged} dialectical relation(s) connected to node `{ref_node_label}` as needing review.",
            priority=1.0,
        )


def flag_nodes_as_needing_review(
    ref_prop_id: PropositionID,
    exempt_nodes_flagging: list[NodeLabel],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Flag all nodes referencing a proposition as needing review.

    Direct move of :func:`cedrus.tools.adapters.relations.flag_nodes_as_needing_review`.
    """

    nodes_requiring_review: list[NodeLabel] = [
        node.label
        for node in arg_map.list_claims()
        if ref_prop_id == node.proposition_id and node.label not in exempt_nodes_flagging
    ] + [
        node.label
        for node in arg_map.list_arguments()
        if ref_prop_id in node.premises + [node.conclusion]
        and node.label not in exempt_nodes_flagging
    ]

    for node_label in nodes_requiring_review:
        arg_map.update_node(node_label, {"needs_review_flag": True})

    if nodes_requiring_review:
        tc.issue(
            "info",
            f"Flagged {len(nodes_requiring_review)} node(s) as needing review due to proposition update: {', '.join(nodes_requiring_review)}",
            priority=1.0,
        )


__all__ = [
    "new_support_relation",
    "new_attack_relation",
    "ground_support_relation",
    "ground_attack_relation",
    "delete_relation",
    "flag_relations_as_needing_review",
    "flag_nodes_as_needing_review",
]
