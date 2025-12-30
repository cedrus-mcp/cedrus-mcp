"""Relation models: DialecticalRelation and LogicalRelation."""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime

from koala.models.base import NodeLabel

DialecticalRelationType = Literal["support", "attack"]
LogicalRelationType = Literal["equivalence", "negation"]

class DialecticalRelation(BaseModel):
    """Dialectical relation between nodes in argument map."""
    relation_type: DialecticalRelationType = Field(alias="_type")
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")
    target_premise_idx: int | None = None
    needs_review_flag: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"populate_by_name": True}


class LogicalRelation(BaseModel):
    """Logical relation between propositions in argument map."""
    relation_type: LogicalRelationType = Field(alias="_type")
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")


class RelationConfig(BaseModel):
    """Options for creating or editing relations in tools."""
    to_label: NodeLabel | None = Field(default=None, alias="target")
    from_label: NodeLabel | None = Field(default=None, alias="source")
    relation_type: DialecticalRelationType = Field(default="support", alias="type")
    target_premise_idx: int | None = None
    
    model_config = {
        "validate_by_name": True,
        "validate_by_alias": True,
        "populate_by_name": True,
    }

    @property
    def target(self) -> NodeLabel | None:
        return self.to_label

    @target.setter
    def target(self, value: NodeLabel | None):
        self.to_label = value

    @property
    def source(self) -> NodeLabel | None:
        return self.from_label

    @source.setter
    def source(self, value: NodeLabel | None):
        self.from_label = value
