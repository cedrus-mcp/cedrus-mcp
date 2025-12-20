"""Graph view resources: summary, nodes, claims, arguments."""

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from koala.graph.rendering import render_argdown
from koala.models.base import NodeLabel
from koala.server import AppContext, mcp

@mcp.resource("argmap://graph/thin")
async def graph_thin_resource() -> str:
    """Provide a thin argdown representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    return render_argdown(app_ctx.arg_map, label_only=True)


@mcp.resource("argmap://graph/details")
async def graph_details_resource() -> str:
    """Provide a detailed argdown representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    return render_argdown(app_ctx.arg_map, label_only=False, extra_tags=app_ctx.mode in ["author", "review"])


@mcp.resource("argmap://neighborhood/{label}/{k}")
async def neighborhood_details_resource(label: NodeLabel, k: int) -> str:
    """Provide a detailed argdown representation of the k-neighborhood of node `label`."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    neighborhood = app_ctx.arg_map.get_k_neighborhood(label, k)
    return render_argdown(
        app_ctx.arg_map, subset=neighborhood, label_only=False, extra_tags=app_ctx.mode in ["author", "review"]
    )
