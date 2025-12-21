"""Review flagging logic for nodes and relations."""

from koala.graph.argument_map import ArgumentMap
from koala.models import NodeLabel
from koala.models.base import PropositionID
from koala.tools.tool_context import ToolContext


def flag_relations_as_needing_review(
    ref_node_label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Flag all relations connected to a node as needing review.
    
    Args:
        ref_node_label: Label of the reference node
        arg_map: The argument map
        tc: Tool context for logging
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
        tc.issue("info", 
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
    
    Args:
        ref_prop_id: ID of the proposition that was modified
        exempt_nodes_flagging: List of node labels to exempt from flagging
        arg_map: The argument map
        tc: Tool context for logging
    """
    nodes_requiring_review: list[NodeLabel] = [
        node.label
        for node in arg_map.list_claims()
        if ref_prop_id == node.proposition_id and node.label not in exempt_nodes_flagging
    ] + [
        node.label
        for node in arg_map.list_arguments()
        if ref_prop_id in node.premises + [node.conclusion] and node.label not in exempt_nodes_flagging
    ]

    for node_label in nodes_requiring_review:
        arg_map.update_node(node_label, {"needs_review_flag": True})

    if nodes_requiring_review:
        tc.issue("info", 
            f"Flagged {len(nodes_requiring_review)} node(s) as needing review due to proposition update: {', '.join(nodes_requiring_review)}",
            priority=1.0,
        )
