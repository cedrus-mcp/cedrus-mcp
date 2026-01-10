"""Internal helper modules for cedrus.tools.

This package groups utilities that support the MCP-level tool
implementations in :mod:`cedrus.tools.impl`.

The intent is that higher-level code imports helpers from here,
e.g.::

    from cedrus.tools.backend import nodes

During the refactor, we keep thin shim modules at the old locations
(:mod:`cedrus.tools.backend.nodes`, etc.) so external callers that
import those paths continue to work.
"""

from .misc import *
