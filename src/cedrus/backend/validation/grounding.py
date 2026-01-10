"""Grounding validation checks."""

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.graph.query import is_grounded_relation
from cedrus.tools.runtime.tool_context import ToolContext


def check_grounding(
    arg_map: ArgumentMap, tc: ToolContext, fix: bool = False, max_issues: int | None = None
) -> int:
    """Checks that all dialectical relations in the argument map are properly grounded.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        The number of issues found.
    """

    issues_found = 0

    # check support relations
    for from_label, to_label in arg_map.list_support_relations():
        if max_issues is not None and issues_found >= max_issues:
            break
        if not is_grounded_relation(from_label, to_label, "support", arg_map):
            message = f"Support relation from {from_label} to {to_label} is not properly grounded."
            tc.issue("error", message, label=to_label)
            issues_found += 1
            tc.suggest(
                "connect",
                {"source": from_label, "target": to_label, "relation_type": "support"},
                f"Ensure that the support relation from {from_label} to {to_label} is grounded in internal premise conclusion structure of adjacent nodes.",
                "fix",
            )
    # check attack relations
    for from_label, to_label in arg_map.list_attack_relations():
        if max_issues is not None and issues_found >= max_issues:
            break
        if not is_grounded_relation(from_label, to_label, "attack", arg_map):
            message = f"Attack relation from {from_label} to {to_label} is not properly grounded."
            tc.issue("error", message, label=to_label)
            issues_found += 1
            tc.suggest(
                "connect",
                {"source": from_label, "target": to_label, "relation_type": "attack"},
                f"Ensure that the attack relation from {from_label} to {to_label} is grounded in internal premise conclusion structure of adjacent nodes.",
                "fix",
            )

    return issues_found
