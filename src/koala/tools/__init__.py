"""MCP tools for argument map manipulation."""

from typing import Literal

from .node_authoring import (
    new_claim,
    new_argument,
    update_claim,
    update_argument,
    update_metadata,
    update_tags,
    update_premises,
    delete_claim,
    delete_argument,
)

from .relation_authoring import (
    new_support_relation,
    new_attack_relation,
    ground_support_relation,
    ground_attack_relation,
)


# This generates the literal type values
ToolName = Literal[
    "new_claim",
    "new_argument",
    "update_claim",
    "update_argument",
    "update_metadata",
    "update_tags",
    "update_premises",
    "new_support_relation",
    "new_attack_relation",
    "ground_support_relation",
    "ground_attack_relation",
    "delete_claim",
    "delete_argument",
]

__all__ = [
    "ToolName",
    "new_claim",
    "new_argument",
    "update_claim",
    "update_argument",
    "update_metadata",
    "update_tags",
    "update_premises",
    "new_support_relation",
    "new_attack_relation",
    "ground_support_relation",
    "ground_attack_relation",
    "delete_claim",
    "delete_argument",
]


