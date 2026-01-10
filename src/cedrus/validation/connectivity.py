"""Connectivity validation checks."""

from cedrus.graph.argument_map import ArgumentMap
from cedrus.tools.runtime.tool_context import ToolContext


def check_connectivity(
    arg_map: ArgumentMap, tc: ToolContext, fix: bool = False, max_issues: int | None = None
) -> int:
    """Check that the argument map is fully connected.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        The number of issues found.
    """

    issues_found = 0

    connected_components = arg_map.connected_components()
    num_components = len(connected_components)
    if num_components > 1:
        roots = arg_map.list_roots()
        cc_roots: list[str] = []
        for e, cc in enumerate(connected_components):
            cc_roots.append(
                f"component {e} root(s): " + ", ".join([node for node in roots if node in cc])
            )

        message = f"Argument map has {num_components} disconnected components."
        message += (
            f" Consider connecting the components via their root nodes ({'; '.join(cc_roots)})."
        )
        tc.issue("warning", message)
        issues_found += 1

    return issues_found
