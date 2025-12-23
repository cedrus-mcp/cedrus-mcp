"""ValidationPipeline class for chainable validation."""


from koala.graph.argument_map import ArgumentMap
from koala.tools.tool_context import ToolContext
from koala.validation.completeness import check_completeness
from koala.validation.consistency import check_consistency
from koala.validation.connectivity import check_connectivity
from koala.validation.grounding import check_grounding


def validate_argument_map(arg_map: ArgumentMap, tc: ToolContext, fix: bool=False, max_issues: int | None = None) -> int:
    """Validate the argument map using a series of validation steps.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        The number of issues found.
    """

    issues_found = 0

    if tc.mode != "sketch":
        issues_found += check_grounding(arg_map, tc, fix, max_issues)
        issues_found += check_completeness(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)
        issues_found += check_consistency(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)

    issues_found += check_connectivity(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)

    return issues_found

