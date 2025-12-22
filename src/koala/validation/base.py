"""ValidationPipeline class for chainable validation."""


from koala.graph.argument_map import ArgumentMap
from koala.tools.tool_context import ToolContext
from koala.validation.completeness import check_completeness
from koala.validation.consistency import check_consistency
from koala.validation.connectivity import check_connectivity
from koala.validation.grounding import check_grounding


def validate_argument_map(arg_map: ArgumentMap, tc: ToolContext, fix: bool=False) -> None:
    """Validate the argument map using a series of validation steps.

    Args:
        arg_map: The argument map to validate.
        tc: The tool context.
        fix: If True, attempt to automatically fix certain issues.

    Returns:
        None
    """
    
    if tc.mode != "sketch":
        check_grounding(arg_map, tc, fix)
        check_completeness(arg_map, tc, fix)
        check_consistency(arg_map, tc, fix)

    check_connectivity(arg_map, tc, fix)

