"""Completeness validation checks."""

from koala.graph.argument_map import ArgumentMap
from koala.models.nodes import ArgumentNode, ClaimNode
from koala.tools.tool_context import ToolContext


def check_core_content(arg_map: ArgumentMap, tc: ToolContext, fix: bool = False, max_issues: int | None = None) -> int:
    """Check that every node has gist / proposition.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        The number of issues found.
    """

    issues_found = 0

    # iterate over all node pairs
    for label in arg_map.list_node_labels():
        if max_issues is not None and issues_found >= max_issues:
            break

        node = arg_map.get_node(label)
        if node is None:
            issues_found += 1
            message = f"Node {label} is missing."
            tc.issue("error", message, label=label)
            continue

        if isinstance(node, ClaimNode):
            proposition = arg_map.get_proposition(node.proposition_id)
            if proposition is None or not proposition.content.strip():
                issues_found += 1
                message = f"Claim node {label} is missing a proposition."
                tc.issue("warning", message, label=label)
                tc.suggest(
                    "edit",
                    {
                        "label": label,
                        "field": "proposition",
                        "edit_options": {
                            "new_value": "Add a proposition here."
                        },
                    },
                    f"Add a proposition to claim node {label}.",
                    "fix",
                )

        if isinstance(node, ArgumentNode):
            if node.gist is None or not node.gist.strip():
                issues_found += 1
                message = f"Argument node {label} is missing a gist."
                tc.issue("warning", message, label=label)
                tc.suggest(
                    "edit",
                    {
                        "label": label,
                        "field": "gist",
                        "edit_options": {
                            "new_value": "Add a gist here."
                        },
                    },
                    f"Add a gist to argument node {label}.",
                    "fix",
                )

    return issues_found


def check_argument_structure(arg_map: ArgumentMap, tc: ToolContext, fix: bool = False, max_issues: int | None = None) -> int:
    """Check that argument nodes have at least one premise and one conclusion.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.
        max_issues: The maximum number of issues to report.

    Returns:
        The number of issues found.
    """
    
    issues_found = 0

    # iterate over all argument nodes
    for label in arg_map.list_node_labels():
        if max_issues is not None and issues_found >= max_issues:
            break

        node = arg_map.get_node(label)
        if not isinstance(node, ArgumentNode):
            continue

        premises = [
            arg_map.get_proposition(p_id) for p_id in node.premises
        ]
        premises = [p for p in premises if p is not None]
        conclusion = arg_map.get_proposition(node.conclusion)

        if conclusion is None:
            issues_found += 1
            message = f"Argument node {label} is missing a conclusion."
            tc.issue("warning", message, label=label)
            tc.suggest(
                "edit",
                {
                    "label": label,
                    "field": "conclusion",
                    "edit_options": {
                        "new_value": "Add a conclusion here."
                    },
                },
                f"Add a conclusion to argument node {label}.",
                "fix",
            )
        if max_issues is not None and issues_found >= max_issues:
            break

        if len(premises) == 0:
            issues_found += 1
            message = f"Argument node {label} has no premises."
            tc.issue("warning", message, label=label)
            tc.suggest(
                "edit",
                {
                    "label": label,
                    "field": "premises",
                    "edit_options": {
                        "new_value": "Add a premise here."
                    },
                },
                f"Add a premise to argument node {label}. Repeat as necessary.",
                "fix",
            )

    return issues_found