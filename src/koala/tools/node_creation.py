"""Node creation functions for the argument map."""

import textwrap

from koala.graph.argument_map import ArgumentMap
from koala.graph.rendering import render_argdown_node
from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.propositions import Proposition
from koala.models.relations import DialecticalRelationType
from koala.tools import utils
from koala.tools.grounding import GroundingStrategy, maybe_ground_relation
from koala.tools.tool_context import ToolContext


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
    proposition_node = utils.maybe_create_proposition_from_content(label, proposition_content=proposition, arg_map=arg_map, tc=tc)

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
    tc.issue("info", f"✓ Created new claim node `[{label}]` with proposition `{textwrap.shorten(proposition_node.content, width=50)}`.")

    # Create dialectical relation if specified
    relation_creation_fn = (
        arg_map.add_support_relation
        if relation_type == "support"
        else arg_map.add_attack_relation
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
        tc.issue("info", f"\n  Linked `{from_label}` to new claim via a `{relation_type}` relation.")
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
        conclusion_node = utils.maybe_create_proposition_from_content(
            label, proposition_content=conclusion, arg_map=arg_map, tc=tc
        )

    # Create premise propositions if provided
    premise_nodes: list[Proposition] = []
    if premises:
        for premise_content in premises:
            premise_node = utils.maybe_create_proposition_from_content(
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
    msg = f"✓ Created new argument node `<{label}>`"
    msg += f" with gist `{textwrap.shorten(gist or '', width=50)}`." if gist else "."
    tc.issue("info", msg)

    # Create dialectical relation if specified
    relation_creation_fn = (
        arg_map.add_support_relation
        if relation_type == "support"
        else arg_map.add_attack_relation
    )
    if to_label:
        relation_creation_fn(
            from_label=label, to_label=to_label, target_premise_idx=target_premise_idx
        )
        tc.issue("info", f"\n  Linked new argument to `{to_label}` via a `{relation_type}` relation.")
        maybe_ground_relation(
            label, to_label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
        )
    if from_label:
        relation_creation_fn(from_label=from_label, to_label=label)
        tc.issue("info", f"\n  Linked `{from_label}` to new argument via a `{relation_type}` relation.")
        maybe_ground_relation(
            from_label, label, relation_type, target_premise_idx, grounding_strategy, arg_map, tc
        )

    # Refresh argument_node after possible grounding updates
    refreshed_argument_node = arg_map.get_argument(label)
    if refreshed_argument_node is None:
        raise RuntimeError(f"Failed to retrieve argument node `<{label}>` after creation.")
    argument_node = refreshed_argument_node
    tc.success(
        f"✓ Created new argument node `<{label}>`.",
        result=render_argdown_node(arg_map, label, details=False),
    )
