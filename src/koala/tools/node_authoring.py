"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

import textwrap

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.propositions import Proposition
from koala.models.relations import DialecticalRelationType
from koala.server import mcp, AppContext
from koala.tools import utils
from koala.tools.tool_context import tool_context

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger


@mcp.tool()
def new_claim(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    proposition: str | None = None,
    to_label: NodeLabel | None = None,
    from_label: NodeLabel | None = None,
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> CallToolResult:
    """Create a new claim node in the argument map.

    For basic usage, provide label and proposition. Optional arguments specify details, or
    relate the new claim to existing nodes, auto-filling proposition from connected nodes
    as needed.

    Args:
        label: The unique label for the new claim node to be created.
        proposition: The proposition text for the new claim node.
        to_label: Optional label of existing node to connect the new claim _to_.
        from_label: Optional label of existing node to connect the new claim _from_.
        relation_type: Optional type of relation to create when connecting nodes. Defaults to "support".
        target_premise_idx: Optional index of the premise to target in the relation, provided to_label refers to an argument node.
        tags: Optional list of tags for the claim node.
        metadata: Optional metadata dictionary for the claim node.

    Returns:
        Textual feedback and next step suggestions.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        # Ensure label is unique
        label = utils.ensure_label_is_unique(label, arg_map, tc)

        # Validate relation arguments
        to_label, from_label, target_premise_idx = utils.sanitize_relation_args_new_node(
            to_label, from_label, target_premise_idx, arg_map, tc
        )

        # Maybe get existing ref proposition
        existing_ref_proposition_node = utils.maybe_get_ref_proposition_from_relation_args(
            to_label, from_label, target_premise_idx, arg_map, tc
        )

        # Fix proposition_node to use in new argument
        proposition_node = utils.get_claim_proposition_from_relation_args(
            label, proposition, existing_ref_proposition_node, relation_type, arg_map, tc
        )

        # Create the claim node
        claim_node = ClaimNode(
            label=label,
            proposition_id=proposition_node.id,
            issues=tc.issues.copy(),
            needs_review_flag=bool(tc.issues),
            tags=tags or [],
            metadata=metadata or {},
        )

        try:
            # Add claim node to argument map
            arg_map.add_claim(claim_node)
            msg = f"✓ Created new claim node `[{label}]` with proposition `{textwrap.shorten(proposition_node.content, width=50)}`."

            # Create relations if specified
            relation_creation_fn = (
                arg_map.add_support_relation
                if relation_type == "support"
                else arg_map.add_attack_relation
            )
            if to_label:
                relation_creation_fn(
                    from_label=label, to_label=to_label, target_premise_idx=target_premise_idx
                )
                msg += f"\n  Linked new claim to `{to_label}` via a `{relation_type}` relation."
            if from_label:
                relation_creation_fn(from_label=from_label, to_label=label)
                msg += f"\n  Linked `{from_label}` to new claim via a `{relation_type}` relation."

            tc.note(msg)
            tc.success(
                f"✓ Created new claim node `[{label}]`.",
                result=arg_map.get_info_claim_node(claim_node, verbose=False),
            )

        except Exception as e:
            return tc.failure(
                f"✗ Failed to create claim `[{label}]`: {str(e)}", error=str(e)
            ).build()

        # Add suggestions if no critical issues
        if not tc.issues:
            tc.suggest(
                "new_argument",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "gist": "KEY_POINT_OF_NEW_ARGUMENT",
                    "to_label": label,
                    "relation_type": "support",
                },
                f"Explore pros and cons by adding a new supporting argument for `[{label}]`.",
                action_type="expand",
            )
            tc.suggest(
                "new_argument",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "gist": "KEY_POINT_OF_NEW_ARGUMENT",
                    "to_label": label,
                    "relation_type": "attack",
                },
                f"Explore pros and cons by adding a new argument attacking `[{label}]`.",
                action_type="expand",
            )
            tc.suggest(
                "new_argument",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "gist": "KEY_POINT_OF_NEW_ARGUMENT",
                    "from_label": label,
                    "relation_type": "support",
                },
                f"Show how claim `[{label}]` is embedded in the debate by adding a new argument which is supported by `[{label}]`.",
                action_type="expand",
            )

            if arg_map.list_arguments():
                if len(arg_map.get_supporters(label)) > len(arg_map.get_attackers(label)):
                    tc.suggest(
                        "new_attack_relation",
                        {
                            "from_label": "EXISTING_ARGUMENT_LABEL",
                            "to_label": label,
                            "relation_type": "support",
                        },
                        f"Show how claim `[{label}]` is related to other arguments by identifying a supporting argument.",
                        action_type="connect",
                    )
                else:
                    tc.suggest(
                        "new_support_relation",
                        {
                            "from_label": "EXISTING_ARGUMENT_LABEL",
                            "to_label": label,
                            "relation_type": "support",
                        },
                        f"Show how claim `[{label}]` is related to other arguments by identifying a supporting argument.",
                        action_type="connect",
                    )

        return tc.build()


@mcp.tool()
def update_claim(
    label: NodeLabel,
    field: str,
    new_value: str | bool | None,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Update a claim node in the argument map.

    Args:
        label: The label of the claim node to update.
        field: The field to update (e.g., "proposition", "label", "needs_review_flag").
        new_value: The new value for the specified field.

    Returns:
        Textual feedback and next step suggestions.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            claim_node = arg_map.get_claim(label)
            if not claim_node:
                return tc.failure(
                    f"✗ Claim node `[{label}]` does not exist.", error="NodeNotFound"
                ).build()

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
                        "delete_claim",
                        {"label": label},
                        f"Delete defect claim node `[{label}]` since its proposition is missing.",
                        action_type="cleanup",
                    ).build()

                old_content = proposition.content
                try:
                    utils.update_proposition(proposition.id, {"content": new_value}, exempt_nodes_flagging=[claim_node.label], arg_map=arg_map, tc=tc)
                except Exception as e:
                    return tc.failure(
                        f"✗ Failed to update proposition for claim node `[{label}]`: {str(e)}",
                        error=str(e),
                    ).build()
                utils.flag_relations_as_needing_review(claim_node.label, arg_map, tc)
                return tc.success(
                    f"✓ Updated proposition of claim node `[{label}]` from `{textwrap.shorten(old_content, width=40)}` to `{textwrap.shorten(new_value, width=40)}`.",
                    result=arg_map.get_info_claim_node(claim_node, verbose=False),
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
                    result=arg_map.get_info_claim_node(claim_node, verbose=False),
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
                    result=arg_map.get_info_claim_node(claim_node, verbose=False),
                ).build()

            else:
                return tc.failure(
                    f"✗ Field `{field}` is not supported for updating in claim nodes.",
                    error="InvalidField",
                ).build()

        except Exception as e:
            return tc.failure(
                f"✗ Failed to update claim `[{label}]`: {str(e)}", error=str(e)
            ).build()


@mcp.tool()
def new_argument(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
    gist: str | None = None,
    to_label: NodeLabel | None = None,
    from_label: NodeLabel | None = None,
    relation_type: DialecticalRelationType = "support",
    target_premise_idx: int | None = None,
    premises: list[str] | None = None,
    conclusion: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> CallToolResult:
    """Create a new argument node in the argument map.

    For basic usage, provide label and gist. Optional arguments specify details, or
    relate the new argument to existing nodes, auto-filling conclusion or premises
    from connected nodes as needed.

    Args:
        label: The unique label for the new argument node to be created.
        gist: The gist text for the new argument node.
        to_label: Optional label of existing node to connect the new argument _to_.
        from_label: Optional label of existing node to connect the new argument _from_.
        relation_type: Optional type of relation to create when connecting nodes.
        target_premise_idx: Optional index of the premise to target in the relation (in to_label argument, or in newly created argument).
        premises: Optional list of premise texts for the new argument node.
        conclusion: Optional conclusion text for the new argument node.
        tags: Optional list of tags for the argument node.
        metadata: Optional metadata dictionary for the argument node.

    Returns:
        Textual feedback and next step suggestions.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        # Ensure label is unique
        label = utils.ensure_label_is_unique(label, arg_map, tc)

        # Validate relation arguments
        to_label, from_label, target_premise_idx = utils.sanitize_relation_args_new_node(
            to_label, from_label, target_premise_idx, arg_map, tc
        )

        # Maybe get existing ref proposition to be used as conclusion (to_label) or premise (from_label)
        existing_ref_proposition_node = utils.maybe_get_ref_proposition_from_relation_args(
            to_label, from_label, target_premise_idx, arg_map, tc
        )

        # Fix conclusion node to use in new argument
        conclusion_node = utils.get_conclusion_proposition_from_relation_args(
            label,
            conclusion,
            existing_ref_proposition_node if to_label else None,
            relation_type,
            arg_map,
            tc,
        )

        # Fix premise nodes to use in new argument
        premise_nodes = utils.get_premise_propositions_from_relation_args(
            label,
            premises,
            existing_ref_proposition_node if from_label else None,
            target_premise_idx,
            relation_type,
            arg_map,
            tc,
        )

        # Create the argument node
        argument_node = ArgumentNode(
            label=label,
            gist=gist or "",
            premises=[p.id for p in premise_nodes or []],
            conclusion=conclusion_node.id if conclusion_node else "",
            issues=tc.issues.copy(),
            needs_review_flag=bool(tc.issues),
            tags=tags or [],
            metadata=metadata or {},
        )

        try:
            # Add argument node to argument map
            arg_map.add_argument(argument_node)
            msg = f"✓ Created new argument node `<{label}>`"
            msg += f" with gist `{textwrap.shorten(gist or '', width=50)}`." if gist else "."

            # Create relations if specified
            relation_creation_fn = (
                arg_map.add_support_relation
                if relation_type == "support"
                else arg_map.add_attack_relation
            )
            if to_label:
                relation_creation_fn(
                    from_label=label, to_label=to_label, target_premise_idx=target_premise_idx
                )
                msg += f"\n  Linked new argument to `{to_label}` via a `{relation_type}` relation."
            if from_label:
                relation_creation_fn(from_label=from_label, to_label=label)
                msg += (
                    f"\n  Linked `{from_label}` to new argument via a `{relation_type}` relation."
                )

            tc.note(msg)
            tc.success(
                f"✓ Created new argument node `<{label}>`.",
                result=arg_map.get_info_argument_node(argument_node, verbose=False),
            )

        except Exception as e:
            return tc.failure(
                f"✗ Failed to create argument `<{label}]`: {str(e)}", error=str(e)
            ).build()

        # Add suggestions if no critical issues
        if not tc.issues:
            # Suggest support for premises or argument
            if premise_nodes:
                tc.suggest_support_argument(
                    label,
                    f"Add a further supporting argument that backs up premise (TARGET_PREMISE_IDX) of argument `<{label}>`.",
                    target_premise_idx="TARGET_PREMISE_IDX",
                )
            else:
                tc.suggest_support_argument(
                    label, f"Add a further supporting argument for argument `<{label}>`."
                )

            # Suggest adding gist if missing
            if not gist:
                tc.suggest_update_field(
                    label,
                    "gist",
                    f"Summarize the key point of argument `<{label}>` by adding a gist.",
                    tool="update_argument",
                )

            # Suggest attack if too many supporters
            if len(arg_map.get_supporters(label)) > len(arg_map.get_attackers(label)):
                tc.suggest_attack_argument(
                    label,
                    f"Reconstruct an objection to `<{label}>` by adding an attacking argument.",
                )

            # Suggest embedding if isolated
            if not arg_map.get_supported(label) and not arg_map.get_attacked(label):
                if arg_map.list_claims():
                    tc.suggest_connect_relation(
                        label, "EXISTING_CLAIM_LABEL", "support", tool="new_support_relation"
                    )
                if arg_map.list_arguments():
                    tc.suggest_connect_relation(
                        label, "EXISTING_ARGUMENT_LABEL", "attack", tool="new_attack_relation"
                    )

        return tc.build()


@mcp.tool()
def update_argument(
    label: NodeLabel,
    field: str,
    new_value: str | bool | None,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Update an argument node in the argument map.

    Args:
        label: The label of the argument node to update.
        field: The field to update (e.g., "gist", "conclusion", "label", "needs_review_flag").
        new_value: The new value for the specified field.

    Returns:
        Textual feedback.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
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
                tc.success(
                    f"✓ Updated label of argument node from `<{old_label}>` to `<{new_value}>`.",
                    result=arg_map.get_info_argument_node(argument_node, verbose=False),
                )

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
                        utils.flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                        return tc.success(
                            f"✓ Removed conclusion of argument node `<{label}>` which was `{textwrap.shorten(str(old_value), width=40)}`.",
                            result=arg_map.get_info_argument_node(argument_node, verbose=False),
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
                    utils.update_proposition(conclusion_prop.id, {"content": new_value}, exempt_nodes_flagging=[argument_node.label], arg_map=arg_map, tc=tc)
                if conclusion_prop is None:
                    conclusion_prop = Proposition(content=new_value)
                    arg_map.add_proposition(conclusion_prop)

                try:
                    # reference new proposition
                    arg_map.update_node(argument_node.label, {"conclusion": conclusion_prop.id})
                    # maybe delete old proposition if now unused
                    arg_map.maybe_remove_unused_proposition(old_conclusion_prop.id) if old_conclusion_prop else None
                except Exception as e:
                    return tc.failure(
                        f"✗ Failed to update conclusion for argument node `<{label}>`: {str(e)}",
                        error=str(e),
                    ).build()
                
                utils.flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                return tc.success(
                    f"✓ Updated conclusion of argument node `<{label}>` {('from `' +textwrap.shorten(old_value, width=40) + '`') if old_value else ''} to `{textwrap.shorten(new_value or '', width=40)}`.",
                    result=arg_map.get_info_argument_node(argument_node, verbose=False),
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
                    result=arg_map.get_info_argument_node(argument_node, verbose=False),
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
                    result=arg_map.get_info_argument_node(argument_node, verbose=False),
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

    return CallToolResult(content=[])


@mcp.tool()
def update_metadata(
    label: NodeLabel,
    field: str,
    new_value: str | None,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Update metadata for a node in the argument map.

    Args:
        label: The label of the node to update.
        field: The metadata field to update.
        new_value: The new value for the specified metadata field. If None, the field is removed.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            if not arg_map.is_node(label):
                return tc.failure(
                    f"✗ Node `[{label}]` does not exist.", error="NodeNotFound"
                ).build()
            node = arg_map.get_node(label)

            old_metadata = node.metadata.copy()
            updated_metadata = old_metadata.copy()
            if new_value is None:
                if field in updated_metadata:
                    del updated_metadata[field]
                    tc.note(
                        f"Removing metadata field `{field}` from node `[{label}]` (`new_value=None`)."
                    )
            else:
                updated_metadata[field] = new_value

            try:
                arg_map.update_node(node.label, {"metadata": updated_metadata})
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update metadata for node `[{label}]`: {str(e)}", error=str(e)
                ).build()

            return tc.success(
                f"✓ Updated metadata field `{field}` of node `[{label}]`.",
                result=arg_map.get_info_claim_node(node, verbose=False)
                if isinstance(node, ClaimNode)
                else arg_map.get_info_argument_node(node, verbose=False),
            ).build()

        except Exception as e:
            return tc.failure(
                f"✗ Failed to update metadata for node `[{label}]`: {str(e)}", error=str(e)
            ).build()


@mcp.tool()
def update_tags(
    label: NodeLabel,
    old_value: str | None,
    new_value: str | None,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Update tags for a node in the argument map.

    Args:
        label: The label of the node to update.
        old_value: The tag to remove (if any).
        new_value: The tag to add (if any).
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            if not arg_map.is_node(label):
                return tc.failure(
                    f"✗ Node `[{label}]` does not exist.", error="NodeNotFound"
                ).build()
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
                    tc.note(f"Removing tag `{old_value}` from node `[{label}]`.")
                else:
                    tc.note(f"Tag `{old_value}` not found in node `[{label}]`; nothing to remove.")
            if new_value is not None:
                if new_value not in updated_tags:
                    updated_tags.add(new_value)
                    tc.note(f"Adding tag `{new_value}` to node `[{label}]`.")
                else:
                    tc.note(f"Tag `{new_value}` already present in node `[{label}]`; nothing to add.")

            try:
                arg_map.update_node(node.label, {"tags": list(updated_tags)})
            except Exception as e:
                return tc.failure(
                    f"✗ Failed to update tags for node `[{label}]`: {str(e)}", error=str(e)
                ).build()

            return tc.success(
                f"✓ Updated tags for node `[{label}]`.",
                result=arg_map.get_info_claim_node(node, verbose=False)
                if isinstance(node, ClaimNode)
                else arg_map.get_info_argument_node(node, verbose=False),
            ).build()

        except Exception as e:
            return tc.failure(
                f"✗ Failed to update tags for node `[{label}]`: {str(e)}", error=str(e)
            ).build()



@mcp.tool()
def update_premises(
    label: NodeLabel,
    premise_idx: int,
    new_value: str | None,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """
    Update premises for an argument node in the argument map.

    Args:
        label: The label of the argument node to update.
        premise_idx: The index of the premise to update.
        new_value: The content of the premise to add (if any). If None, the premise at premise_idx is removed.

    If premise_idx refers to a valid index of the premises list, 
    the corresponding premise is updated or removed.
    If premise_idx is out of range, a new premise is added.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            argument_node = arg_map.get_argument(label)
            if not argument_node:
                return tc.failure(
                    f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
                ).build()

            premise_nodes = [arg_map.get_proposition(pid) for pid in argument_node.premises]
            if any(p is None for p in premise_nodes):
                tc.note(
                    f"Found and cleaned up non-existing premises in argument `<{label}>`.",
                    priority=0.2,
                )
            premise_nodes = [p for p in premise_nodes if p is not None]
            premise_node = premise_nodes[premise_idx - 1] if 0 < premise_idx <= len(premise_nodes) else None
                
            if premise_node is None:
                if new_value is None:
                    return tc.failure(
                        f"✗ Cannot remove non-existing premise at index {premise_idx} of argument `<{label}>`.",
                        error="InvalidPremiseIndex",
                    ).build()
                if new_value.strip() == "":
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
                    result=arg_map.get_info_argument_node(argument_node, verbose=False),
                ).build()
            else:
                if new_value is not None and new_value.strip() == "":
                    return tc.failure(
                        f"✗ Cannot update premise at index {premise_idx} of argument `<{label}>` to an empty value.",
                        error="EmptyPremiseContent",
                    ).build()

                if new_value is not None and premise_node.content == new_value:
                    return tc.failure(
                        f"✗ Old premise content and new_value are the same (`{premise_node.content}`) for updating premises of argument `<{label}>`.",
                        error="SamePremiseValuesProvided",
                    ).build()

                if new_value is None:
                    premise_nodes.pop(premise_idx - 1)
                    arg_map.update_node(
                        argument_node.label,
                        {"premises": [p.id for p in premise_nodes if p is not None]},
                    )
                    arg_map.maybe_remove_unused_proposition(premise_node.id)
                    utils.flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                    return tc.success(
                        f"✓ Removed premise '({premise_idx}) {textwrap.shorten(premise_node.content, 30)}' from argument `<{label}>`.",
                        result=arg_map.get_info_argument_node(argument_node, verbose=False),
                    ).build()

                if new_value is not None:
                    utils.update_proposition(premise_node.id, {"content": new_value}, exempt_nodes_flagging=[argument_node.label], arg_map=arg_map, tc=tc)
                    utils.flag_relations_as_needing_review(argument_node.label, arg_map, tc)
                    return tc.success(
                        f"✓ Updated premise '({premise_idx}) {textwrap.shorten(premise_node.content, 30)}' of argument `<{label}>` to '{textwrap.shorten(new_value, 30)}'.",
                        result=arg_map.get_info_argument_node(argument_node, verbose=False),
                    ).build()
        except Exception as e:
            return tc.failure(
                f"✗ Failed to update premises for argument `<{label}>`: {str(e)}", error=str(e)
            ).build()


@mcp.tool()
def delete_claim(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """
    Delete a claim node from the argument map.

    Args:
        label: The label of the claim node to delete.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            claim_node = arg_map.get_claim(label)
            if not claim_node:
                return tc.failure(
                    f"✗ Claim node `[{label}]` does not exist.", error="NodeNotFound"
                ).build()

            ref_propIDs = [claim_node.proposition_id]
            ref_propIDs = [prop_id for prop_id in ref_propIDs if arg_map.is_proposition(prop_id)]

            arg_map.delete_node(label)
            for prop_id in ref_propIDs:
                arg_map.maybe_remove_unused_proposition(prop_id)
            return tc.success(f"✓ Deleted claim node `[{label}]`.").build()

        except Exception as e:
            return tc.failure(
                f"✗ Failed to delete claim `[{label}]`: {str(e)}", error=str(e)
            ).build()

@mcp.tool()
def delete_argument(
    label: NodeLabel,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """
    Delete an argument node from the argument map.

    Args:
        label: The label of the argument node to delete.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map

    with tool_context(arg_map) as tc:
        try:
            argument_node = arg_map.get_argument(label)
            if not argument_node:
                return tc.failure(
                    f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
                ).build()

            ref_propIDs = argument_node.premises + [argument_node.conclusion]
            ref_propIDs = [prop_id for prop_id in ref_propIDs if arg_map.is_proposition(prop_id)]

            arg_map.delete_node(label)
            for prop_id in ref_propIDs:
                arg_map.maybe_remove_unused_proposition(prop_id)
            return tc.success(f"✓ Deleted argument node `<{label}>`.").build()

        except Exception as e:
            return tc.failure(
                f"✗ Failed to delete argument `<{label}>`: {str(e)}", error=str(e)
            ).build()
