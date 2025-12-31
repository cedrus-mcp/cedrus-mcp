"""Tool execution context for managing tool outputs in a unified way."""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, field
from pydantic.networks import AnyUrl
from typing import Any, Literal, TYPE_CHECKING, Iterator

from mcp.types import CallToolResult, TextContent, TextResourceContents, EmbeddedResource, Annotations, ContentBlock, Role

from koala.models.base import Issue, NodeLabel, Mode
from koala.models.results import NextAction

if TYPE_CHECKING:
    from koala.graph import ArgumentMap
    from koala.tools import ToolName
else:
    ToolName = str  # Runtime fallback


@dataclass
class ToolContext:
    """Unified context for tool execution with fluent API.
    
    Manages content, issues, suggestions, and result state throughout tool execution.
    Provides fluent methods for adding outputs and building CallToolResult.
    """
    
    arg_map: ArgumentMap
    mode: Mode = "sketch"
    
    # Collections
    content: list[ContentBlock] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    suggestions: list[NextAction] = field(default_factory=list)
    resources: list[EmbeddedResource] = field(default_factory=list)
    
    # Result state
    _status: Literal["success", "failure", "partial"] = "success"
    _message: str = ""
    _result_data: dict[str, Any] | None = None
    _error: str | None = None
    
    # === Fluent Collection Methods ===
    
    def suggest(
        self,
        tool: ToolName,
        params: dict[str, Any],
        reason: str,
        action_type: str = "expand"
    ) -> ToolContext:
        """Add a suggestion for next action.
        
        Args:
            tool: Tool name to suggest
            params: Parameters for the tool
            reason: Reason for the suggestion
            action_type: Type of action (expand, improve, connect, fix)
            
        Returns:
            Self for method chaining
        """
        self.suggestions.append(
            NextAction(tool=tool, params=params, reason=reason, action_type=action_type)
        )
        return self
    
    def issue(
        self,
        severity: Literal["info", "warning", "error"],
        message: str,
        field: str | None = None,
        label: NodeLabel | None = None,
        **kwargs: Any
    ) -> ToolContext:
        """Add an issue.
        
        Args:
            severity: Issue severity (info, warning, error)
            message: Issue description
            field: Field the issue relates to
            **kwargs: Additional issue properties
            
        Returns:
            Self for method chaining
        """
        self.issues.append(
            Issue(severity=severity, issue=message, field=field or "", label=label or "", **kwargs)
        )
        if severity in ("error", "critical"):
            if self._status == "success":
                self._status = "failure"
        return self
    
    def note(
        self,
        text: str,
        priority: float = 0.3,
        audience: list[Role] | None = None
    ) -> ToolContext:
        """Add informational content.
        
        Args:
            text: Content text
            priority: Priority level (0.0-1.0)
            audience: Target audience (defaults to ["assistant"])
            
        Returns:
            Self for method chaining
        """
        default_audience: list[Role] = ["assistant"]
        self.content.append(
            TextContent(
                type="text",
                text=text,
                annotations=Annotations(
                    audience=audience or default_audience,
                    priority=priority
                )
            )
        )
        return self
    
    def embed_resource(
        self,
        uri: AnyUrl,
        text: str,
        priority: float = 0.5,
        audience: list[Role] | None = None
    ) -> ToolContext:
        """Embed a text resource as content.
        
        Args:
            uri: Resource URI
            text: Resource text content
            priority: Priority level (0.0-1.0)
            audience: Target audience (defaults to ["assistant"])
            
        Returns:
            Self for method chaining
        """
        default_audience: list[Role] = ["assistant"]
        self.resources.append(
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=uri,
                    text=text,
                ),
                annotations=Annotations(
                    audience=audience or default_audience,
                    priority=priority
                )
            )
        )
        return self

    # === Result State Methods ===
    
    def success(self, message: str, result: Any = None) -> ToolContext:
        """Mark operation as successful.
        
        Args:
            message: Success message
            result: Result data (dict or object with model_dump)
            
        Returns:
            Self for method chaining
        """
        self._status = "success"
        self._message = message
        if result is not None:
            self._result_data = result if isinstance(result, dict) else result
        return self
    
    def failure(self, message: str, error: str | None = None) -> ToolContext:
        """Mark operation as failed.
        
        Args:
            message: Failure message
            error: Error details
            
        Returns:
            Self for method chaining
        """
        self._status = "failure"
        self._message = message
        self._error = error or message
        return self
    
    def set_result(self, result: Any) -> ToolContext:
        """Set the result data.
        
        Args:
            result: Result data
            
        Returns:
            Self for method chaining
        """
        self._result_data = result if isinstance(result, dict) else result
        return self
    
    # === Builder Method ===
    
    def build(self) -> CallToolResult:
        """Build the final CallToolResult.
        
        Constructs appropriate CallToolResult based on accumulated state,
        handling both success and failure cases.
        
        Returns:
            CallToolResult with all collected content and structured data
        """
        if self._status == "failure":
            structuredContent={
                    "status": "failure",
                    "error": self._error,
                    "message": self._message,
                    "issues": [i.model_dump() for i in self.issues] if self.issues else []
                }
            self.content.append(
                TextContent(
                    type="text",
                    text=str(structuredContent),
                    annotations=Annotations(audience=["assistant"], priority=1.0)
                )
            )
            return CallToolResult(
                content=self.content,
                structuredContent=structuredContent
            )
        
        # Build structured content for success case
        structured_content: dict[str, Any] = {
            "status": self._status,
            "message": self._message,
        }
        plain_content: list[str] = []   
        
        if self._result_data is not None:
            structured_content["result"] = self._result_data
            plain_content.append(f"RESULT:\n\n{self._result_data}")
        
        if self.resources:
            structured_content["embedded_resources"] = [r.model_dump() for r in self.resources]
            text = "\n\n".join(f"{r.resource.uri}\n\n{r.resource.text}" for r in self.resources if isinstance(r.resource, TextResourceContents))
            plain_content.append(f"EMBEDDED RESOURCES:\n\n{text}")

        if self.issues:
            structured_content["issues"] = [i.model_dump() for i in self.issues]
            text = "\n\n".join(f"{i.severity}: {i.issue}" for i in self.issues)
            plain_content.append(f"ISSUES:\n\n{text}")

        if self.suggestions:
            structured_content["next_actions"] = [s.model_dump() for s in self.suggestions]
            text = "\n\n".join(f"{s.reason} ({s.action_type}): {s.tool}({s.params})" for s in self.suggestions)
            plain_content.append(f"SUGGESTIONS:\n\n{[s.model_dump() for s in self.suggestions]}")


        # Cast structured_content as plain text for backwards compatibility
        content = [
            TextContent(
                type="text",
                text="\n\n".join(plain_content),
            )
        ] + self.content

        return CallToolResult(
            content=content,
            structuredContent=structured_content
        )
    
    # === Domain-Specific Helper Methods ===
    
    def suggest_support_argument(
        self,
        label: str,
        reason: str,
        target_premise_idx: int | str | None = None
    ) -> ToolContext:
        """Shorthand for suggesting a supporting argument.
        
        Args:
            label: Label of node to support
            reason: Reason for the suggestion
            target_premise_idx: Optional premise index to target
            
        Returns:
            Self for method chaining
        """
        new_label = "New-Supporting-Argument"
        params: dict[str, Any] = {
            "target": label,
            "source": new_label,
            "relation_type": "support"
        }
        if target_premise_idx is not None:
            params["target_premise_idx"] = target_premise_idx
            
        self.suggest(
            "add_argument",
            {
                "label": new_label,
                "gist": f"Key point of new argument <{new_label}> goes here"
            },
            f"{reason} (Step 1 of 2)",
            action_type="expand"
        )
        self.suggest(
            "connect",
            params,
            f"{reason} (Step 2 of 2)",
            action_type="expand"
        )
        return self
    
    def suggest_attack_argument(
        self,
        label: str,
        reason: str,
        target_premise_idx: int | str | None = None
    ) -> ToolContext:
        """Shorthand for suggesting an attacking argument.
        
        Args:
            label: Label of node to attack
            reason: Reason for the suggestion
            
        Returns:
            Self for method chaining
        """
        new_label = "New-Attacking-Argument"
        params: dict[str, Any] = {
            "target": label,
            "source": new_label,
            "relation_type": "attack",
        }
        if target_premise_idx is not None:
            params["target_premise_idx"] = target_premise_idx

        self.suggest(
            "add_argument",
            {
                "label": new_label,
                "gist": f"Key point of new argument <{new_label}> goes here",
            },
            f"{reason} (Step 1 of 2)",
            action_type="expand"
        )
        self.suggest(
            "connect",
            params,
            f"{reason} (Step 2 of 2)",
            action_type="expand"
        )
        return self
    
    def suggest_update_field(
        self,
        label: str,
        field: str,
        reason: str,
    ) -> ToolContext:
        """Shorthand for suggesting a field update.
        
        Args:
            label: Label of node to update
            field: Field name to update
            reason: Reason for the suggestion
            
        Returns:
            Self for method chaining
        """
        return self.suggest(
            "edit",
            {
                "label": label,
                "field": field,
                "edit_options": {
                    "new_value": f"{field.upper()}_VALUE"
                }
            },
            reason,
            action_type="improve"
        )
    
    def suggest_connect_relation(
        self,
        from_label: str,
        to_label: str,
        relation_type: Literal["support", "attack"],
    ) -> ToolContext:
        """Shorthand for suggesting a relation connection.
        
        Args:
            from_label: Source node label
            to_label: Target node label (may be placeholder)
            relation_type: Type of relation
            
        Returns:
            Self for method chaining
        """
        actual_tool: ToolName = "connect"
        
        return self.suggest(
            actual_tool,
            {
                "source": from_label,
                "target": to_label,
                "relation_type": relation_type,
            },
            f"Connect `{from_label}` to existing node via {relation_type}.",
            action_type="connect"
        )


@contextmanager
def tool_context(
    arg_map: ArgumentMap,
    mode: Mode = "sketch"
) -> Iterator[ToolContext]:
    """Context manager for tool execution.
    
    Usage:
        with tool_context(arg_map, mode) as tc:
            tc.note("Processing...")
            tc.success("Done!", result=data)
            return tc.build()
    
    Args:
        arg_map: ArgumentMap instance
        mode: Current mode (sketch or detail)
        
    Yields:
        ToolContext instance
    """
    tc = ToolContext(arg_map=arg_map, mode=mode)
    try:
        yield tc
    except Exception as e:
        if tc._status == "success":  # Only override if not already set
            tc.failure(f"Unexpected error: {str(e)}", error=str(e))
        raise
