# src/koala/models/results.py
"""Result models with next actions and validation issues."""

from typing import Any, Dict, Literal
from pydantic import BaseModel, Field

from .base import Issue

# Type-safe tool name - this creates a Literal type from actual tool names
from koala.tools import ToolName


class NextAction(BaseModel):
    """Next action suggested for a result."""
    tool: ToolName
    params: Dict[str, Any]
    reason: str
    action_type: str = "improve"

    def model_post_init(self, context: Any) -> None:
        """runtime validation of suggested tool and params."""
        super().model_post_init(context)
        # validate that suggested tool is defined in koala.tools
        from koala import tools  # Import here to avoid circular import
        if not hasattr(tools, self.tool):
            raise ValueError(f"Suggested tool '{self.tool}' is not defined in koala.tools.")
        # check function signature matches params
        from inspect import signature
        sig = signature(getattr(tools, self.tool))
        for param in self.params:
            if param not in sig.parameters:
                raise ValueError(f"Parameter '{param}' is not valid for tool '{self.tool}'.")


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
    issues: list[Issue] | None = None
) -> ActionableResult:
    """Factory for creating consistent tool results"""
    return ActionableResult(
        status=status,
        message=message,
        result=result,
        suggested_actions=next_actions or [],
        validation_issues=issues or []
    )