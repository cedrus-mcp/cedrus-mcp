"""Mode-specific MCP tool entrypoints.

This package defines the MCP-visible tool entrypoints for each mode
(`sketch`, `elaborate`, `review`). Each module exposes functions whose
names match the public tool names (e.g. ``add_claim``, ``inspect_graph``,
``validate``) and a ``register_*_tools()`` function that populates the
global :class:`cedrus.tools.tool_registry.ToolRegistry`.

The entrypoints are thin adapters over the shared implementations in
``cedrus.tools.impl``. They are responsible only for:

* Selecting appropriate defaults per mode
* Passing through arguments to ``*_core`` functions in ``impl``
* Registering the correct :class:`ToolVariant` metadata
"""

__all__ = [
    "sketch",
    "elaborate",
    "review",
]
