"""Base node model definitions."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

PropositionID = str
NodeLabel = str
Mode = Literal["sketch", "elaborate", "review"]

# Rendering / format types
Format = Literal["argdown", "tree", "json-nested", "yaml-nested"]


class Issue(BaseModel):
    """Validation issue found in result."""

    field: str
    label: NodeLabel
    issue: str
    severity: Literal["error", "warning", "info"] = "warning"


class BaseNode(BaseModel):
    """Base node in argument map."""

    node_type: Literal["claim", "argument"] = Field(alias="_type")
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")
    label: NodeLabel
    tags: list[str] = Field(default_factory=list)
    # issues: list[Issue] = Field(default_factory=list)
    needs_review_flag: bool = False
    misses_justification_flag: bool = False
    misses_critique_flag: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}  # Allow both name and alias
