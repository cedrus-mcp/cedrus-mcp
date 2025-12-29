"""MCP tools for argument map manipulation."""

from typing import Literal

from .tools import (
    add_claim,
    add_argument,
    edit,
    remove,
    connect,
    inspect,
    instructions,
    validate,
    #export_svg,
    mode,
)


# This generates the literal type values
ToolName = Literal[
    "add_claim",
    "add_argument",
    "edit",
    "remove",
    "connect",
    "inspect",
    "instructions",
    "validate",
    #"export_svg",
    "mode",
]

__all__ = [
    "add_claim",
    "add_argument",
    "edit",
    "remove",
    "connect",
    "inspect",
    "instructions",
    "validate",
    #"export_svg",
    "mode",
    "ToolName",
]


