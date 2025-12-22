"""Grounding validation checks."""

from koala.graph.argument_map import ArgumentMap
from koala.tools.tool_context import ToolContext
from koala.utils.relations import is_grounded_relation


def check_grounding(arg_map: ArgumentMap, tc: ToolContext, fix: bool = False) -> None:
    """Checks that all dialectical relations in the argument map are properly grounded.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.
    """

    # check support relations
    for from_label, to_label in arg_map.list_support_relations():
        if not is_grounded_relation(from_label, to_label, "support", arg_map):
            message = f"Support relation from {from_label} to {to_label} is not properly grounded."
            tc.issue("error", message, label=to_label)
            tc.suggest(
                "connect",
                {
                    "from": from_label,
                    "to": to_label,
                    "relation_options": {"relation_type": "support"},
                },
                f"Ensure that the support relation from {from_label} to {to_label} is grounded in internal premise conclusion structure of adjacent nodes.",
                "fix",
            )
    # check attack relations
    for from_label, to_label in arg_map.list_attack_relations():
        if not is_grounded_relation(from_label, to_label, "attack", arg_map):
            message = f"Attack relation from {from_label} to {to_label} is not properly grounded."
            tc.issue("error", message, label=to_label)
            tc.suggest(
                "connect",
                {
                    "from": from_label,
                    "to": to_label,
                    "relation_options": {"relation_type": "attack"},
                },
                f"Ensure that the attack relation from {from_label} to {to_label} is grounded in internal premise conclusion structure of adjacent nodes.",
                "fix",
            )
