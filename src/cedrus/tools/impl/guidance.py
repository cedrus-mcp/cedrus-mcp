"""Guidance-related MCP tool implementations.

This module hosts the core implementation for guidance/instruction tools,
refactored out of :mod:`cedrus.tools.tools`.

The intent is to provide a unified ``get_instructions_core`` function that
can serve both the basic instructions tool and the elaborate/topic-specific
variant, while preserving the legacy behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult
from pydantic import AnyUrl

from cedrus.tools.runtime import tool_context

if TYPE_CHECKING:
    from cedrus.server import AppContext


logger = get_logger("cedrus.tools.impl.guidance")


async def get_instructions_core(
    *,
    ctx: Context[ServerSession, AppContext],
    topic: Literal["grounding", "validity", "none"] | None = None,
    mode: str | None = None,
) -> CallToolResult:
    """Unified instructions tool.

    This combines the behavior of ``get_instructions`` and
    ``get_instructions_elaborate`` from :mod:`cedrus.tools.tools`.

    Semantics:
        - If ``topic`` is ``None`` or ``"none"``, behave like legacy
          ``get_instructions`` (general instructions for current mode).
        - If ``topic`` is ``"grounding"`` or ``"validity"``, behave like
          ``get_instructions_elaborate(topic=...)`` and return
          topic-specific instructions.

    ``mode`` is currently advisory only; the concrete behavior is
    driven by the underlying resource functions, exactly as before.
    """

    # Normalize topic
    normalized_topic: Literal["grounding", "validity", "none"]
    if topic is None:
        normalized_topic = "none"
    else:
        normalized_topic = topic

    # General instructions path (legacy get_instructions)
    if normalized_topic == "none":
        arg_map = ctx.request_context.lifespan_context.arg_map
        current_mode = ctx.request_context.lifespan_context.mode

        with tool_context.tool_context(arg_map, current_mode) as tc:
            try:
                import cedrus.resources

                text = await cedrus.resources.instructions.instruction_resource()
                tc.embed_resource(uri=AnyUrl("argmap://instructions"), text=text)
            except Exception as e:  # pragma: no cover - defensive logging
                logger.error(f"Error embedding instructions resource: {str(e)}")
                return tc.failure(
                    f"✗ Failed to embed instructions resource: {str(e)}", error=str(e)
                ).build()

        tc.success("✓ Printed instructions.")
        return tc.build()

    # Topic-specific instructions path (legacy get_instructions_elaborate)
    arg_map = ctx.request_context.lifespan_context.arg_map
    current_mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, current_mode) as tc:
        try:
            import cedrus.resources

            if normalized_topic == "grounding":
                text = cedrus.resources.instructions.instructions_grounding()
                return tc.success("✓ Providing grounding instructions.", result=text).build()
            if normalized_topic == "validity":
                text = cedrus.resources.instructions.instructions_validity()
                return tc.success("✓ Providing validity instructions.", result=text).build()

            # Unknown topic – keep legacy error message wording
            return tc.failure(
                f"Unknown topic '{normalized_topic}' for elaborate instructions. Available topics: 'grounding', 'validity'.",
                error="UnknownTopic",
            ).build()
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                f"Error providing elaborate instructions for topic '{normalized_topic}': {str(e)}"
            )
            return tc.failure(
                f"✗ Error providing `elaborate` instructions for topic '{normalized_topic}'",
                error=str(e),
            ).build()


__all__ = ["get_instructions_core"]
