"""Node models: ClaimNode and ArgumentNode."""

from pydantic import Field
from typing import Literal
from .base import BaseNode, PropositionID


class ClaimNode(BaseNode):
    """Claim node in argument map."""
    node_type: Literal["claim", "argument"] = Field(default="claim", alias="_type")
    proposition_id: PropositionID


class ArgumentNode(BaseNode):
    """Argument node in argument map."""
    node_type: Literal["claim", "argument"] = Field(default="argument", alias="_type")
    gist: str = ""
    premises: list[PropositionID] = Field(default_factory=list)
    conclusion: PropositionID = ""
    tags: list[str] = Field(default_factory=list)
