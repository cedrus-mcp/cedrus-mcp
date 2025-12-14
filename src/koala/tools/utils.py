# koala/tools.utils.py
"""Utility functions for MCP tools."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
from textwrap import shorten

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
    source_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
    target_prop_ids = [target_node.proposition_id] if isinstance(target_node, ClaimNode) else target_node.premises

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
    tc.suggest(
        tool="update_claim",
        params={"label": label, "field": "label", "new_value": "REVISED_LABEL_HERE"},
        reason="Revisit and revise the automatically generated unique label if needed.",
        action_type="improve",
    )
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
        msg = f"Target node `{to_label}` does not exist in the argument map. Will create claim without relation."
        tc.note(f"Warning: {msg}", priority=1.0)
        to_label = None
    if from_label is not None and arg_map.is_node(from_label) is False:
        msg = f"Source node `{from_label}` does not exist in the argument map. Will create claim without relation."
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
    grounding_strategy: Literal["define_negation", "define_equivalence", "copy_premise", "copy_conclusion"]
    | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> bool:
    if grounding_strategy is None:
        return False
    if grounding_strategy == "define_equivalence" and relation_type != "support":
        tc.issue(
            "warning",
            "Grounding strategy `define_equivalence` is only applicable to `support` relations. Ignoring grounding.",
        )
        return False
    if grounding_strategy == "define_negation" and relation_type != "attack":
        tc.issue(
            "warning",
            "Grounding strategy `define_negation` is only applicable to `attack` relations. Ignoring grounding.",
        )
        return False
    if not arg_map.is_node(from_label) or not arg_map.is_node(to_label):
        return False
    source_node = arg_map.get_node(from_label)
    target_node = arg_map.get_node(to_label)
    source_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
    target_prop_id = ""
    if isinstance(target_node, ClaimNode):
        target_prop_id = target_node.proposition_id
    else:
        if target_premise_idx is not None and 0 < target_premise_idx <= len(target_node.premises):
            target_prop_id = target_node.premises[target_premise_idx -1]

    match grounding_strategy:
        case "define_negation" | "define_equivalence":
            if not arg_map.is_proposition(source_prop_id):
                tc.issue("warning", f"Grounding strategy `{grounding_strategy}` requires source node '{from_label}' to have a proposition / conclusion.")
                return False
            if not arg_map.is_proposition(target_prop_id):
                tc.issue("warning", f"Grounding strategy `{grounding_strategy}` requires target node '{to_label}' to have a proposition / premise at index {target_premise_idx}.")
                return False
        case "copy_premise":
            if not arg_map.is_proposition(target_prop_id):
                tc.issue("warning", f"Grounding strategy `copy_premise` requires target node '{to_label}' to have a proposition / premise at index ({target_premise_idx}).")
                return False
        case "copy_conclusion":
            if not arg_map.is_proposition(source_prop_id):
                tc.issue("warning", f"Grounding strategy `copy_conclusion` requires source node '{from_label}' to have a proposition / conclusion.")
                return False
    return True

def maybe_ground_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    grounding_strategy: Literal["define_negation", "define_equivalence", "copy_premise", "copy_conclusion"]
    | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> bool:
    if is_grounded_relation(
        from_label, to_label, relation_type, arg_map
    ):
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
                to_prop_id = target_node.proposition_id if isinstance(target_node, ClaimNode) else target_node.premises[target_premise_idx or 0] 
                from_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
                arg_map.add_equivalence(from_prop_id, to_prop_id)
                tc.note("Grounded support relation by defining equivalence between target and sourcepropositions.")
                return True
            case "define_negation":
                to_prop_id = target_node.proposition_id if isinstance(target_node, ClaimNode) else target_node.premises[target_premise_idx or 0]
                from_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
                arg_map.add_negation(from_prop_id, to_prop_id)
                tc.note("Grounded attack relation by defining negation between target and source propositions.")
                return True
            case "copy_premise":
                to_prop_id = target_node.proposition_id if isinstance(target_node, ClaimNode) else target_node.premises[target_premise_idx or 0]
                from_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion  # may be empty
                if isinstance(source_node, ClaimNode):
                    arg_map.update_node(source_node.label, {"proposition_id": to_prop_id})
                    tc.note("Grounded support relation by using target proposition as source claim's proposition.")
                else:
                    arg_map.update_node(source_node.label, {"conclusion": to_prop_id})
                    tc.note("Grounded support relation by using target proposition to source argument's conclusion.")
                if from_prop_id:
                    arg_map.maybe_remove_unused_proposition(from_prop_id)
                return True
            case "copy_conclusion":
                to_prop_id = target_node.proposition_id if isinstance(target_node, ClaimNode) else ""
                from_prop_id = source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
                if isinstance(target_node, ClaimNode):
                    arg_map.update_node(target_node.label, {"proposition_id": from_prop_id})
                    tc.note("Grounded support relation by using source proposition as target claim's proposition.")
                else:
                    arg_map.update_node(target_node.label, {"premises": target_node.premises + [from_prop_id]})
                    tc.note("Grounded support relation by adding source proposition to target argument's premises.")
                return True
            case _:
                tc.failure(f"Unknown grounding strategy: {grounding_strategy}")
                return False
    except Exception as e:
        tc.failure(f"Failed to ground support relation: {str(e)}")
        return False


def maybe_get_target_proposition(
    to_label: NodeLabel,
    target_premise_idx: int | None,
    arg_map: ArgumentMap,
) -> tuple[Proposition | None, str | None]:
    if arg_map.is_node(to_label) is False:
        msg = f"Target node `{to_label}` does not exist in the argument map."
        return None, msg
    to_node = arg_map.get_node(to_label)
    if isinstance(to_node, ArgumentNode) and target_premise_idx is not None:
        try:
            prop_id = to_node.premises[target_premise_idx]
            target_proposition = arg_map.get_proposition(prop_id)
        except IndexError:
            msg = f"Target premise index {target_premise_idx} is out of bounds for argument node `[{to_label}]`."
            return None, msg
    elif isinstance(to_node, ClaimNode):
        target_proposition = arg_map.get_proposition(to_node.proposition_id)
    else:
        logger.error(f"Node '{to_label}' is neither ArgumentNode nor ClaimNode.")
        raise ValueError(f"Node '{to_label}' is neither ArgumentNode nor ClaimNode.")
    return target_proposition, None


def maybe_get_source_proposition(
    from_label: NodeLabel,
    arg_map: ArgumentMap,
) -> tuple[Proposition | None, str | None]:
    if arg_map.is_node(from_label) is False:
        msg = f"Source node `{from_label}` does not exist in the argument map."
        return None, msg
    from_node = arg_map.get_node(from_label)
    if isinstance(from_node, ClaimNode):
        source_proposition = arg_map.get_proposition(from_node.proposition_id)
    elif isinstance(from_node, ArgumentNode):
        if not from_node.conclusion:
            return None, None
        source_proposition = arg_map.get_proposition(from_node.conclusion)
    else:
        logger.error(f"Node '{from_label}' is not a ClaimNode.")
        raise ValueError(f"Node '{from_label}' is not a ClaimNode.")
    return source_proposition, None


def maybe_get_ref_proposition_from_relation_args(
    to_label: NodeLabel | None,
    from_label: NodeLabel | None,
    target_premise_idx: int | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> Proposition | None:
    existing_proposition_node: Proposition | None = None
    msg = None
    if to_label:
        existing_proposition_node, msg = maybe_get_target_proposition(
            to_label, target_premise_idx, arg_map
        )
        msg = f"Will not ground relation to `{to_label}`: {msg}" if msg else None
    if from_label:
        existing_proposition_node, msg = maybe_get_source_proposition(from_label, arg_map)
        msg = f"Will not ground relation from `{from_label}`: {msg}" if msg else None
    if msg:
        tc.note(f"Warning: {msg}", priority=1.0)

    return existing_proposition_node


def get_claim_proposition_from_relation_args(
    new_label: NodeLabel,
    proposition_content: str | None,
    existing_ref_proposition_node: Proposition | None,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> Proposition:
    if existing_ref_proposition_node:
        if not proposition_content:
            if relation_type == "support":
                return existing_ref_proposition_node
            proposition_node = next(arg_map.get_negation_of(existing_ref_proposition_node.id), None)
            if proposition_node:
                return proposition_node
            # Automatically negate existing proposition
            proposition_content = arg_map.negate_proposition_content(
                existing_ref_proposition_node.content
            )
            tc.issue(
                severity="info",
                message=f"Automatically negating existing proposition '{shorten(existing_ref_proposition_node.content, width=40)}' as '{shorten(proposition_content, width=30)}'.",
                field="proposition",
            )
            tc.suggest(
                tool="update_claim",
                params={
                    "label": new_label,
                    "field": "proposition",
                    "new_value": "PROPOSITION_TEXT_HERE",
                },
                reason="Revise automatically negated proposition to express negation in plain language.",
                action_type="improve",
            )
        if (
            proposition_content
            and existing_ref_proposition_node.content.strip() == proposition_content.strip()
            and relation_type == "support"
        ):
            return existing_ref_proposition_node

        proposition_node = Proposition(content=proposition_content)
        arg_map.add_proposition(proposition_node)
        if relation_type == "support":
            arg_map.add_equivalence(existing_ref_proposition_node.id, proposition_node.id)
            tc.issue(
                severity="info",
                message=f"New proposition is automatically declared as equivalent to '{existing_ref_proposition_node.content}'.",
                field="proposition",
            )
        elif relation_type == "attack":
            arg_map.add_negation(existing_ref_proposition_node.id, proposition_node.id)
            tc.issue(
                severity="info",
                message=f"New proposition is NOT automatically declared as negation of '{existing_ref_proposition_node.content}'.",
                field="proposition",
            )
        return proposition_node

    # no existing_proposition_node:

    if not proposition_content:
        # fix proposition_content and add suggestion
        proposition_content = f"Content of claim `[{new_label}]` ... (to be filled in later)"
        msg = (
            f"Claim `[{new_label}]` created without proposition text. → Fill in proposition later."
        )
        tc.issue(severity="info", message=msg, field="proposition")
        tc.suggest(
            tool="update_claim",
            params={
                "label": new_label,
                "field": "proposition",
                "new_value": "PROPOSITION_TEXT_HERE",
            },
            reason="Add proposition text to the newly created claim node.",
            action_type="fix",
        )

    proposition_node = Proposition(content=proposition_content)
    arg_map.add_proposition(proposition_node)

    return proposition_node


def get_conclusion_proposition_from_relation_args(
    new_label: NodeLabel,
    conclusion_content: str | None,
    existing_ref_proposition_node: Proposition | None,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> Proposition | None:
    if existing_ref_proposition_node:
        if not conclusion_content:
            if relation_type == "support":
                return existing_ref_proposition_node
            conclusion_node = next(arg_map.get_negation_of(existing_ref_proposition_node.id), None)
            if conclusion_node:
                return conclusion_node
            # Automatically negate existing proposition
            conclusion_content = arg_map.negate_proposition_content(
                existing_ref_proposition_node.content
            )
            tc.issue(
                severity="info",
                message=f"Automatically negating existing proposition '{shorten(existing_ref_proposition_node.content, width=40)}' as '{shorten(conclusion_content, width=30)}'.",
                field="conclusion",
            )
            tc.suggest(
                tool="update_argument",
                params={
                    "label": new_label,
                    "field": "conclusion",
                    "new_value": "CONCLUSION_TEXT_HERE",
                },
                reason="Revise automatically negated conclusion to express negation in plain language.",
                action_type="improve",
            )
        if (
            conclusion_content
            and existing_ref_proposition_node.content.strip() == conclusion_content.strip()
            and relation_type == "support"
        ):
            return existing_ref_proposition_node

        conclusion_node = Proposition(content=conclusion_content)
        arg_map.add_proposition(conclusion_node)
        if relation_type == "support":
            arg_map.add_equivalence(existing_ref_proposition_node.id, conclusion_node.id)
            tc.issue(
                severity="info",
                message=f"New conclusion is automatically declared as equivalent to '{existing_ref_proposition_node.content}'.",
                field="conclusion",
            )
        elif relation_type == "attack":
            arg_map.add_negation(existing_ref_proposition_node.id, conclusion_node.id)
            tc.issue(
                severity="info",
                message=f"New conclusion is automatically declared as negation of '{existing_ref_proposition_node.content}'.",
                field="conclusion",
            )
        return conclusion_node

    # no existing_ref_proposition_node:
    if conclusion_content:
        conclusion_node = Proposition(content=conclusion_content)
        arg_map.add_proposition(conclusion_node)
        return conclusion_node

    return None


def get_premise_propositions_from_relation_args(
    new_label: NodeLabel,
    premise_contents: list[str] | None,
    existing_ref_proposition_node: Proposition | None,
    target_premise_idx: int | None,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> list[Proposition] | None:
    # validate target_premise_idx as referring to premises in new argument
    if existing_ref_proposition_node and target_premise_idx is not None:
        if premise_contents is None:
            target_premise_idx = None
        elif not (0 < target_premise_idx <= len(premise_contents)):
            target_premise_idx = None
        if target_premise_idx is None:
            tc.note(
                f"Warning: Target premise index {target_premise_idx} is out of bounds for provided premises in argument `<{new_label}>`. Ignoring `target_premise_idx`.",
                priority=0.8,
            )

    if not premise_contents and not existing_ref_proposition_node:
        return None

    if not premise_contents and existing_ref_proposition_node:
        if relation_type == "support":
            return [existing_ref_proposition_node]
        premise_node = next(arg_map.get_negation_of(existing_ref_proposition_node.id), None)
        if premise_node:
            return [premise_node]
        # Automatically negate existing proposition
        premise_content = arg_map.negate_proposition_content(existing_ref_proposition_node.content)
        tc.issue(
            severity="info",
            message=f"Automatically negating existing proposition '{shorten(existing_ref_proposition_node.content, width=40)}' as '{shorten(premise_content, width=30)}'.",
            field="premises",
        )
        tc.suggest(
            tool="update_premises",
            params={
                "label": new_label,
                "old_value": premise_content,
                "new_value": "REPHRASED_PREMISE_TEXT_HERE",
            },
            reason="Revise automatically negated premise to express negation in plain language.",
            action_type="improve",
        )

    premise_nodes: list[Proposition] = []
    for idx, premise_content in enumerate(premise_contents or [], start=1):
        if (
            idx != target_premise_idx
            or target_premise_idx is None
            or existing_ref_proposition_node is None
        ):
            premise_node = Proposition(content=premise_content)
            arg_map.add_proposition(premise_node)
            premise_nodes.append(premise_node)
            continue

        if (
            existing_ref_proposition_node.content.strip() == premise_content.strip()
            and relation_type == "support"
        ):
            premise_nodes.append(existing_ref_proposition_node)
            continue

        premise_node = Proposition(content=premise_content)
        arg_map.add_proposition(premise_node)
        premise_nodes.append(premise_node)

        if relation_type == "support":
            arg_map.add_equivalence(existing_ref_proposition_node.id, premise_node.id)
            tc.issue(
                severity="info",
                message=f"Premise ({idx}) is automatically declared as equivalent to '{existing_ref_proposition_node.content}'.",
                field="premises",
            )
        elif relation_type == "attack":
            arg_map.add_negation(existing_ref_proposition_node.id, premise_node.id)
            tc.issue(
                severity="info",
                message=f"Premise ({idx}) is automatically declared as negation of '{existing_ref_proposition_node.content}'.",
                field="premises",
            )

    return premise_nodes
