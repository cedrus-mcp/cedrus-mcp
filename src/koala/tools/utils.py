# koala/tools.utils.py
"""Utility functions for MCP tools."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

from mcp.server.fastmcp.utilities.logging import get_logger

from koala.graph import ArgumentMap
from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
    Proposition,
)
from koala.models.base import PropositionID
from koala.models.relations import DialecticalRelationType

if TYPE_CHECKING:
    from koala.tools.tool_context import ToolContext

GroundingStrategy = Literal[
    "define_negation",
    "define_equivalence",
    "copy_premise",
    "negate_premise",
    "copy_conclusion",
    "negate_conclusion",
]

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


def is_grounded_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
) -> bool:
    rel = arg_map.get_dialectic_relation(from_label, to_label)
    if rel is None:
        return False
    source_node = arg_map.get_node(from_label)
    target_node = arg_map.get_node(to_label)
    source_prop_id = (
        source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
    )
    target_prop_ids = (
        [target_node.proposition_id] if isinstance(target_node, ClaimNode) else target_node.premises
    )

    if relation_type == "support":
        return any(arg_map.are_equivalent(source_prop_id, pid) for pid in target_prop_ids)
    elif relation_type == "attack":
        return any(arg_map.are_contradictory(source_prop_id, pid) for pid in target_prop_ids)
    else:
        logger.error(f"Unknown relation type: {relation_type}")
        return False


def flag_relations_as_needing_review(
    ref_node_label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
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
        tc.note(
            f"Flagged {total_flagged} dialectical relation(s) connected to node `{ref_node_label}` as needing review.",
            priority=1.0,
        )


def flag_nodes_as_needing_review(
    ref_prop_id: PropositionID,
    exempt_nodes_flagging: list[NodeLabel],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Flag all nodes referencing the given proposition as needing review, except those in exempt_nodes_flagging."""
    nodes_requiring_review: list[NodeLabel] = [
        node.label
        for node in arg_map.list_arguments()
        if ref_prop_id in node.premises or ref_prop_id == node.conclusion
    ] + [node.label for node in arg_map.list_claims() if ref_prop_id == node.proposition_id]
    nodes_requiring_review = [
        node_label
        for node_label in nodes_requiring_review
        if node_label not in exempt_nodes_flagging
    ]
    for node_label in nodes_requiring_review:
        arg_map.update_node(
            node_label,
            {"needs_review_flag": True},
        )

    tc.note(
        f"Flagged {len(nodes_requiring_review)} node(s) referencing updated proposition as needing review: {', '.join(nodes_requiring_review)}.",
        priority=1.0,
    )


