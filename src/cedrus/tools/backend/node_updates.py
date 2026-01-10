"""Node update functions for the argument map."""

import textwrap
from typing import Any

from mcp.types import CallToolResult

from cedrus.graph.argument_map import ArgumentMap
from cedrus.graph.rendering import render_argdown_node
from cedrus.models import (
    ArgumentNode,
    ClaimNode,
    NodeLabel,
    Proposition,
)
from cedrus.tools.backend.review_flagging import (
    flag_nodes_as_needing_review,
    flag_relations_as_needing_review,
)
from cedrus.tools.runtime.tool_context import ToolContext


def update_proposition(
    prop_id: str,
    updates: dict[str, Any],
    exempt_nodes_flagging: list[str],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Update a proposition in the argument map and flag all nodes referencing it as needing review.

    Args:
        prop_id: ID of the proposition to update
        updates: Dictionary of updates to apply
        exempt_nodes_flagging: List of node labels to exempt from review flagging
        arg_map: The argument map
        tc: Tool context for logging
    """

    if not updates:
        return
    if not arg_map.is_proposition(prop_id):
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


def update_claim(
    label: NodeLabel,
    field: str,
    new_value: str | bool | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Update a claim node in the argument map.

    Args:
        label: The label of the claim node to update.
        field: The field to update (e.g., "proposition", "label", "needs_review_flag").
        new_value: The new value for the specified field.

    Returns:
        Textual feedback and next step suggestions.
    """

    claim_node = arg_map.get_claim(label)
    if not claim_node:
        return tc.failure(f"✗ Claim node `[{label}]` does not exist.", error="NodeNotFound").build()

    if field == "proposition":
        if not isinstance(new_value, str) or not new_value.strip():
            return tc.failure(
                f"✗ Cannot update proposition of claim node `[{label}]` to an empty or non-string value.",
                error="InvalidNewProposition",
            ).build()
        proposition = arg_map.get_proposition(claim_node.proposition_id)
        if not proposition:
            tc.failure(
                f"✗ Proposition for claim node `[{label}]` does not exist.",
                error="PropositionNotFound",
            )
            # mark claim as "needs review"
            arg_map.update_node(claim_node.label, updates={"needs_review_flag": True})
            return tc.suggest(
                "remove",
                {"label": label},
                f"Delete defect claim node `[{label}]` since its proposition is missing.",
                action_type="cleanup",
            ).build()

        old_content = proposition.content
        try:
            update_proposition(
                proposition.id,
                {"content": new_value},
                exempt_nodes_flagging=[claim_node.label],
                arg_map=arg_map,
                tc=tc,
            )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update proposition for claim node `[{label}]`: {str(e)}",
                error=str(e),
            ).build()
        flag_relations_as_needing_review(claim_node.label, arg_map, tc)
        return tc.success(
            f"✓ Updated proposition of claim node `[{label}]` from `{textwrap.shorten(old_content, width=40)}` to `{textwrap.shorten(new_value, width=40)}`.",
            result=render_argdown_node(arg_map, label, details=False),
        ).build()
    elif field == "label":
        if not isinstance(new_value, str) or not new_value.strip():
            return tc.failure(
                f"✗ Cannot update label of claim node `[{label}]` to `[{new_value}]` since a label cannot be empty or None.",
                error="InvalidNewLabel",
            ).build()
        old_label = claim_node.label
        if arg_map.get_claim(new_value) is not None:
            return tc.failure(
                f"✗ Cannot update label of claim node `[{label}]` to `[{new_value}]` since that label is already in use.",
                error="LabelAlreadyExists",
            ).build()
        try:
            arg_map.update_label(claim_node.label, new_value)
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update label of claim node `[{label}]`: {str(e)}",
                error=str(e),
            ).build()
        if (claim_node := arg_map.get_claim(new_value)) is None:
            return tc.failure(
                f"✗ Failed to retrieve claim node after label update to `[{new_value}]`.",
                error="NodeNotFoundAfterUpdate",
            ).build()
        return tc.success(
            f"✓ Updated label of claim node from `[{old_label}]` to `[{new_value}]`.",
            result=render_argdown_node(arg_map, new_value, details=False),
        ).build()
    elif field in [
        "needs_review_flag",
        "misses_justification_flag",
        "misses_critique_flag",
    ]:
        if not isinstance(new_value, bool):
            new_value = bool(new_value)
        old_value = getattr(claim_node, field)
        try:
            arg_map.update_node(claim_node.label, {field: new_value})
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update `{field}` for claim node `[{label}]`: {str(e)}",
                error=str(e),
            ).build()

        return tc.success(
            f"✓ Updated `{field}` of claim node `[{label}]` from `{old_value}` to `{new_value}`.",
            result=render_argdown_node(arg_map, label, details=False),
        ).build()

    else:
        return tc.failure(
            f"✗ Field `{field}` is not supported for updating in claim nodes.",
            error="InvalidField",
        ).build()


