# cedrus/tools.utils.py
"""Utility functions for MCP tools."""

from __future__ import annotations
from typing import TYPE_CHECKING

from cedrus.graph import ArgumentMap
from cedrus.models import (
    NodeLabel,
    ArgumentNode,
    Proposition,
)
from cedrus.models.relations import RelationConfig

if TYPE_CHECKING:
    from cedrus.tools.tool_context import ToolContext

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

    tc.issue("warning",
        f"Note: Label '{label}' is already in use. Creating unique label '{new_label}'.",
        priority=1.0,
    )
    label = new_label

    msg = f"Label '{label}' has been created automatically to ensure uniqueness and may need revision."
    tc.issue(severity="warning", message=msg, field="label")
    return label


def sanitize_relation_args_new_node(
    arg_map: ArgumentMap,
    tc: ToolContext,
    relation_config: RelationConfig,
) -> RelationConfig:
    target = relation_config.target
    source = relation_config.source
    target_premise_idx = relation_config.target_premise_idx

    # Make sure only one relation is created
    if target and source:
        source = None  # Can't have both
        tc.issue("warning", 
            "Note: Both 'target' and 'source' were provided. Will ignore 'source'.",
            priority=1.0,
        )

    # Check if target / source exist
    if target is not None and arg_map.is_node(target) is False:
        msg = f"Target node `{target}` does not exist in the argument map. Will create node without relation."
        tc.issue("warning", msg, priority=1.0)
        target = None
    if source is not None and arg_map.is_node(source) is False:
        msg = f"Source node `{source}` does not exist in the argument map. Will create node without relation."
        tc.issue("warning", msg, priority=1.0)
        source = None

    # Validate target_premise_idx
    if target_premise_idx is not None and (
        not target or not validate_target_premise_idx(target, target_premise_idx, arg_map)
    ):
        msg = f"No premise at index {target_premise_idx} in target argument `{target}`. Ignoring `target_premise_idx`."
        tc.issue("warning", msg, priority=1.0)
        target_premise_idx = None

    relation_config = relation_config.model_copy()
    relation_config.target = target
    relation_config.source = source
    relation_config.target_premise_idx = target_premise_idx

    return relation_config


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
