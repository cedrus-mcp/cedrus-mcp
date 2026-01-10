"""Node deletion functions for the argument map."""

from mcp.types import CallToolResult

from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import NodeLabel
from cedrus.tools.runtime.tool_context import ToolContext


def delete_claim(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete a claim node from the argument map.

    Args:
        label: The label of the claim node to delete.

    Returns:
        CallToolResult with success or failure message
    """

    try:
        claim_node = arg_map.get_claim(label)
        if not claim_node:
            return tc.failure(
                f"✗ Claim node `[{label}]` does not exist.", error="NodeNotFound"
            ).build()

        ref_propIDs = [claim_node.proposition_id]
        ref_propIDs = [prop_id for prop_id in ref_propIDs if arg_map.is_proposition(prop_id)]

        arg_map.delete_node(label)
        for prop_id in ref_propIDs:
            arg_map.maybe_remove_unused_proposition(prop_id)
        return tc.success(f"✓ Deleted claim node `[{label}]`.").build()

    except Exception as e:
        return tc.failure(f"✗ Failed to delete claim `[{label}]`: {str(e)}", error=str(e)).build()


def delete_argument(
    label: NodeLabel,
    arg_map: ArgumentMap,
    tc: ToolContext,
) -> CallToolResult:
    """Delete an argument node from the argument map.

    Args:
        label: The label of the argument node to delete.

    Returns:
        CallToolResult with success or failure message
    """

    try:
        argument_node = arg_map.get_argument(label)
        if not argument_node:
            return tc.failure(
                f"✗ Argument node `<{label}>` does not exist.", error="NodeNotFound"
            ).build()

        ref_propIDs = argument_node.premises + [argument_node.conclusion]
        ref_propIDs = [prop_id for prop_id in ref_propIDs if arg_map.is_proposition(prop_id)]

        arg_map.delete_node(label)
        for prop_id in ref_propIDs:
            arg_map.maybe_remove_unused_proposition(prop_id)
        return tc.success(f"✓ Deleted argument node `<{label}>`.").build()

    except Exception as e:
        return tc.failure(
            f"✗ Failed to delete argument `<{label}>`: {str(e)}", error=str(e)
        ).build()
