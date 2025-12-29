"""MCP tools for argument map manipulation."""

from typing import Literal

from .tools import (
    add,
    edit,
    remove,
    connect,
    inspect,
    instructions,
    validate,
    export_svg,
    mode,
)


# This generates the literal type values
ToolName = Literal[
    "add",
    "edit",
    "remove",
    "connect",
    "inspect",
    "instructions",
    "validate",
    "export_svg",
    "mode",
]

__all__ = [
    "add",
    "edit",
    "remove",
    "connect",
    "inspect",
    "instructions",
    "validate",
    "export_svg",
    "mode",
    "ToolName",
]


