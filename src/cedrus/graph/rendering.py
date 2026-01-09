"""Render argumen map as argdown"""

from typing import Literal
import json
from cedrus.graph import ArgumentMap
from cedrus.models.base import NodeLabel
from cedrus.models.nodes import ArgumentNode, ClaimNode
from cedrus.models.relations import DialecticalRelationType


def _get_next_indent_str(current_indent_str: str, child_index: int, total_children: int) -> str:
    """Get the indent string for the next level based on the current indent string."""
    base_indent_str = "".join([
        "│" if c in ["│", "├"] else " "
        for c in current_indent_str
    ])
    if base_indent_str:
        base_indent_str = base_indent_str + "    "
    if child_index == total_children - 1:
        return base_indent_str + "└─ "
    else:
        return base_indent_str + "├─ "
        

def _render_node_recursive(
    arg_map: ArgumentMap,
    node: ClaimNode | ArgumentNode,
    relation_to_successor: DialecticalRelationType | None,
    subset: list[NodeLabel] | None,
    lines: list[str],
    indent_level: int,
    indent_str: str,
    nodes_visited: set[NodeLabel],
    label_only: bool,
    format: Literal["argdown", "tree"],
    extra_tags: bool,
) -> None:
    """Recursively render a node and its successors."""
    if format == "argdown":
        line = "    " * indent_level
        if relation_to_successor is not None:
            line += "<+ " if relation_to_successor == "support" else "<- "
    elif format == "tree":
        line = indent_str
        if relation_to_successor is not None:
            line += "PRO " if relation_to_successor == "support" else "CON "
    else:
        raise RuntimeError(f"Unknown format (_render_node_recursive): {format}")
    
    line += f"[{node.label}]" if isinstance(node, ClaimNode) else f"<{node.label}>"
    if not label_only:
        if isinstance(node, ClaimNode):
            proposition = arg_map.get_proposition(node.proposition_id)
            if proposition:
                line += f": {proposition.content}"
        elif isinstance(node, ArgumentNode):
            if node.gist:
                line += f": {node.gist}"
        tags = node.tags.copy()
        if extra_tags:
            if node.needs_review_flag:
                tags.append("review-required")
        if tags:
            line += " " + " ".join([f"#{tag}" for tag in tags])
        if node.metadata:
            line += " " + json.dumps(node.metadata)

    lines.append(line)

    # Render all predecessor nodes (children) that have not been visited yet
    support_nodes: list[ClaimNode | ArgumentNode] = []
    for support_id in arg_map.get_supporters(node.label):
        if subset is not None and support_id not in subset:
            continue
        if support_id in nodes_visited:
            continue
        if (support_id, node.label) in arg_map.redundant_edges(subset=subset):
            continue
        support_node = arg_map.get_node(support_id)
        if support_node is not None:
            support_nodes.append(support_node)

    attack_nodes: list[ClaimNode | ArgumentNode] = []
    for attack_id in arg_map.get_attackers(node.label):
        if subset is not None and attack_id not in subset:
            continue
        if attack_id in nodes_visited:
            continue
        if (attack_id, node.label) in arg_map.redundant_edges(subset=subset):
            continue
        attack_node = arg_map.get_node(attack_id)
        if attack_node is not None:
            attack_nodes.append(attack_node)

    for e, node in enumerate(support_nodes + attack_nodes):
        relation_to_successor = "support" if e < len(support_nodes) else "attack"
        next_indent_str = _get_next_indent_str(indent_str, e, len(support_nodes) + len(attack_nodes))
        _render_node_recursive(
            arg_map,
            node,
            relation_to_successor=relation_to_successor,
            subset=subset,
            lines=lines,
            indent_level=indent_level + 1,
            indent_str=next_indent_str,
            nodes_visited=nodes_visited | {node.label},
            label_only=label_only,
            format=format,
            extra_tags=extra_tags,
        )

