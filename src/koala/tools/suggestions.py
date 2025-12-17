"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from mcp.server.fastmcp.utilities.logging import get_logger

from koala.graph.argument_map import ArgumentMap
from koala.models import (
    NodeLabel,
)
from koala.tools.tool_context import ToolContext

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger



def add_suggestions_after_adding_node(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> None:

    if claim_added := arg_map.get_claim(label):
        if tc.mode == "author":
            # Add suggestions to replace dummy proposition if needed
            prop = arg_map.get_proposition(claim_added.proposition_id)
            if prop and prop.is_dummy:
                tc.suggest_update_field(
                    label,
                    "proposition",
                    f"Replace dummy proposition in claim `[{label}]`.",
                )

        # Add suggestions if no critical issues
        if not tc.issues and tc.mode in ["sketch", "author"]:
            tc.suggest(
                "add",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "node_type": "argument",
                    "gist": "KEY_POINT_OF_NEW_ARGUMENT",
                    "to_label": label,
                    "relation_type": "support",
                },
                f"Explore pros and cons by adding a new supporting argument for claim `[{label}]`.",
                action_type="expand",
            )
            tc.suggest(
                "add",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "node_type": "argument",
                    "gist": "KEY_POINT_OF_NEW_ARGUMENT",
                    "to_label": label,
                    "relation_type": "attack",
                },
                f"Explore pros and cons by adding a new argument attacking claim `[{label}]`.",
                action_type="expand",
            )
            tc.suggest(
                "add",
                {
                    "label": "NEW_ARGUMENT_LABEL",
                    "node_type": "argument",
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
                        "connect",
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
                        "connect",
                        {
                            "from_label": "EXISTING_ARGUMENT_LABEL",
                            "to_label": label,
                            "relation_type": "support",
                        },
                        f"Show how claim `[{label}]` is related to other arguments by identifying a supporting argument.",
                        action_type="connect",
                    )

    elif argument_added := arg_map.get_argument(label):
        # Add suggestions if no critical issues
        if not tc.issues and tc.mode in ["sketch", "author"]:
            # Suggest support for premises or argument
            if argument_added.premises:
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
            if not argument_added.gist:
                tc.suggest_update_field(
                    label,
                    "gist",
                    f"Summarize the key point of argument `<{label}>` by adding a gist.",
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
                        label, "EXISTING_CLAIM_LABEL", "support"
                    )
                if arg_map.list_arguments():
                    tc.suggest_connect_relation(
                        label, "EXISTING_ARGUMENT_LABEL", "attack"
                    )

