"""Grounding logic for dialectical relations."""

from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from koala.graph import ArgumentMap
from koala.models import ClaimNode, NodeLabel, Proposition
from koala.models.relations import DialecticalRelationType
from koala.utils.relations import is_grounded_relation


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


def validate_grounding_strategy(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    grounding_strategy: GroundingStrategy | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> bool:
    """Validate that a grounding strategy is applicable.
    
    Args:
        from_label: Source node label
        to_label: Target node label
        relation_type: Type of relation
        target_premise_idx: Optional premise index
        grounding_strategy: The grounding strategy to validate
        arg_map: The argument map
        tc: Tool context for logging issues
        
    Returns:
        True if strategy is valid, False otherwise
    """
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
    """Ground a dialectical relation according to the specified strategy.
    
    Args:
        from_label: Source node label
        to_label: Target node label
        relation_type: Type of relation
        target_premise_idx: Optional premise index
        grounding_strategy: Strategy to use for grounding
        arg_map: The argument map
        tc: Tool context for logging
        
    Returns:
        True if grounding succeeded, False otherwise
    """
    if is_grounded_relation(from_label, to_label, relation_type, arg_map):
        tc.issue("info", f"Dialectical relation (`{relation_type}`) created is already grounded.")
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
                tc.issue("info", 
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
                tc.issue("info", 
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
                    tc.issue("info", 
                        "Grounded support relation by using target proposition as source claim's proposition."
                    )
                else:
                    arg_map.update_node(source_node.label, {"conclusion": to_prop_id})
                    tc.issue("info", 
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
                    tc.issue("info", 
                        "Grounded attack relation by using negated target proposition as source claim's proposition."
                    )
                else:
                    arg_map.update_node(source_node.label, {"conclusion": neg_to_prop.id})
                    tc.issue("info", 
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
                    tc.issue("info", 
                        "Grounded support relation by using source proposition as target claim's proposition."
                    )
                else:
                    arg_map.update_node(
                        target_node.label, {"premises": target_node.premises + [from_prop_id]}
                    )
                    tc.issue("info", 
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
                    tc.issue("info", 
                        "Grounded attack relation by using negated source proposition as target claim's proposition."
                    )
                else:
                    arg_map.update_node(target_node.label, {"conclusion": neg_from_prop.id})
                    tc.issue("info", 
                        "Grounded attack relation by using negated source proposition as target argument's conclusion."
                    )
                return True
            case _:
                tc.failure(f"Unknown grounding strategy: {grounding_strategy}")
                return False
    except Exception as e:
        tc.failure(f"Failed to ground support relation: {str(e)}")
        return False
