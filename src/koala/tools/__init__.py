"""MCP tools for argument map manipulation."""

from typing import Literal

# Trigger tool registration
from . import tools   # noqa: F401

# This generates the literal type values
ToolName = Literal[
    "add_claim",
    "add_argument",
    "edit",
    "remove",
    "connect",
    "inspect_graph",
    "inspect_neighborhood",
    "inspect_node",
    "instructions",
    "validate",
    #"export_svg",
    "set_mode",
]

__all__ = [
    "ToolName",
]


