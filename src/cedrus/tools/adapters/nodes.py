"""Node-level operations for the argument map.

This module groups creation, deletion, and update helpers for
claim and argument nodes. These functions are used by the MCP
tool implementations in :mod:`cedrus.tools.impl.editing`.
"""

from __future__ import annotations

from typing import Any

from mcp.types import CallToolResult

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.graph.rendering import render_argdown_node
from cedrus.backend.models import ArgumentNode, ClaimNode, NodeLabel, Proposition
from cedrus.backend.models.propositions import Proposition as PropositionModel
from cedrus.backend.models.relations import DialecticalRelationType
from cedrus.tools.adapters.grounding import GroundingStrategy, maybe_ground_relation
from cedrus.tools.adapters.relations import (
    flag_nodes_as_needing_review,
    flag_relations_as_needing_review,
)
from cedrus.tools.runtime.tool_context import ToolContext
from cedrus.tools.util import maybe_create_proposition_from_content


def new_claim(
    label: NodeLabel,
    proposition: str | None,
    to_label: NodeLabel | None,
    from_label: NodeLabel | None,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    tags: list[str] | None,
    metadata: dict[str, str] | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Create a new claim node in the argument map.

    This is a direct move of :func:`cedrus.tools.adapters.nodes.new_claim`.
    """

    import textwrap

    grounding_strategy: GroundingStrategy | None = None
    if tc.mode != "sketch":
        if to_label:
            if relation_type == "support":
                grounding_strategy = "define_equivalence" if proposition else "copy_premise"
            elif relation_type == "attack":
                grounding_strategy = "define_negation" if proposition else "negate_premise"
        elif from_label:
            if relation_type == "support":
                grounding_strategy = "define_equivalence" if proposition else "copy_conclusion"
            elif relation_type == "attack":
                grounding_strategy = "define_negation" if proposition else "negate_conclusion"

    # Maybe create new proposition node
    proposition_node = maybe_create_proposition_from_content(
        label, proposition_content=proposition, arg_map=arg_map, tc=tc
    )

    # Create the claim node
    claim_node = ClaimNode(
        label=label,
        proposition_id=proposition_node.id,
        needs_review_flag=any(issue.severity in ["warning", "error"] for issue in tc.issues),
        tags=tags or [],
        metadata=metadata or {},
    )

    # Add claim node to argument map
    arg_map.add_claim(claim_node)
    tc.issue(
        "info",
        f"✓ Created new claim node `[{label}]` with proposition `{textwrap.shorten(proposition_node.content, width=50)}`.",
    )

    # Create dialectical relation if specified
    relation_creation_fn = (
        arg_map.add_support_relation if relation_type == "support" else arg_map.add_attack_relation
    )
    if to_label:
        relation_creation_fn(
            from_label=label, to_label=to_label, target_premise_idx=target_premise_idx
        )
        tc.issue("info", f"\n  Linked new claim to `{to_label}` via a `{relation_type}` relation.")
        maybe_ground_relation(
            label, to_label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
        )
    if from_label:
        relation_creation_fn(from_label=from_label, to_label=label)
        tc.issue(
            "info", f"\n  Linked `{from_label}` to new claim via a `{relation_type}` relation."
        )
        maybe_ground_relation(
            from_label, label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
        )

    # Refresh claim_node after possible grounding updates
    refreshed_claim_node = arg_map.get_claim(label)
    if refreshed_claim_node is None:
        raise RuntimeError(f"Failed to retrieve claim node `[{label}]` after creation.")
    claim_node = refreshed_claim_node
    tc.success(
        f"✓ Created new claim node `[{label}]`.",
        result=render_argdown_node(arg_map, label, details=False),
    )


def new_argument(
    label: NodeLabel,
    gist: str | None,
    to_label: NodeLabel | None,
    from_label: NodeLabel | None,
    relation_type: DialecticalRelationType,
    target_premise_idx: int | None,
    premises: list[str] | None,
    conclusion: str | None,
    tags: list[str] | None,
    metadata: dict[str, str] | None,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Create a new argument node in the argument map.

    Direct move of :func:`cedrus.tools.adapters.nodes.new_argument`.
    """

    # Infer grounding strategy from context
    grounding_strategy: GroundingStrategy | None = None
    if tc.mode != "sketch":
        if to_label:
            # New argument supports/attacks existing node via its conclusion
            if relation_type == "support":
                grounding_strategy = "define_equivalence" if conclusion else "copy_premise"
            elif relation_type == "attack":
                grounding_strategy = "define_negation" if conclusion else "negate_premise"
        elif from_label:
            # Existing node supports/attacks new argument via one of our premises
            if relation_type == "support":
                grounding_strategy = "define_equivalence" if premises else "copy_conclusion"
            elif relation_type == "attack":
                grounding_strategy = "define_negation" if premises else "negate_conclusion"

    # Create conclusion proposition if provided
    conclusion_node: Proposition | None = None
    if conclusion:
        conclusion_node = maybe_create_proposition_from_content(
            label, proposition_content=conclusion, arg_map=arg_map, tc=tc
        )

    # Create premise propositions if provided
    premise_nodes: list[Proposition] = []
    if premises:
        for premise_content in premises:
            premise_node = maybe_create_proposition_from_content(
                label, proposition_content=premise_content, arg_map=arg_map, tc=tc
            )
            premise_nodes.append(premise_node)

    # Create the argument node
    argument_node = ArgumentNode(
        label=label,
        gist=gist or "",
        premises=[p.id for p in premise_nodes],
        conclusion=conclusion_node.id if conclusion_node else "",
        needs_review_flag=any(issue.severity in ["warning", "error"] for issue in tc.issues),
        tags=tags or [],
        metadata=metadata or {},
    )

    # Add argument node to argument map
    arg_map.add_argument(argument_node)

    # Create dialectical relation if specified
    relation_creation_fn = (
        arg_map.add_support_relation if relation_type == "support" else arg_map.add_attack_relation
    )
    if to_label:
        relation_creation_fn(
            from_label=label, to_label=to_label, target_premise_idx=target_premise_idx
        )
        tc.issue(
            "info", f"\n  Linked new argument to `{to_label}` via a `{relation_type}` relation."
        )
        if tc.mode == "elaborate":
            maybe_ground_relation(
                label, to_label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
            )
    if from_label:
        relation_creation_fn(from_label=from_label, to_label=label)
        tc.issue(
            "info", f"\n  Linked `{from_label}` to new argument via a `{relation_type}` relation."
        )
        if tc.mode == "elaborate":
            maybe_ground_relation(
                from_label,
                label,
                relation_type,
                target_premise_idx,
                grounding_strategy,
                arg_map,
                tc,
            )

    # Refresh argument_node after possible grounding updates
    refreshed_argument_node = arg_map.get_argument(label)
    if refreshed_argument_node is None:
        raise RuntimeError(f"Failed to retrieve argument node `<{label}>` after creation.")
    argument_node = refreshed_argument_node
    details = bool(premise_nodes or conclusion_node or tc.mode in ["review", "elaborate"])
    tc.success(
        f"✓ Created new argument node `<{label}>`.",
        result=render_argdown_node(arg_map, label, details=details),
    )


def delete_claim(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete a claim node from the argument map.

    Direct move of :func:`cedrus.tools.adapters.nodes.delete_claim`.
    """

    try:
        claim_node = arg_map.get_claim(label)
        if not claim_node:
            return tc.failure(
                f"✗ Claim node `[{label}]` does not exist.", error="NodeNotFound"
            ).build()

        ref_prop_ids = [claim_node.proposition_id]
        ref_prop_ids = [prop_id for prop_id in ref_prop_ids if arg_map.is_proposition(prop_id)]

        arg_map.delete_node(label)
        for prop_id in ref_prop_ids:
            arg_map.maybe_remove_unused_proposition(prop_id)
        return tc.success(f"✓ Deleted claim node `[{label}]`.").build()

    except Exception as e:
        return tc.failure(f"✗ Failed to delete claim `[{label}]`: {str(e)}", error=str(e)).build()


def delete_argument(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete an argument node from the argument map.

    Direct move of :func:`cedrus.tools.adapters.nodes.delete_argument`.
    """

    try:
        argument_node = arg_map.get_argument(label)
        if not argument_node:
            return tc.failure(
                f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
            ).build()

        ref_prop_ids = argument_node.premises + [argument_node.conclusion]
        ref_prop_ids = [prop_id for prop_id in ref_prop_ids if arg_map.is_proposition(prop_id)]

        arg_map.delete_node(label)
        for prop_id in ref_prop_ids:
            arg_map.maybe_remove_unused_proposition(prop_id)
        return tc.success(f"✓ Deleted argument node `<{label}>`.").build()

    except Exception as e:
        return tc.failure(
            f"✗ Failed to delete argument `<{label}>`: {str(e)}", error=str(e)
        ).build()


def update_proposition(
    prop_id: str,
    updates: dict[str, Any],
    exempt_nodes_flagging: list[str],
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:
    """Update a proposition in the argument map and flag referencing nodes.

    Direct move of :func:`cedrus.tools.adapters.nodes.update_proposition`.
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

    Direct move of :func:`cedrus.tools.adapters.nodes.update_claim`.
    """

    import textwrap

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

    Direct move of :func:`cedrus.tools.adapters.nodes.update_argument`.
    """

    import textwrap

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
                conclusion_prop = PropositionModel(content=new_value)
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

    Direct move of :func:`cedrus.tools.adapters.nodes.update_metadata`.
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

    Direct move of :func:`cedrus.tools.adapters.nodes.update_tags`.
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

    Direct move of :func:`cedrus.tools.adapters.nodes.update_premises`.
    """

    import textwrap

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
                prop_node = PropositionModel(content=new_value)
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


__all__ = [
    "new_claim",
    "new_argument",
    "delete_claim",
    "delete_argument",
    "update_proposition",
    "update_claim",
    "update_argument",
    "update_metadata",
    "update_tags",
    "update_premises",
]
