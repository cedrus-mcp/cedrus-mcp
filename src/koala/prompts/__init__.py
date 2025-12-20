"""MCP prompts for guided workflows."""

# Import all prompt modules to ensure @mcp.prompt decorators execute
from . import analysis  # noqa: F401
from . import debate  # noqa: F401
from . import reconstruction  # noqa: F401
