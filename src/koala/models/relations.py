"""Relation models: DialecticalRelation and LogicalRelation."""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime

DialecticalRelationType = Literal["support", "attack"]
LogicalRelationType = Literal["equivalence", "negation"]

class DialecticalRelation(BaseModel):
    """Dialectical relation between nodes in argument map."""
    relation_type: DialecticalRelationType = Field(alias="_type")
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")
    target_premise_idx: int | None = None
    needs_review_flag: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"populate_by_name": True}


class LogicalRelation(BaseModel):
    """Logical relation between propositions in argument map."""
    relation_type: LogicalRelationType = Field(alias="_type")
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")
