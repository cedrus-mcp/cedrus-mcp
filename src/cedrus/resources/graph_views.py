"""Graph view resources: summary, nodes, claims, arguments."""

from typing import Literal

from cedrus.backend.graph.rendering import render_argdown, render_nested_json, render_nested_yaml
from cedrus.backend.models.base import Format, NodeLabel
from cedrus.server import mcp


@mcp.resource("argmap://graph/thin/{format}")
async def graph_thin_resource(
    format: Format = "argdown",
) -> str:
    """Provide a thin representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context

    if format in ["argdown", "tree"]:
        fmt: Literal["argdown", "tree"] = format  # type: ignore[assignment]
        rendering = render_argdown(app_ctx.arg_map, label_only=True, format=fmt)
        return f"```argdown\n{rendering}\n```"

    if format == "json-nested":
        rendering = render_nested_json(app_ctx.arg_map, detailed=False, extra_tags=False)
        return f"```json\n{rendering}\n```"

    if format == "yaml-nested":
        rendering = render_nested_yaml(app_ctx.arg_map, detailed=False, extra_tags=False)
        return f"```yaml\n{rendering}\n```"

    raise RuntimeError(f"Unsupported format for thin graph view: {format}")


@mcp.resource("argmap://graph/details/{format}")
async def graph_details_resource(
    format: Format = "argdown",
) -> str:
    """Provide a detailed representation of the entire argument map."""
    app_ctx = mcp.get_context().request_context.lifespan_context

    if format in ["argdown", "tree"]:
        fmt: Literal["argdown", "tree"] = format  # type: ignore[assignment]
        rendering = render_argdown(
            app_ctx.arg_map,
            label_only=False,
            format=fmt,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```argdown\n{rendering}\n```"

    if format == "json-nested":
        rendering = render_nested_json(
            app_ctx.arg_map,
            detailed=True,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```json\n{rendering}\n```"

    if format == "yaml-nested":
        rendering = render_nested_yaml(
            app_ctx.arg_map,
            detailed=True,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```yaml\n{rendering}\n```"

    raise RuntimeError(f"Unsupported format for detailed graph view: {format}")


@mcp.resource("argmap://neighborhood/{label}/{k}")
async def neighborhood_details_resource(label: NodeLabel, k: int) -> str:
    """Provide a detailed argdown representation of the k-neighborhood of node `label`."""
    return await neighborhood_details_view(label=label, k=k, format="argdown")


async def neighborhood_details_view(
    label: NodeLabel,
    k: int,
    format: Format = "argdown",
) -> str:
    """Provide a detailed representation of the k-neighborhood of node `label`."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    neighborhood = app_ctx.arg_map.get_k_neighborhood(label, k)

    if format in ["argdown", "tree"]:
        fmt: Literal["argdown", "tree"] = format  # type: ignore[assignment]
        rendering = render_argdown(
            app_ctx.arg_map,
            subset=neighborhood,
            label_only=False,
            format=fmt,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```argdown\n{rendering}\n```"

    if format == "json-nested":
        rendering = render_nested_json(
            app_ctx.arg_map,
            subset=neighborhood,
            detailed=True,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```json\n{rendering}\n```"

    if format == "yaml-nested":
        rendering = render_nested_yaml(
            app_ctx.arg_map,
            subset=neighborhood,
            detailed=True,
            extra_tags=app_ctx.mode in ["elaborate", "review"],
        )
        return f"```yaml\n{rendering}\n```"

    raise RuntimeError(f"Unsupported format for neighborhood view: {format}")
