"""Graph-editing backend helpers for MCP tools.

This package provides lower-level helpers used by
:mod:`cedrus.tools.impl.editing` and validation modules.

Public modules:

- :mod:`cedrus.tools.backend.nodes` – node creation, deletion, updates
- :mod:`cedrus.tools.backend.relations` – relation creation, grounding, review flagging
- :mod:`cedrus.tools.backend.grounding` – core grounding logic
"""

from . import nodes, relations

__all__ = ["nodes", "relations"]
