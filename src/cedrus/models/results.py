# src/cedrus/models/results.py
"""Result models with next actions and validation issues."""

from typing import Any, Dict, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field

from .base import Issue

# Type-safe tool name - use the ToolName alias from cedrus.tools with a runtime fallback
if TYPE_CHECKING:
    from cedrus.tools import ToolName
else:
    ToolName = str


class NextAction(BaseModel):
    """Next action suggested for a result."""

    tool: ToolName
    params: Dict[str, Any]
    reason: str
    action_type: str = "improve"

    def model_post_init(self, context: Any) -> None:
        """Runtime validation of suggested tool against dynamic tool registry.

        Validates that the suggested tool exists in the tool registry.
        Parameter validation is skipped as tools have mode-specific variants
        with different signatures, and we don't have mode context here.
        """
        super().model_post_init(context)

        # Validate that suggested tool exists in the dynamic tool registry
        from cedrus.tools.tool_registry import TOOL_REGISTRY  # Import here to avoid circular import

        if self.tool not in TOOL_REGISTRY._variants:
            raise ValueError(
                f"Suggested tool '{self.tool}' is not defined in cedrus.tools. "
                f"Available tools: {', '.join(sorted(TOOL_REGISTRY._variants.keys()))}"
            )


class ActionableResult(BaseModel):
    """Generic result with next actions"""

    status: Literal["success", "error", "warning"]
    message: str
    result: Dict[str, Any]
    suggested_actions: list[NextAction] = Field(default_factory=list)
    validation_issues: list[Issue] = Field(default_factory=list)


def create_result(
    result: Dict[str, Any],
    message: str,
    status: Literal["success", "error", "warning"] = "success",
    next_actions: list[NextAction] | None = None,
    issues: list[Issue] | None = None,
) -> ActionableResult:
    """Factory for creating consistent tool results"""
    return ActionableResult(
        status=status,
        message=message,
        result=result,
        suggested_actions=next_actions or [],
        validation_issues=issues or [],
    )
