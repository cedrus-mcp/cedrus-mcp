"""Node detail resources: detailed node information and context."""
from typing import Any

from koala.graph.argument_map import ArgumentMap
from koala.server import mcp

@mcp.resource("argmap://statistics")
async def statistics_resource() -> dict[str, Any]:
    """Provide descriptive statistics of the argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    arg_map: ArgumentMap = app_ctx.arg_map

    return {
        "num_nodes": len(arg_map.argument_graph.nodes),
        "num_claims": len(arg_map.list_claims()),
        "num_arguments": len(arg_map.list_arguments()),
        "num_roots": len(arg_map.list_roots()),
        "num_connected_components": len(arg_map.connected_components()),
        "is_acyclic": arg_map.is_acyclic(),
        "longest_path_length": len(arg_map.longest_path()),
        "active_editing_mode": app_ctx.mode,
    }