def update_proposition(
    prop_id: str,
    updates: dict[str, Any],
    exempt_nodes_flagging: list[str],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Update a proposition in the argument map. And flag all nodes referencing it as needing review."""

    if not updates:
        return
    if not arg_map.is_proposition(prop_id):
        logger.error(f"Proposition with id '{prop_id}' does not exist.")
        return

    if "content" in updates:
        updates["is_dummy"] = False
    arg_map.update_proposition(prop_id, updates)
        
    flag_nodes_as_needing_review(
        ref_prop_id=prop_id,
        exempt_nodes_flagging=exempt_nodes_flagging,
        arg_map=arg_map,
        tc=tc,
    )


def ensure_label_is_unique(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> NodeLabel:
    """
    Ensure that the given label is unique in the argument map. If not, generate a unique label,
    append a note to tc, add an issue and a next action suggestion.
    Return the (possibly new) unique label.
    """

    new_label = arg_map.maybe_make_unique_label(label)
    if new_label == label:
        return label

    tc.note(
        f"Note: Label '{label}' is already in use. Creating unique label '{new_label}'.",
        priority=1.0,
    )
    label = new_label

    msg = f"Label '{label}' has been created automatically to ensure uniqueness and may need revision."
    tc.issue(severity="warning", message=msg, field="label")
    return label


def sanitize_relation_args_new_node(
    to_label: NodeLabel | None,
    from_label: NodeLabel | None,
    target_premise_idx: int | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> tuple[NodeLabel | None, NodeLabel | None, int | None]:
    # Make sure only one relation is created
    if to_label and from_label:
        from_label = None  # Can't have both
        tc.note(
            "Note: Both 'to_label' and 'from_label' were provided. Will ignore 'from_label'.",
            priority=1.0,
        )

    # Check if to_label / from_label exist
    if to_label is not None and arg_map.is_node(to_label) is False:
        msg = f"Target node `{to_label}` does not exist in the argument map. Will create node without relation."
        tc.note(f"Warning: {msg}", priority=1.0)
        to_label = None
    if from_label is not None and arg_map.is_node(from_label) is False:
        msg = f"Source node `{from_label}` does not exist in the argument map. Will create node without relation."
        tc.note(f"Warning: {msg}", priority=1.0)
        from_label = None

    # Validate target_premise_idx
    if target_premise_idx is not None and (
        not to_label or not validate_target_premise_idx(to_label, target_premise_idx, arg_map)
    ):
        msg = f"No premise at index {target_premise_idx} in target argument `{to_label}`. Ignoring `target_premise_idx`."
        tc.note(f"Warning: {msg}", priority=1.0)
        target_premise_idx = None

    return to_label, from_label, target_premise_idx


def validate_target_premise_idx(
    label: NodeLabel,
    target_premise_idx: int | None,
    arg_map: ArgumentMap,
) -> bool:
    if target_premise_idx is None:
        return False
    if not arg_map.is_node(label):
        return False
    node = arg_map.get_node(label)
    if not isinstance(node, ArgumentNode):
        return False
    if target_premise_idx <= 0 or target_premise_idx > len(node.premises):
        return False
    return True


def validate_grounding_strategy(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    grounding_strategy: GroundingStrategy | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> bool:
    if grounding_strategy is None:
        return False
    if (
        grounding_strategy in ["define_equivalence", "copy_premise", "copy_conclusion"]
        and relation_type != "support"
    ):
        tc.issue(
            "warning",
            "Grounding strategies `define_equivalence`, `copy_premise`, and `copy_conclusion` are only applicable to `support` relations. Ignoring grounding.",
        )
        return False
    if (
        grounding_strategy in ["define_negation", "negate_premise", "negate_conclusion"]
        and relation_type != "attack"
    ):
        tc.issue(
            "warning",
            "Grounding strategies `define_negation`, `negate_premise`, and `negate_conclusion` are only applicable to `attack` relations. Ignoring grounding.",
        )
        return False
    if not arg_map.is_node(from_label) or not arg_map.is_node(to_label):
        return False
    source_node = arg_map.get_node(from_label)
    target_node = arg_map.get_node(to_label)
    source_prop_id = (
        source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
    )
    target_prop_id = ""
    if isinstance(target_node, ClaimNode):
        target_prop_id = target_node.proposition_id
    else:
        if target_premise_idx is not None and 0 < target_premise_idx <= len(target_node.premises):
            target_prop_id = target_node.premises[target_premise_idx - 1]

    match grounding_strategy:
        case "define_negation" | "define_equivalence":
            if not arg_map.is_proposition(source_prop_id):
                tc.issue(
                    "warning",
                    f"Grounding strategy `{grounding_strategy}` requires source node '{from_label}' to have a proposition / conclusion.",
                )
                return False
            if not arg_map.is_proposition(target_prop_id):
                tc.issue(
                    "warning",
                    f"Grounding strategy `{grounding_strategy}` requires target node '{to_label}' to have a proposition / premise at index {target_premise_idx}.",
                )
                return False
        case "copy_premise" | "negate_premise":
            if not arg_map.is_proposition(target_prop_id):
                tc.issue(
                    "warning",
                    f"Grounding strategy `copy_premise` requires target node '{to_label}' to have a proposition / premise at index ({target_premise_idx}).",
                )
                return False
        case "copy_conclusion" | "negate_conclusion":
            if not arg_map.is_proposition(source_prop_id):
                tc.issue(
                    "warning",
                    f"Grounding strategy `copy_conclusion` requires source node '{from_label}' to have a proposition / conclusion.",
                )
                return False
    return True


def maybe_ground_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    grounding_strategy: GroundingStrategy | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> bool:
    if is_grounded_relation(from_label, to_label, relation_type, arg_map):
        tc.note("Dialectical relation (`{relation_type}`) created is already grounded.")
        return True

    if not validate_grounding_strategy(
        from_label, to_label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
    ):
        return False

    target_node = arg_map.get_node(to_label)
    source_node = arg_map.get_node(from_label)
    try:
        match grounding_strategy:
            case "define_equivalence":
                to_prop_id = (
                    target_node.proposition_id
                    if isinstance(target_node, ClaimNode)
                    else target_node.premises[target_premise_idx or 0]
                )
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )
                arg_map.add_equivalence(from_prop_id, to_prop_id)
                tc.note(
                    "Grounded support relation by defining equivalence between target and sourcepropositions."
                )
                return True
            case "define_negation":
                to_prop_id = (
                    target_node.proposition_id
                    if isinstance(target_node, ClaimNode)
                    else target_node.premises[target_premise_idx or 0]
                )
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )
                arg_map.add_negation(from_prop_id, to_prop_id)
                tc.note(
                    "Grounded attack relation by defining negation between target and source propositions."
                )
                return True
            case "copy_premise":
                to_prop_id = (
                    target_node.proposition_id
                    if isinstance(target_node, ClaimNode)
                    else target_node.premises[target_premise_idx or 0]
                )
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )  # may be empty
                if isinstance(source_node, ClaimNode):
                    arg_map.update_node(source_node.label, {"proposition_id": to_prop_id})
                    tc.note(
                        "Grounded support relation by using target proposition as source claim's proposition."
                    )
                else:
                    arg_map.update_node(source_node.label, {"conclusion": to_prop_id})
                    tc.note(
                        "Grounded support relation by using target proposition to source argument's conclusion."
                    )
                if from_prop_id:
                    arg_map.maybe_remove_unused_proposition(from_prop_id)
                return True
            case "negate_premise":
                to_prop_id = (
                    target_node.proposition_id
                    if isinstance(target_node, ClaimNode)
                    else target_node.premises[target_premise_idx or 0]
                )
                to_prop = arg_map.get_proposition(to_prop_id)
                if to_prop is None:
                    tc.failure(
                        f"Failed to retrieve premise proposition at ({target_premise_idx}) for grounding."
                    )
                    return False
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )  # may be empty
                neg_to_prop = next(arg_map.get_negation_of(to_prop_id), None)
                if neg_to_prop is None:
                    neg_to_prop = Proposition(
                        content=arg_map.negate_proposition_content(to_prop.content)
                    )
                    arg_map.add_proposition(neg_to_prop)
                if isinstance(source_node, ClaimNode):
                    arg_map.update_node(source_node.label, {"proposition_id": neg_to_prop.id})
                    tc.note(
                        "Grounded attack relation by using negated target proposition as source claim's proposition."
                    )
                else:
                    arg_map.update_node(source_node.label, {"conclusion": neg_to_prop.id})
                    tc.note(
                        "Grounded attack relation by using negated target proposition as source argument's conclusion."
                    )
                return True
            case "copy_conclusion":
                to_prop_id = (
                    target_node.proposition_id if isinstance(target_node, ClaimNode) else ""
                )
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )
                if isinstance(target_node, ClaimNode):
                    arg_map.update_node(target_node.label, {"proposition_id": from_prop_id})
                    tc.note(
                        "Grounded support relation by using source proposition as target claim's proposition."
                    )
                else:
                    arg_map.update_node(
                        target_node.label, {"premises": target_node.premises + [from_prop_id]}
                    )
                    tc.note(
                        "Grounded support relation by adding source proposition to target argument's premises."
                    )
                return True
            case "negate_conclusion":
                to_prop_id = (
                    target_node.proposition_id if isinstance(target_node, ClaimNode) else ""
                )
                from_prop_id = (
                    source_node.proposition_id
                    if isinstance(source_node, ClaimNode)
                    else source_node.conclusion
                )
                neg_from_prop = next(arg_map.get_negation_of(from_prop_id), None)
                if neg_from_prop is None:
                    from_prop = arg_map.get_proposition(from_prop_id)
                    if from_prop is None:
                        tc.failure("Failed to retrieve source proposition for grounding.")
                        return False
                    neg_from_prop = Proposition(
                        content=arg_map.negate_proposition_content(from_prop.content)
                    )
                    arg_map.add_proposition(neg_from_prop)
                if isinstance(target_node, ClaimNode):
                    arg_map.update_node(target_node.label, {"proposition_id": neg_from_prop.id})
                    tc.note(
                        "Grounded attack relation by using negated source proposition as target claim's proposition."
                    )
                else:
                    arg_map.update_node(target_node.label, {"conclusion": neg_from_prop.id})
                    tc.note(
                        "Grounded attack relation by using negated source proposition as target argument's conclusion."
                    )
                return True
            case _:
                tc.failure(f"Unknown grounding strategy: {grounding_strategy}")
                return False
    except Exception as e:
        tc.failure(f"Failed to ground support relation: {str(e)}")
        return False


def maybe_create_proposition_from_content(
    ref_node_label: NodeLabel,
    proposition_content: str | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> Proposition:
    proposition_node = next(arg_map.find_proposition_by_content(proposition_content or ""), None)
    if proposition_node:
        return proposition_node

    is_dummy = False
    if not proposition_content:
        # fix proposition_content
        proposition_content = (
            f"Content of proposition in `{ref_node_label}` ... (to be filled in later)"
        )
        is_dummy = True

    proposition_node = Proposition(content=proposition_content, is_dummy=is_dummy)
    arg_map.add_proposition(proposition_node)

    return proposition_node
