"""Node detail resources: detailed node information and context."""


from koala.graph.rendering import render_argdown_node
from koala.models.base import NodeLabel
from koala.server import mcp

@mcp.resource("argmap://node/details/{label}")
async def node_details_resource(label: NodeLabel) -> str:
    """Provide a detailed argdown representation of a single node."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    rendering = render_argdown_node(
        app_ctx.arg_map,
        label=label,
        details=app_ctx.mode in ["elaborate", "review"],
    )
    return f"```argdown\n{rendering}\n```"