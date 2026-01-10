"""Public MCP tools facade.

This module provides the canonical public surface for the ``cedrus.tools``
package. It exposes

* :data:`TOOL_ORDER` – canonical tool ordering for presentation
* :data:`TOOL_REGISTRY` – global :class:`ToolRegistry` instance

and wires up all mode-specific tool variants by importing the entrypoint
registration helpers.

Code that previously imported from :mod:`cedrus.tools.tools` should
incrementally migrate to import from :mod:`cedrus.tools` instead, e.g.::

    from cedrus.tools import TOOL_ORDER, TOOL_REGISTRY

The legacy :mod:`cedrus.tools.tools` module is kept as a thin facade for
backwards compatibility during the refactor.
"""

from __future__ import annotations

from typing import Literal, TYPE_CHECKING

from cedrus.tools.tool_registry import TOOL_REGISTRY
from cedrus.tools.entrypoints.sketch import register_sketch_tools
from cedrus.tools.entrypoints.elaborate import register_elaborate_tools
from cedrus.tools.entrypoints.review import register_review_tools


# Public tool order (family-level)
TOOL_ORDER: list[str] = [
    "add_claim",
    "add_argument",
    "edit",
    "remove",
    "connect",
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    "get_instructions",
    "validate",
    "switch_mode",
    "reset_graph",
]


def _register_tool_variants() -> None:
    """Register all tool variants for all modes.

    Called at import time so that :data:`TOOL_REGISTRY` is fully populated
    when the MCP server starts up.
    """

    register_sketch_tools()
    register_elaborate_tools()
    register_review_tools()


# Initialize registry on import
_register_tool_variants()


# This generates the literal type values for tool names used in type hints.
ToolName = Literal[
    "add_claim",
    "add_argument",
    "edit",
    "remove",
    "connect",
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    "get_instructions",
    "validate",
    "switch_mode",
    "reset_graph",
]


__all__ = [
    "ToolName",
    "TOOL_ORDER",
    "TOOL_REGISTRY",
]