def render_argdown(
    arg_map: ArgumentMap,
    subset: list[NodeLabel] | None = None,
    label_only: bool = False,
    format: Literal["argdown", "tree"] = "argdown",
    extra_tags: bool = False,
) -> str:
    lines: list[str] = []

    # get root nodes
    roots = [arg_map.get_node(label) for label in arg_map.list_roots()]

    for root in roots:
        # Render this node and all its descendants recursively
        _render_node_recursive(
            arg_map=arg_map,
            node=root,
            relation_to_successor=None,
            subset=subset,
            lines=lines,
            indent_level=0,
            indent_str="",
            nodes_visited=set(),
            label_only=label_only,
            format=format,
            extra_tags=extra_tags,
        )

    # add any redundant edges that were skipped
    extra_lines: list[str] = []
    for from_label, to_label in arg_map.redundant_edges(subset=subset):
        if not subset or (from_label in subset and to_label in subset):
            from_node = arg_map.get_node(from_label)
            to_node = arg_map.get_node(to_label)
            if from_node is not None and to_node is not None:
                line = "// "
                line += f"[{from_node.label}]" if isinstance(from_node, ClaimNode) else f"<{from_node.label}>"
                relation = arg_map.get_dialectic_relation(from_label, to_label)
                if relation is not None:
                    line += " +> " if relation.relation_type == "support" else " -> "
                else:
                    line += " ?? "
                line += f"[{to_node.label}]" if isinstance(to_node, ClaimNode) else f"<{to_node.label}>"
                extra_lines.append(line)

    if extra_lines:
        lines.append("")
        lines.append("// Redundant edges skipped above:")
        lines.extend(extra_lines)

    return "\n".join(lines)


def render_argdown_node(
    arg_map: ArgumentMap,
    label: NodeLabel,
    details: bool
) -> str:
    lines: list[str] = []
    node = arg_map.get_node(label)
    if node is None:
        return f"Node {label} not found."
    
    if isinstance(node, ClaimNode):
        proposition = arg_map.get_proposition(node.proposition_id)
        content = proposition.content if proposition else "/*No proposition provided.*/"        
        line = f"[{node.label}]: {content}"
        if node.tags:
            line += " " + " ".join([f"#{tag}" for tag in node.tags])
        if details and node.metadata:
            line += " " + json.dumps(node.metadata)
    elif isinstance(node, ArgumentNode):
        gist = node.gist if node.gist else "/*No gist provided.*/"
        line = f"<{node.label}>: {gist}"
    else:
        raise RuntimeError(f"Unknown node type for label {label}: {type(node)}")
    lines.append(line)
    # Show supporters
    supported = arg_map.get_supported(label)
    if supported:
        lines.append("// Supports:")
        for sup_id in supported:
            sup_node = arg_map.get_node(sup_id)
            if sup_node:
                sup_line = "+> "
                if isinstance(sup_node, ClaimNode):
                    sup_line += f"[{sup_node.label}]"
                elif isinstance(sup_node, ArgumentNode):
                    sup_line += f"<{sup_node.label}>"
                lines.append(sup_line)
    # Show attacked
    attacked = arg_map.get_attacked(label)
    if attacked:
        lines.append("// Attacks:")
        for att_id in attacked:
            att_node = arg_map.get_node(att_id)
            if att_node:
                att_line = "-> "
                if isinstance(att_node, ClaimNode):
                    att_line += f"[{att_node.label}]"
                elif isinstance(att_node, ArgumentNode):
                    att_line += f"<{att_node.label}>"
                lines.append(att_line)
    # Show supporters
    supporters = arg_map.get_supporters(label)
    if supporters:
        lines.append("// Supported by:")
        for sup_id in supporters:
            sup_node = arg_map.get_node(sup_id)
            if sup_node:
                sup_line = "<+ "
                if isinstance(sup_node, ClaimNode):
                    sup_line += f"[{sup_node.label}]"
                elif isinstance(sup_node, ArgumentNode):
                    sup_line += f"<{sup_node.label}>"
                lines.append(sup_line)
    # Show attackers
    attackers = arg_map.get_attackers(label)
    if attackers:
        lines.append("// Attacked by:")
        for att_id in attackers:
            att_node = arg_map.get_node(att_id)
            if att_node:
                att_line = "<- "
                if isinstance(att_node, ClaimNode):
                    att_line += f"[{att_node.label}]"
                elif isinstance(att_node, ArgumentNode):
                    att_line += f"<{att_node.label}>"
                lines.append(att_line)

    if details:
        if isinstance(node, ArgumentNode):
            lines.append("")
            if node.premises:
                for idx, premise_id in enumerate(node.premises, start=1):
                    premise = arg_map.get_proposition(premise_id)
                    content = premise.content if premise else "/*No premise proposition found.*/"
                    lines.append(f"({idx}) {content}")
            else:
                lines.append("/*No premises provided.*/")
            lines.append("-----")
            conclusion = arg_map.get_proposition(node.conclusion)
            content = conclusion.content if conclusion else "/*No conclusion proposition found.*/"
            if node.premises:
                lines.append(f"({len(node.premises) + 1}) {content}")
            else:
                lines.append(f"Conclusion: {content}")

        if node.needs_review_flag:
            lines.append("")
            lines.append("This node is marked as needing review.")

    return "\n".join(lines)