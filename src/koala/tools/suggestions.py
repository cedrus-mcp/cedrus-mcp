"""Elaborating tools: new_claim, new_argument, new_support, new_attack."""

from mcp.server.fastmcp.utilities.logging import get_logger

from koala.graph.argument_map import ArgumentMap
from koala.models import (
    NodeLabel,
)
from koala.models.nodes import ClaimNode
from koala.tools.tool_context import ToolContext

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger



def add_suggestions_after_adding_node(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:

    ## CLAIM NODE has been added ##

    if claim_added := arg_map.get_claim(label):

        # Add suggestions to replace dummy proposition if needed
        prop = arg_map.get_proposition(claim_added.proposition_id)
        if prop and prop.is_dummy:
            tc.suggest_update_field(
                label,
                "proposition",
                f"Replace dummy proposition in claim `[{label}]`.",
            )
            return

        # No further suggestions if critical issues
        if any(issue.severity in ["warning", "error"] for issue in tc.issues):
            return

        if tc.mode in ["sketch", "elaborate"]:
            if len(arg_map.list_node_labels()) > 1:
                tc.suggest(
                    "inspect_graph",
                    {},
                    f"Inspect the current argument map to get an overview of all existing nodes and their relations, which can help in deciding how to further connect claim `[{label}]`.",
                    action_type="explore",
                )
            # Suggest connecting to existing arguments if isolated
            if not arg_map.get_supported(label) and not arg_map.get_attacked(label) and len(arg_map.list_arguments()) > 1:
                relation_options = {"relation_type": "support"}
                reason = f"Try to identify an existing argument that is supported by claim `[{label}]`, and declare a corresponding support relation."
                if tc.mode == "elaborate":
                    relation_options["target_premise_idx"] = "TARGET_PREMISE_IDX"
                    reason += " Optionally specify the target premise index to connect to the appropriate premise of the argument."
                tc.suggest(
                    "connect",
                    {
                        "source": label,
                        "target": "Existing-Argument-Label",
                        **relation_options
                    },
                    reason,
                    action_type="connect",
                )
                relation_options = {"relation_type": "attack"}
                reason = f"Try to identify an existing argument that is attacked by claim `[{label}]`, and declare a corresponding attack relation."
                if tc.mode == "elaborate":
                    relation_options["target_premise_idx"] = "TARGET_PREMISE_IDX"
                    reason += " Optionally specify the target premise index to connect to the appropriate premise (negated by the claim) of the argument."
                tc.suggest(
                    "connect",
                    {
                        "source": label,
                        "target": "Existing-Argument-Label",
                        **relation_options
                    },
                    reason,
                )

        if tc.mode in ["sketch"]:
            # Suggest adding supporting/attacking arguments if none exist
            if not arg_map.get_supporters(label):
                tc.suggest(
                    "add_argument",
                    {
                        "label": "Supporting-Argument-Label",
                        "gist": "Key point of new supporting argument goes here",
                    },
                    f"Explore pros and cons. Step 1: Add a new supporting argument for claim `[{label}]`.",
                    action_type="expand",
                ).suggest(
                    "connect",
                    {
                        "source": "Supporting-Argument-Label",
                        "target": label,
                        "relation_type": "support"
                    },
                    f"Explore pros and cons. Step 2: Connect the new supporting argument to claim `[{label}]`.",
                    action_type="expand",
                )

            if not arg_map.get_attackers(label):
                tc.suggest(
                    "add_argument",
                    {
                        "label": "Attacking-Argument-Label",
                        "gist": "Key point of new attacking argument goes here",
                    },
                    f"Explore pros and cons. Step 1: Add a new attacking argument against claim `[{label}]`.",
                    action_type="expand",
                ).suggest(
                    "connect",
                    {
                        "source": "Attacking-Argument-Label",
                        "target": label,
                        "relation_type": "attack"
                    },
                    f"Explore pros and cons. Step 2: Connect the new attacking argument to claim `[{label}]`.",
                    action_type="expand",
                )

            # Suggest connecting from existing arguments
            if arg_map.has_non_supporting_arguments():
                tc.suggest(
                    "connect",
                    {
                        "source": "EXISTING_ARGUMENT_LABEL",
                        "target": label,
                        "relation_type": "support"
                    },
                    f"Having investigated whether any argument supports claim `[{label}]`: connect the two nodes correspondingly.",
                    action_type="expand",
                )
            if arg_map.has_non_attacking_arguments():
                tc.suggest(
                    "connect",
                    {
                        "source": "EXISTING_ARGUMENT_LABEL",
                        "target": label,
                        "relation_type": "attack"
                    },
                    f"Having investigated whether any argument attacks claim `[{label}]`: connect the two nodes correspondingly.",
                    action_type="expand",
                )

    ## ARGUMENT NODE has been added ##

    elif argument_added := arg_map.get_argument(label):
        # Add suggestions only if no critical issues
        if any(issue.severity in ["warning", "error"] for issue in tc.issues) and tc.mode in ["sketch", "elaborate"]:
            return
        
        if len(arg_map.list_node_labels()) > 1:
            tc.suggest(
                "inspect_graph",
                {},
                f"Inspect the current argument map to get an overview of all existing nodes and their relations, which can help in deciding how to further connect claim `[{label}]`.",
                action_type="explore",
            )


        # Suggest adding gist if missing
        if not argument_added.gist:
            tc.suggest_update_field(
                label,
                "gist",
                f"Summarize the key point of argument `<{label}>` by adding a gist.",
            )

        if tc.mode == "sketch":
            # suggest to connect to existing arguments or claims
            if not arg_map.get_attacked(label) and not arg_map.get_supported(label) and len(arg_map.list_node_labels()) > 1:
                tc.suggest(
                    "connect",
                    {
                        "source": label,
                        "target": "Claim-Or-Argument-Label",
                        "relation_type": "SUPPORT_OR_ATTACK"
                    },
                    "Explore whether any existing argument or claim is supported or attacked by this argument, and add a corresponding dialectical relation to the argument map.",
                )
            if not arg_map.get_supporters(label):
                tc.suggest_support_argument(
                    label=label,
                    reason=f"Add a further argument which supports <{label}>."
                )
            if not arg_map.get_attackers(label):
                tc.suggest_attack_argument(
                    label=label,
                    reason=f"Add a further argument which attacks <{label}>."
                )
            if target_node_labels := arg_map.get_supported(label):
                if target_node := arg_map.get_node(target_node_labels[0]):
                    reason = "Further add a different argument which supports"
                    if isinstance(target_node, ClaimNode):
                        reason += f" claim [{target_node.label}]."
                    else:
                        reason += f" argument <{target_node.label}>."
                    tc.suggest_support_argument(label=target_node.label, reason=reason)
            
        if tc.mode == "elaborate":

            tc.suggest(
                "inspect_node",
                {
                    "label": label,
                },
                f"Inspect the details of argument `<{label}>` to review and possibly improve its content and structure.",
                action_type="explore",
            )

            if not argument_added.conclusion:
                tc.suggest_update_field(label=argument_added.label, field="conclusion", reason="State explicitly the conclusion of this argument.")
                tc.suggest(
                    "connect",
                    {
                        "source": argument_added.label,
                        "target": "Claim-Label",
                        "relation_type": "support",
                        "grounding_strategy": "copy_premise"
                    },
                    f"Specify the conclusion of this newly added argument <{argument_added.label}> by connecting it to a corresponding existing claim.",
                    "consolidate"
                )
                tc.suggest(
                    "connect",
                    {
                        "source": argument_added.label,
                        "target": "Argument-Label",
                        "relation_type": "support",
                        "target_premise_idx": "TARGET_PREMISE_IDX",
                        "grounding_strategy": "copy_premise"
                    },
                    f"Specify the conclusion of this newly added argument <{argument_added.label}> by connecting it to a corresponding existing argument (whose premise at the given target idx will serve as conclusion).",
                    "consolidate"
                )
                return
            if not argument_added.premises or len(argument_added.premises) < 2:
                tc.suggest(
                    "edit",
                    {
                        "label": label,
                        "field": "premises",
                        "edit_options": {
                            "premise_idx": 1,
                            "new_value": "PREMISE_TEXT"
                        }
                    },
                    "Add a premise with content PREMISE_TEXT to this argument, which is used and required to infer the conclusion. Repeat as necessary.",
                    "consolidate"
                )
                tc.suggest(
                    "connect",
                    {
                        "source": "CLAIM_OR_ARGUMENT_LABEL",
                        "target": label,
                        "relation_type": "support",
                        "grounding_strategy": "copy_conclusion",
                    },
                    f"Specify a premise of <{argument_added.label}> by connecting an existing claim or argument (whose proposition or conclusion will serve as premise).",
                    "consolidate"
                )
                return

            # Suggest support for premises or argument
            if argument_added.premises:
                tc.suggest_support_argument(
                    label,
                    f"Add a new supporting argument that backs up premise (TARGET_PREMISE_IDX) of argument `<{label}>`.",
                    target_premise_idx="TARGET_PREMISE_IDX",
                )
                tc.suggest_attack_argument(
                    label,
                    f"Add a new attacking argument that attacks premise (TARGET_PREMISE_IDX) of argument `<{label}>`.",
                    target_premise_idx="TARGET_PREMISE_IDX",
                )

        elif tc.mode == "review":
            tc.suggest(
                "validate",
                {},
                f"Review the argument `<{label}>`, and (re-)run all validations on the entire argument map.", 
            )






