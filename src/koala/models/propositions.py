"""Proposition model."""


from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from .base import PropositionID


class Proposition(BaseModel):
    """Base node in argument map."""
    content: str
    created_at: datetime = Field(default_factory=datetime.now, alias="_created_at")
    last_modified: datetime = Field(default_factory=datetime.now, alias="_last_modified")
    id: PropositionID = Field(default_factory=lambda: uuid4().hex)
    is_dummy: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"populate_by_name": True}
