"""Validation-related MCP tool implementations.

This module hosts the core implementation for validation tools, refactored
out of :mod:`cedrus.tools.tools`.

The primary entrypoint is :func:`validate_core`, which mirrors the behavior
of the legacy ``validate`` tool.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult

from cedrus.tools.runtime import tool_context
from cedrus.validation import validate_argument_map

if TYPE_CHECKING:
    from cedrus.server import AppContext


logger = get_logger("cedrus.tools.impl.validation")


def validate_core(
    *,
    ctx: Context[ServerSession, AppContext],
    fix: bool = False,
    max_issues: int | None = None,
) -> CallToolResult:
    """Validate the current argument map for consistency and completeness.

    This is a direct port of :func:`cedrus.tools.tools.validate` with the
    same behavior and messaging.
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context.tool_context(arg_map, mode) as tc:
        if tc.mode == "sketch":
            tc.issue("info", "Validation may be limited in `sketch` mode.")

        try:
            issues_found = validate_argument_map(arg_map, tc, fix=fix, max_issues=max_issues)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(f"Error during argument map validation: {str(e)}")
            return tc.failure(f"✗ Failed to validate argument map: {str(e)}", error=str(e)).build()

        if not any(issue.severity == "error" for issue in tc.issues):
            tc.success("✓ Argument map is valid and consistent.")
        else:
            tc.success(
                f"✗ Argument map has {issues_found} issues.",
            )
            if not fix:
                tc.suggest(
                    "validate",
                    {"fix": True},
                    "Run validate with fix=True to attempt automatic corrections.",
                )

        return tc.build()


__all__ = ["validate_core"]
