# koala/tools.utils.py
"""Utility functions for MCP tools."""

from __future__ import annotations
from typing import TYPE_CHECKING

from koala.graph import ArgumentMap
from koala.models import (
    NodeLabel,
    ArgumentNode,
    Proposition,
)

if TYPE_CHECKING:
    from koala.tools.tool_context import ToolContext

# NOTE: Grounding functions moved to grounding.py
# NOTE: Review flagging functions moved to review_flagging.py
# NOTE: update_proposition moved to node_updates.py



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
