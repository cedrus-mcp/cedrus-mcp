"""Tool argument classes and validation logic."""

from typing import Any, Literal, overload

from mcp.server.fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, Field

from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import NodeLabel
from cedrus.models.relations import DialecticalRelationType
from cedrus.tools.runtime.tool_context import ToolContext

logger = get_logger("cedrus.tool_args")

# @overload
# def parse_tool_args(tool_name: Literal["add"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any) -> "AddToolArgs": ...


@overload
def parse_tool_args(
    tool_name: Literal["edit"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any
) -> "EditToolArgs": ...


@overload
def parse_tool_args(
    tool_name: Literal["connect"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any
) -> "ConnectToolArgs": ...


def parse_tool_args(
    tool_name: str, tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any
) -> "EditToolArgs | ConnectToolArgs":
    """Parse and validate tool arguments for the specified tool."""
    ToolArgClass: type[EditToolArgs] | type[ConnectToolArgs]
    if tool_name == "edit":
        ToolArgClass = EditToolArgs
    elif tool_name == "connect":
        ToolArgClass = ConnectToolArgs
    else:
        logger.error(f"Internal Error: Unknown tool name '{tool_name}' for argument parsing.")
        raise RuntimeError(f"Internal Error: Unknown tool name '{tool_name}' for argument parsing.")

    try:
        # Check for unexpected arguments and collect keys to remove
        keys_to_remove = [key for key in kwargs if key not in ToolArgClass.model_fields]
        if keys_to_remove:
            tc.issue(
                "warning",
                f"Ignoring unexpected argument(s) {', '.join(keys_to_remove)} for tool '{tool_name}'. Valid arguments are: {', '.join(ToolArgClass.model_fields.keys())}.",
                priority=1.0,
            )
        # Remove unexpected arguments
        for key in keys_to_remove:
            kwargs.pop(key)
        args = ToolArgClass(**kwargs)
        args.sanitize(tc, arg_map)
        return args
    except Exception as e:
        logger.error(f"Error parsing arguments for tool '{tool_name}': {str(e)}")
        raise ValueError(f"Error while parsing arguments for tool '{tool_name}': {str(e)}")


# class AddToolArgs(BaseModel):
#     """Arguments for the add tool."""

#     proposition: str | None = None
#     gist: str | None = None
#     conclusion: PropositionID | None = None
#     premises: list[PropositionID] | None = None
#     node_type: Literal["claim", "argument"] | None = None
#     to_label: NodeLabel | None = None
#     from_label: NodeLabel | None = None
#     relation_type: DialecticalRelationType | None = None
#     target_premise_idx: int | None = None
#     tags: list[str] | None = None
#     metadata: dict[str, str] | None = None

#     def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:
#         """Validate and sanitize arguments for the add tool."""

#         # Infer node_type if not provided
#         if self.node_type is None:
#             if self.gist or self.conclusion or self.premises:
#                 self.node_type = "argument"
#                 tc.issue("info", "Adding an 'argument' node (inferred from provided fields).", priority=.2)
#             else:
#                 self.node_type = "claim"
#                 tc.issue("info", "Adding a 'claim' node (inferred from provided fields).", priority=.2)

#         # Check node arguments
#         if self.node_type not in ["claim", "argument"]:
#             raise ValueError("node_type must be either 'claim' or 'argument'.")
#         if self.node_type == "argument":
#             if self.proposition is not None:
#                 tc.issue("info", "As we are adding an argument node, 'proposition' will be ignored.")
#         if self.node_type == "claim":
#             ignored_fields = [
#                 field for field in ["gist", "conclusion", "premises"] if getattr(self, field) is not None
#             ]
#             if ignored_fields:
#                 tc.issue("info", f"As we are adding a claim node, fields {', '.join(ignored_fields)} will be ignored.")

#         # Validate relation arguments
#         self.to_label, self.from_label, self.target_premise_idx = utils.sanitize_relation_args_new_node(
#             self.to_label, self.from_label, self.target_premise_idx, arg_map, tc
#         )
#         if self.to_label or self.from_label:
#             if self.relation_type is None:
#                 tc.issue("info", "Assuming 'support' relation type as default.", priority=.2)
#                 self.relation_type = "support"
#             if self.relation_type not in ["support", "attack"]:
#                 raise ValueError("relation_type must be either 'support' or 'attack'.")


class EditToolArgs(BaseModel):
    """Arguments for the edit tool."""

    field: str
    node_type: Literal["claim", "argument"]
    key: str | None = None
    new_value: str | None = None
    old_value: str | None = None
    premise_idx: int | None = None

    def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:
        """Validate and sanitize arguments for the edit tool."""

        if self.node_type == "claim":
            valid_fields = ["label", "proposition", "tags", "metadata"]
        elif self.node_type == "argument":
            valid_fields = ["label", "gist", "conclusion", "premises", "tags", "metadata"]
        else:
            logger.error(
                f"Internal Error: Unknown node_type '{self.node_type}' for edit tool argument parsing."
            )
            raise ValueError("Internal error: node_type must be either 'claim' or 'argument'.")

        if self.field not in valid_fields:
            tc.suggest(
                "edit",
                {
                    "label": self.node_type.upper(),
                    "field": valid_fields[2],
                    "edit_options": {"new_value": "NEW_VALUE"},
                },
                f"Edit the '{valid_fields[2]}' field of {self.node_type.upper()}.",
            )
            logger.error(
                f"Invalid field '{self.field}' for node_type '{self.node_type}'. Valid fields are: {', '.join(valid_fields)}."
            )
            raise ValueError(
                f"For node_type '{self.node_type}', field to edit must be one of {', '.join(valid_fields)}."
            )

        match self.field:
            case "tags":
                if self.new_value is None and self.old_value is None:
                    logger.error(
                        "When editing 'tags', at least one of 'new_value' or 'old_value' must be provided."
                    )
                    raise ValueError(
                        "When editing 'tags', at least one of 'new_value' or 'old_value' must be provided."
                    )
                if self.premise_idx is not None:
                    tc.issue(
                        "warning", "Ignoring premise_idx when editing 'tags' field.", priority=0.2
                    )
                    self.premise_idx = None
                if self.key is not None:
                    tc.issue("info", "Ignoring key when editing 'tags' field.", priority=0.2)
                    self.key = None
            case "metadata":
                if self.key is None:
                    logger.error("When editing 'metadata', 'key' must be provided.")
                    raise ValueError("When editing 'metadata', 'key' must be provided.")
                if self.premise_idx is not None:
                    tc.issue(
                        "warning",
                        "Ignoring premise_idx when editing 'metadata' field.",
                        priority=0.2,
                    )
                    self.premise_idx = None
                if self.old_value is not None:
                    tc.issue(
                        "info", "Ignoring old_value when editing 'metadata' field.", priority=0.2
                    )
                    self.old_value = None
            case "proposition" | "gist" | "conclusion" | "label":
                if self.key is not None:
                    tc.issue(
                        "info", f"Ignoring `key` when editing '{self.field}' field.", priority=0.2
                    )
                    self.key = None
                if self.premise_idx is not None:
                    tc.issue(
                        "warning",
                        f"Ignoring `premise_idx` when editing '{self.field}' field.",
                        priority=0.2,
                    )
                    self.premise_idx = None
                if self.old_value is not None:
                    tc.issue(
                        "info",
                        f"Ignoring `old_value` when editing '{self.field}' field.",
                        priority=0.2,
                    )
                    self.old_value = None


class ConnectToolArgs(BaseModel):
    """Arguments for the connect tool."""

    source: NodeLabel
    target: NodeLabel
    relation_type: DialecticalRelationType | None = None
    target_premise_idx: int | None = None
    grounding_strategy: (
        Literal[
            "define_equivalence",
            "copy_premise",
            "copy_conclusion",
            "define_negation",
            "negate_premise",
            "negate_conclusion",
        ]
        | None
    ) = None

    def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:
        """Validate and sanitize arguments for the connect tool."""

        if self.relation_type is None:
            tc.issue("info", "Assuming 'support' relation type as default.", priority=0.2).suggest(
                "connect",
                {"source": self.source, "target": self.target, "relation_type": "attack"},
                "Create an 'attack' relation instead.",
            )
            self.relation_type = "support"
        elif self.relation_type not in ["support", "attack"]:
            tc.suggest(
                "connect",
                {"source": self.source, "target": self.target, "relation_type": "RELATION_TYPE"},
                "Create a relation of type RELATION_TYPE ('support' or 'attack').",
            )
            logger.error(
                f"relation_type must be either 'support' or 'attack', got '{self.relation_type}'."
            )
            raise ValueError("relation_type must be either 'support' or 'attack'.")
        if self.relation_type == "support" and self.grounding_strategy not in [
            None,
            "define_equivalence",
            "copy_premise",
            "copy_conclusion",
        ]:
            tc.suggest(
                "connect",
                {
                    "source": self.source,
                    "target": self.target,
                    "relation_type": "support",
                    "grounding_strategy": "GROUNDING_STRATEGY",
                },
                "Create a relation with grounding strategy GROUNDING_STRATEGY.",
            )
            logger.error(
                f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `support`."
            )
            raise ValueError(
                f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `{self.relation_type}`. Must be one of 'define_equivalence', 'copy_premise', 'copy_conclusion', or None."
            )
        if self.relation_type == "attack" and self.grounding_strategy not in [
            None,
            "define_negation",
            "negate_premise",
            "negate_conclusion",
        ]:
            tc.suggest(
                "connect",
                {
                    "source": self.source,
                    "target": self.target,
                    "relation_type": "attack",
                    "grounding_strategy": "GROUNDING_STRATEGY",
                },
                "Create a relation with grounding strategy GROUNDING_STRATEGY.",
            )
            logger.error(
                f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `attack`."
            )
            raise ValueError(
                f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `{self.relation_type}`. Must be one of 'define_negation', 'negate_premise', 'negate_conclusion', or None."
            )
