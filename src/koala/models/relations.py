"""Relation models: DialecticalRelation and LogicalRelation."""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime

from koala.models.base import NodeLabel

DialecticalRelationType = Literal["support", "attack"]
LogicalRelationType = Literal["equivalence", "negation"]
GroundingStrategy = Literal[
    "define_negation",
    "define_equivalence",
    "copy_premise",
    "negate_premise",
    "copy_conclusion",
    "negate_conclusion",
]

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
    target: NodeLabel | None = Field(default=None)
    source: NodeLabel | None = Field(default=None)
    relation_type: DialecticalRelationType = Field(default="support")
    target_premise_idx: int | None = None
    grounding_strategy: GroundingStrategy | None = None
    