"""ValidationPipeline class for chainable validation."""


from cedrus.graph.argument_map import ArgumentMap
from cedrus.tools.tool_context import ToolContext
from cedrus.validation.completeness import check_completeness
from cedrus.validation.consistency import check_consistency
from cedrus.validation.connectivity import check_connectivity
from cedrus.validation.grounding import check_grounding
from cedrus.validation.content import check_core_content, check_argument_structure


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

    issues_found += check_core_content(arg_map, tc, fix, max_issues)

    if tc.mode != "sketch":
        issues_found += check_argument_structure(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)
        issues_found += check_grounding(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)
        issues_found += check_completeness(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)
        issues_found += check_consistency(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)

    issues_found += check_connectivity(arg_map, tc, fix, max_issues - issues_found if max_issues is not None else None)

    return issues_found

