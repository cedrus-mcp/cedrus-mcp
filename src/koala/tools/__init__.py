"""MCP tools for argument map manipulation."""

from typing import Literal

from .tools import (
    add,
    edit,
    remove,
    connect,
    mode,
)


# This generates the literal type values
ToolName = Literal[
    "add",
    "edit",
    "remove",
    "connect",
    "mode",
]

__all__ = [
    "add",
    "edit",
    "remove",
    "connect",
    "mode",
    "ToolName",
]