def update_argument(
    label: NodeLabel,
    field: str,
    new_value: str | bool | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Update an argument node in the argument map.

    Args:
        label: The label of the argument node to update.
        field: The field to update (e.g., "gist", "conclusion", "label", "needs_review_flag").
        new_value: The new value for the specified field.

    Returns:
        Textual feedback.
    """

    try:
        argument_node = arg_map.get_argument(label)
        if not argument_node:
            return tc.failure(
                f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
            ).build()

        if field == "label":
            old_label = argument_node.label
            if not isinstance(new_value, str) or not new_value.strip():
                return tc.failure(
                    f"✗ Cannot update label of argument node `<{label}>` to `<{new_value}>` since a label cannot be empty or None.",
                    error="InvalidNewLabel",
                ).build()
            if arg_map.get_argument(new_value) is not None:
                return tc.failure(
                    f"✗ Cannot update label of argument node `<{label}>` to `<{new_value}>` since that label is already in use.",
                    error="LabelAlreadyExists",
                ).build()
            try:
                arg_map.update_label(argument_node.label, new_value)
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update label of argument node `<{label}>`: {str(e)}",
                    error=str(e),
                ).build()
            if (argument_node := arg_map.get_argument(new_value)) is None:
                return tc.failure(
                    f"✗ Failed to retrieve argument node after label update to `<{new_value}>`.",
                    error="NodeNotFoundAfterUpdate",
                ).build()
            return tc.success(
                f"✓ Updated label of argument node from `<{old_label}>` to `<{new_value}>`.",
                result=render_argdown_node(arg_map, argument_node.label, details=False),
            ).build()

        elif field in ["conclusion"]:
            old_conclusion_prop = arg_map.get_proposition(argument_node.conclusion)
            old_value = old_conclusion_prop.content if old_conclusion_prop else None

            if new_value is None:
                if not old_conclusion_prop:
                    return tc.failure(
                        f"✗ Cannot remove non-existing conclusion of argument node `<{label}>`.",
                        error="NoExistingConclusion",
                    ).build()
                try:
                    arg_map.update_node(argument_node.label, {"conclusion": ""})
                    arg_map.maybe_remove_unused_proposition(old_conclusion_prop.id)
                    flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                    return tc.success(
                        f"✓ Removed conclusion of argument node `<{label}>` which was `{textwrap.shorten(str(old_value), width=40)}`.",
                        result=render_argdown_node(arg_map, argument_node.label, details=True),
                    ).build()
                except Exception as e:
                    return tc.failure(
                        f"✗ Failed to remove conclusion for argument node `<{label}>`: {str(e)}",
                        error=str(e),
                    ).build()

            if not isinstance(new_value, str) or not new_value.strip():
                return tc.failure(
                    f"✗ Cannot update conclusion of argument node `<{label}>` to an empty or non-string value.",
                    error="InvalidNewConclusion",
                ).build()

            if old_value == new_value:
                return tc.failure(
                    f"✗ Old and new conclusion texts are the same (`{old_value}`) for updating conclusion of argument node `<{label}>`.",
                    error="SameConclusionValuesProvided",
                ).build()

            conclusion_prop = next(arg_map.find_proposition_by_content(new_value), None)
            if conclusion_prop is None and old_conclusion_prop is not None:
                conclusion_prop = old_conclusion_prop
                update_proposition(
                    conclusion_prop.id,
                    {"content": new_value},
                    exempt_nodes_flagging=[argument_node.label],
                    arg_map=arg_map,
                    tc=tc,
                )
            if conclusion_prop is None:
                conclusion_prop = Proposition(content=new_value)
                arg_map.add_proposition(conclusion_prop)

            try:
                # reference new proposition
                arg_map.update_node(argument_node.label, {"conclusion": conclusion_prop.id})
                # maybe delete old proposition if now unused
                arg_map.maybe_remove_unused_proposition(
                    old_conclusion_prop.id
                ) if old_conclusion_prop else None
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update conclusion for argument node `<{label}>`: {str(e)}",
                    error=str(e),
                ).build()

            flag_relations_as_needing_review(argument_node.label, arg_map, tc)
            return tc.success(
                f"✓ Updated conclusion of argument node `<{label}>` {('from `' + textwrap.shorten(old_value, width=40) + '`') if old_value else ''} to `{textwrap.shorten(new_value or '', width=40)}`.",
                result=render_argdown_node(arg_map, argument_node.label, details=True),
            ).build()

        elif field in ["gist"]:
            if not isinstance(new_value, str) or not new_value.strip():
                return tc.failure(
                    f"✗ Cannot update `{field}` of argument node `<{label}>` to an empty or non-string value.",
                    error="InvalidNewValue",
                ).build()
            old_value = getattr(argument_node, field)
            try:
                arg_map.update_node(argument_node.label, {field: new_value})
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update {field} for argument node `<{label}>`: {str(e)}",
                    error=str(e),
                ).build()

            return tc.success(
                f"✓ Updated {field} of argument node `<{label}>` from `{textwrap.shorten(str(old_value), width=40)}` to `{textwrap.shorten(new_value or '', width=40)}`.",
                result=render_argdown_node(arg_map, argument_node.label, details=False),
            ).build()

        elif field in [
            "needs_review_flag",
            "misses_justification_flag",
            "misses_critique_flag",
        ]:
            if not isinstance(new_value, bool):
                new_value = bool(new_value)
            old_value = getattr(argument_node, field)
            try:
                arg_map.update_node(argument_node.label, {field: new_value})
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update `{field}` for argument node `<{label}>`: {str(e)}",
                    error=str(e),
                ).build()

            return tc.success(
                f"✓ Updated `{field}` of argument node `<{label}>` from `{old_value}` to `{new_value}`.",
                result=render_argdown_node(arg_map, argument_node.label, details=True),
            ).build()

        else:
            return tc.failure(
                f"✗ Field `{field}` is not supported for updating in argument nodes.",
                error="InvalidField",
            ).build()

    except Exception as e:
        return tc.failure(
            f"✗ Failed to update argument `<{label}>`: {str(e)}", error=str(e)
        ).build()


def update_metadata(
    label: NodeLabel,
    key: str | None,
    new_value: str | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Update metadata for a node in the argument map.

    Args:
        label: The label of the node to update.
        key: The metadata key to update.
        new_value: The new value for the specified metadata key. If None, the key is removed.
    """

    try:
        if not isinstance(key, str) or not key.strip():
            return tc.failure(
                f"✗ Cannot update metadata key `{key}` for node `[{label}]` since a key cannot be empty or None.",
                error="InvalidMetadataKey",
            ).build()

        if not arg_map.is_node(label):
            return tc.failure(f"✗ Node `[{label}]` does not exist.", error="NodeNotFound").build()
        node = arg_map.get_node(label)

        old_metadata = node.metadata.copy()
        updated_metadata = old_metadata.copy()
        if new_value is None:
            if key in updated_metadata:
                del updated_metadata[key]
                tc.issue(
                    "info",
                    f"Removing metadata key `{key}` from node `[{label}]` (`new_value=None`).",
                )
        else:
            updated_metadata[key] = new_value

        try:
            arg_map.update_node(node.label, {"metadata": updated_metadata})
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update metadata for node `[{label}]`: {str(e)}", error=str(e)
            ).build()

        return tc.success(
            f"✓ Updated metadata key `{key}` of node `[{label}]`.",
            result=render_argdown_node(arg_map, node.label, details=True),
        ).build()

    except Exception as e:
        return tc.failure(
            f"✗ Failed to update metadata for node `[{label}]`: {str(e)}", error=str(e)
        ).build()


