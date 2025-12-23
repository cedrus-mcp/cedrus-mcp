"""Completeness validation checks."""

from koala.graph.argument_map import ArgumentMap
from koala.tools import relation_authoring
from koala.tools.tool_context import ToolContext
from koala.utils.relations import has_grounding


def check_completeness(arg_map: ArgumentMap, tc: ToolContext, fix: bool = False, max_issues: int | None = None) -> int:
    """Check that every dialectical relation that can be derived from the internal structure of nodes is present in the argument map.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        The number of issues found.
    """

    issues_found = 0

    # iterate over all node pairs
    for from_label in arg_map.list_node_labels():
        for to_label in arg_map.list_node_labels():
            if max_issues is not None and issues_found >= max_issues:
                break
            if from_label == to_label:
                continue

            # check for missing support relation
            if has_grounding(from_label, to_label, "support", arg_map):
                relation = arg_map.get_dialectic_relation(from_label, to_label)
                if not relation or relation.relation_type != "support":
                    issues_found += 1
                    if fix:
                        # automatically add the missing support relation
                        _ = relation_authoring.new_support_relation(
                            from_label=from_label,
                            to_label=to_label,
                            target_premise_idx=None,
                            grounding_strategy=None,
                            arg_map=arg_map,
                            tc=tc,
                        )
                        continue
                    else:
                        message = f"Missing support relation from {from_label} to {to_label} based on internal structure."
                        tc.issue("warning", message, label=to_label)
                        tc.suggest(
                            "connect",
                            {
                                "from": from_label,
                                "to": to_label,
                                "relation_options": {"relation_type": "support"},
                            },
                            f"Add a support relation from {from_label} to {to_label} that reflects the internal premise-conclusion structure.",
                            "fix",
                        )

            # check for missing attack relation
            if has_grounding(from_label, to_label, "attack", arg_map):
                relation = arg_map.get_dialectic_relation(from_label, to_label)
                if not relation or relation.relation_type != "attack":
                    issues_found += 1
                    if fix:
                        # automatically add the missing attack relation
                        _ = relation_authoring.new_attack_relation(
                            from_label=from_label,
                            to_label=to_label,
                            target_premise_idx=None,
                            grounding_strategy=None,
                            arg_map=arg_map,
                            tc=tc,
                        )
                        continue
                    else:
                        message = f"Missing attack relation from {from_label} to {to_label} based on internal structure."
                        tc.issue("warning", message, label=to_label)
                        tc.suggest(
                            "connect",
                            {
                                "from": from_label,
                                "to": to_label,
                                "relation_options": {"relation_type": "attack"},
                            },
                            f"Add an attack relation from {from_label} to {to_label} that reflects the internal premise-conclusion structure.",
                            "fix",
                        )

    return issues_found
