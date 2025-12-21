"""Graph view resources: summary, nodes, claims, arguments."""


from koala.graph.rendering import render_argdown
from koala.models.base import NodeLabel
from koala.server import mcp

@mcp.resource("argmap://graph/thin")
async def graph_thin_resource() -> str:
    """Provide a thin argdown representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    rendering = render_argdown(app_ctx.arg_map, label_only=True)
    return f"```argdown\n{rendering}\n```"


@mcp.resource("argmap://graph/details")
async def graph_details_resource() -> str:
    """Provide a detailed argdown representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    rendering = render_argdown(app_ctx.arg_map, label_only=False, extra_tags=app_ctx.mode in ['author', 'review'])
    return f"```argdown\n{rendering}\n```"


@mcp.resource("argmap://neighborhood/{label}/{k}")
async def neighborhood_details_resource(label: NodeLabel, k: int) -> str:
    """Provide a detailed argdown representation of the k-neighborhood of node `label`."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    neighborhood = app_ctx.arg_map.get_k_neighborhood(label, k)
    rendering = render_argdown(app_ctx.arg_map, subset=neighborhood, label_only=False, extra_tags=app_ctx.mode in ['author', 'review'])
    return f"```argdown\n{rendering}\n```"