def update_tags(
    label: NodeLabel,
    old_value: str | None,
    new_value: str | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Update tags for a node in the argument map.

    Args:
        label: The label of the node to update.
        old_value: The tag to remove (if any).
        new_value: The tag to add (if any).
    """

    try:
        if not arg_map.is_node(label):
            return tc.failure(f"✗ Node `[{label}]` does not exist.", error="NodeNotFound").build()
        node = arg_map.get_node(label)

        if old_value is None and new_value is None:
            return tc.failure(
                f"✗ Neither old_value nor new_value provided for updating tags of node `[{label}]`.",
                error="NoTagValuesProvided",
            ).build()

        old_value = old_value.strip() if old_value is not None else None
        new_value = new_value.strip() if new_value is not None else None

        if old_value == new_value:
            return tc.failure(
                f"✗ old_value and new_value are the same (`{old_value}`) for updating tags of node `[{label}]`.",
                error="SameTagValuesProvided",
            ).build()

        old_tags = set(node.tags)
        updated_tags = old_tags.copy()
        if old_value is not None:
            if old_value in updated_tags:
                updated_tags.remove(old_value)
                tc.issue("info", f"Removing tag `{old_value}` from node `[{label}]`.")
            else:
                tc.issue(
                    "info", f"Tag `{old_value}` not found in node `[{label}]`; nothing to remove."
                )
        if new_value is not None:
            if new_value not in updated_tags:
                updated_tags.add(new_value)
                tc.issue("info", f"Adding tag `{new_value}` to node `[{label}]`.")
            else:
                tc.issue(
                    "info",
                    f"Tag `{new_value}` already present in node `[{label}]`; nothing to add.",
                )

        try:
            arg_map.update_node(node.label, {"tags": list(updated_tags)})
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update tags for node `[{label}]`: {str(e)}", error=str(e)
            ).build()

        return tc.success(
            f"✓ Updated tags for node `[{label}]`.",
            result=render_argdown_node(arg_map, node.label, details=True),
        ).build()

    except Exception as e:
        return tc.failure(
            f"✗ Failed to update tags for node `[{label}]`: {str(e)}", error=str(e)
        ).build()


def update_premises(
    label: NodeLabel,
    old_value: str | None,
    new_value: str | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Update premises for an argument node in the argument map.

    Args:
        label: The label of the argument node to update.
        old_value: The content of the premise to remove or replace (if any).
        new_value: The content of the premise to add (if any). If None, the premise at premise_idx is removed.

    If old_value is None, a new premise is added. If new_value is None, the premise with old_value is removed.
    """

    try:
        if old_value is None and new_value is None:
            return tc.failure(
                f"✗ Neither old_value nor new_value provided for updating premises of argument `<{label}>`.",
                error="NoPremiseValuesProvided",
            ).build()

        argument_node = arg_map.get_argument(label)
        if not argument_node:
            return tc.failure(
                f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
            ).build()

        premise_nodes = [arg_map.get_proposition(pid) for pid in argument_node.premises]
        if any(p is None for p in premise_nodes):
            tc.issue(
                "warning",
                f"Ignoring non-existent premises in argument node `<{label}>`. Consider running validate with fix=True to clean up.",
            )
        premise_nodes = [p for p in premise_nodes if p is not None]

        if old_value is not None:
            old_premise = next((p for p in premise_nodes if p and p.content == old_value), None)
            if old_premise is None:
                return tc.failure(
                    f"✗ Cannot find premise '{textwrap.shorten(old_value, 30)}' in argument `<{label}>` for updating.",
                    error="PremiseNotFound",
                ).build()
        else:
            old_premise = None

        if old_premise is None:
            if new_value is None or new_value.strip() == "":
                return tc.failure(
                    f"✗ Cannot create a new empty premise in argument `<{label}>`.",
                    error="EmptyPremiseContent",
                ).build()
            # Maybe create new proposition node for the new premise
            prop_node = next(arg_map.find_proposition_by_content(new_value), None)
            if not prop_node:
                prop_node = Proposition(content=new_value)
                arg_map.add_proposition(prop_node)
            premise_nodes.append(prop_node)
            arg_map.update_node(
                argument_node.label,
                {"premises": [p.id for p in premise_nodes if p is not None]},
            )
            return tc.success(
                f"✓ Added new premise '({len(premise_nodes)}) {textwrap.shorten(new_value, 30)}' to argument `<{label}>`.",
                result=render_argdown_node(arg_map, argument_node.label, details=True),
            ).build()

        else:
            # Check for invalid specifications first
            if new_value is not None and new_value.strip() == "":
                return tc.failure(
                    f"✗ Cannot update premise '{old_premise.content}' of argument `<{label}>` to an empty value.",
                    error="EmptyPremiseContent",
                ).build()

            if new_value is not None and old_premise.content == new_value:
                return tc.failure(
                    f"✗ Old premise content and new_value are the same (`{old_premise.content}`) for updating premises of argument `<{label}>`.",
                    error="SamePremiseValuesProvided",
                ).build()

            if new_value is None:
                arg_map.update_node(
                    argument_node.label,
                    {
                        "premises": [
                            p.id for p in premise_nodes if p is not None and p.id != old_premise.id
                        ]
                    },
                )
                arg_map.maybe_remove_unused_proposition(old_premise.id)
                flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                return tc.success(
                    f"✓ Removed premise '{textwrap.shorten(old_premise.content, 40)}' from argument `<{label}>`.",
                    result=render_argdown_node(arg_map, argument_node.label, details=True),
                ).build()

            if new_value is not None:
                update_proposition(
                    old_premise.id,
                    {"content": new_value},
                    exempt_nodes_flagging=[argument_node.label],
                    arg_map=arg_map,
                    tc=tc,
                )
                flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                return tc.success(
                    f"✓ Updated premise '{old_premise.content}' of argument `<{label}>` to '{new_value}'.",
                    result=render_argdown_node(arg_map, argument_node.label, details=True),
                ).build()
    except Exception as e:
        return tc.failure(
            f"✗ Failed to update premises for argument `<{label}>`: {str(e)}", error=str(e)
        ).build()
