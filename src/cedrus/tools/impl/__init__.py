"""Shared MCP-level tool implementations for CEDRUS.

This package contains mode-aware but signature-agnostic implementations
that back the MCP tool entrypoints. Functions here are typically named
``*_core`` and accept the superset of parameters across modes.

During the migration away from :mod:`cedrus.tools.tools`, existing
wrappers delegate to these core implementations so behavior remains
unchanged while the layout becomes mode-first.
"""

from . import editing, inspection, guidance, validation, meta

__all__ = [
    "editing",
    "inspection",
    "guidance",
    "validation",
    "meta",
]
