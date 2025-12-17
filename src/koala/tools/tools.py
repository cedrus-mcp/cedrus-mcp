"""Authoring tools: new_claim, new_argument, new_support, new_attack."""

from typing import Any, Literal, overload

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.session import ServerSession
from mcp.types import CallToolResult
from pydantic import BaseModel

from koala.graph.argument_map import ArgumentMap
from koala.models import (
    NodeLabel,
    ClaimNode,
    ArgumentNode,
)
from koala.models.base import PropositionID, Mode
from koala.models.relations import DialecticalRelationType
from koala.server import mcp, AppContext
from koala.tools import relation_authoring, utils, node_authoring, suggestions
from koala.tools.tool_context import ToolContext, tool_context

logger = get_logger("koala.tools")  # Creates 'FastMCP.koala' logger

            

@overload
def parse_tool_args(tool_name: Literal["add"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any) -> "AddToolArgs": ...

@overload
def parse_tool_args(tool_name: Literal["edit"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any) -> "EditToolArgs": ...

@overload
def parse_tool_args(tool_name: Literal["connect"], tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any) -> "ConnectToolArgs": ...

def parse_tool_args(tool_name: str, tc: ToolContext, arg_map: ArgumentMap, **kwargs: Any) -> "AddToolArgs | EditToolArgs | ConnectToolArgs":
    """Parse and validate tool arguments for the specified tool."""
    ToolArgClass: type[AddToolArgs] | type[EditToolArgs] | type[ConnectToolArgs]
    if tool_name == "add":
        ToolArgClass = AddToolArgs
    elif tool_name == "edit":
        ToolArgClass = EditToolArgs
    else:
        raise ValueError(f"Internal Error: Unknown tool name '{tool_name}' for argument parsing.")

    try:
        # Check for unexpected arguments and collect keys to remove
        keys_to_remove = [key for key in kwargs if key not in ToolArgClass.model_fields]
        if keys_to_remove:
            tc.issue("info", f"Ignoring unexpected argument(s) {', '.join(keys_to_remove)} for tool '{tool_name}'.")        
        # Remove unexpected arguments
        for key in keys_to_remove:
            kwargs.pop(key)
        args = ToolArgClass(**kwargs)
        args.sanitize(tc, arg_map)
        return args
    except Exception as e:
        raise ValueError(f"Error while parsing arguments for tool '{tool_name}': {str(e)}")


class AddToolArgs(BaseModel):
    proposition: str | None = None
    gist: str | None = None
    conclusion: PropositionID | None = None
    premises: list[PropositionID] | None = None
    node_type: Literal["claim", "argument"] | None = None
    to_label: NodeLabel | None = None
    from_label: NodeLabel | None = None
    relation_type: DialecticalRelationType | None = None
    target_premise_idx: int | None = None
    tags: list[str] | None = None
    metadata: dict[str, str] | None = None

    def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:

        # Infer node_type if not provided
        if self.node_type is None:
            if self.gist or self.conclusion or self.premises:
                self.node_type = "argument"
                tc.note("Adding an 'argument' node (inferred from provided fields).", priority=.2)
            else:
                self.node_type = "claim"
                tc.note("Adding a 'claim' node (inferred from provided fields).", priority=.2)

        # Check node arguments
        if self.node_type not in ["claim", "argument"]:
            raise ValueError("node_type must be either 'claim' or 'argument'.")
        if self.node_type == "argument":
            if self.proposition is not None:
                tc.issue("info", "As we are adding an argument node, 'proposition' will be ignored.")
        if self.node_type == "claim":
            ignored_fields = [
                field for field in ["gist", "conclusion", "premises"] if getattr(self, field) is not None
            ]
            if ignored_fields:
                tc.issue("info", f"As we are adding a claim node, fields {', '.join(ignored_fields)} will be ignored.")

        # Validate relation arguments
        self.to_label, self.from_label, self.target_premise_idx = utils.sanitize_relation_args_new_node(
            self.to_label, self.from_label, self.target_premise_idx, arg_map, tc
        )
        if self.to_label or self.from_label:
            if self.relation_type is None:
                tc.note("Assuming 'support' relation type as default.", priority=.2)
                self.relation_type = "support"
            if self.relation_type not in ["support", "attack"]:
                raise ValueError("relation_type must be either 'support' or 'attack'.")


@mcp.tool()
def add(label: NodeLabel, ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Create a new node in the argument map.

    Example usage:

        add(label="CLAIM_1", proposition="This is a new claim.")
    """


    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if not label or not label.strip():
            raise ValueError("Label must be a non-empty string.")
        
        # Ensure label is unique
        label = utils.ensure_label_is_unique(label, arg_map, tc)

        args = parse_tool_args("add", tc, arg_map, label=label, **kwargs)

        try:
            if args.node_type == "claim":
                # Adding a claim node
                node_authoring.new_claim(
                    label=label,
                    proposition=args.proposition,
                    to_label=args.to_label,
                    from_label=args.from_label,
                    relation_type=args.relation_type or "support",
                    target_premise_idx=args.target_premise_idx,
                    tags=args.tags,
                    metadata=args.metadata,
                    arg_map=arg_map,
                    tc=tc,
                )
            elif args.node_type == "argument":
                # Adding an argument node
                node_authoring.new_argument(
                    label=label,
                    gist=args.gist,
                    to_label=args.to_label,
                    from_label=args.from_label,
                    relation_type=args.relation_type or "support",
                    target_premise_idx=args.target_premise_idx,
                    premises=args.premises,
                    conclusion=args.conclusion,
                    tags=args.tags,
                    metadata=args.metadata,
                    arg_map=arg_map,
                    tc=tc,
                )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create {args.node_type} `{label}`: {str(e)}", error=str(e)
            ).build()

        suggestions.add_suggestions_after_adding_node(label, arg_map, tc)

        return tc.build()
    



class EditToolArgs(BaseModel):
    field: str
    node_type: Literal["claim", "argument"]
    key: str | None = None
    new_value: str | None = None
    old_value: str | None = None
    premise_idx: int | None = None    

    def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:

        if self.node_type == "claim":
            valid_fields = ["label", "proposition", "tags", "metadata"]
        elif self.node_type == "argument":
            valid_fields = ["label", "gist", "conclusion", "premises", "tags", "metadata"]
        else:
            logger.error(f"Internal error: node_type must be either 'claim' or 'argument' (but is {self.node_type}).")
            raise ValueError("Internal error: node_type must be either 'claim' or 'argument'.")

        if self.field not in valid_fields:
            tc.suggest(
                "edit",
                {"label": self.node_type.upper(), "field": valid_fields[2], "new_value": "NEW_VALUE"},
                f"Edit the '{valid_fields[2]}' field of {self.node_type.upper()}.",
            )
            raise ValueError(f"For node_type '{self.node_type}', field to edit must be one of {', '.join(valid_fields)}.")

        match self.field:
            case "tags":
                if self.new_value is None and self.old_value is None:
                    raise ValueError("When editing 'tags', at least one of 'new_value' or 'old_value' must be provided.")
                if self.premise_idx is not None:
                    tc.note("Ignoring premise_idx when editing 'tags' field.", priority=.2)
                    self.premise_idx = None
                if self.key is not None:
                    tc.note("Ignoring key when editing 'tags' field.", priority=.2)
                    self.key = None
            case "metadata":
                if self.key is None:
                    raise ValueError("When editing 'metadata', 'key' must be provided.")
                if self.premise_idx is not None:
                    tc.note("Ignoring premise_idx when editing 'metadata' field.", priority=.2)
                    self.premise_idx = None
                if self.old_value is not None:
                    tc.note("Ignoring old_value when editing 'metadata' field.", priority=.2)
                    self.old_value = None
            case "proposition" | "gist" | "conclusion" | "label":
                if self.key is not None:
                    tc.note(f"Ignoring `key` when editing '{self.field}' field.", priority=.2)
                    self.key = None
                if self.premise_idx is not None:
                    tc.note(f"Ignoring `premise_idx` when editing '{self.field}' field.", priority=.2)
                    self.premise_idx = None
                if self.old_value is not None:
                    tc.note(f"Ignoring `old_value` when editing '{self.field}' field.", priority=.2)
                    self.old_value = None


@mcp.tool()
def edit(label: NodeLabel, ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Edit an existing node in the argument map.

    Example usage:

        edit(label="CLAIM_1", proposition="This is the updated claim content.")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        node = arg_map.get_node(label)
        if node is None:
            return tc.failure(
                f"Node '{label}' does not exist.",
                error="NonExistentNode",
            ).build()

        node_type = "claim" if isinstance(node, ClaimNode) else "argument"
        args = parse_tool_args("edit", tc, arg_map, node_type=node_type, **kwargs)

        try:
            match args.field:
                case "tags":
                    return node_authoring.update_tags(
                        label=label,
                        old_value=args.old_value,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )
                case "metadata":
                    return node_authoring.update_metadata(
                        label=label,
                        key=args.key,
                        new_value=args.new_value,
                        arg_map=arg_map,
                        tc=tc,
                    )

            if isinstance(node, ClaimNode):
                match args.field:
                    case "label" | "proposition":
                        return node_authoring.update_claim(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
            elif isinstance(node, ArgumentNode):
                match args.field:
                    case "label" | "gist" | "conclusion":
                        return node_authoring.update_argument(
                            label=label,
                            field=args.field,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "premises":
                        return node_authoring.update_premises(
                            label=label,
                            premise_idx=args.premise_idx,
                            new_value=args.new_value,
                            arg_map=arg_map,
                            tc=tc,
                        )
        except Exception as e:
            return tc.failure(
                f"✗ Failed to edit node `{label}`: {str(e)}", error=str(e)
            ).build()
        
        return tc.failure(
            f"✗ Failed to edit field '{args.field}' of {args.node_type} node `{label}`."
        ).build()


class ConnectToolArgs(BaseModel):
    from_label: NodeLabel
    to_label: NodeLabel
    relation_type: DialecticalRelationType | None = None
    target_premise_idx: int | None = None
    grounding_strategy: Literal["define_equivalence", "copy_premise", "copy_conclusion", "define_negation", "negate_premise", "negate_conclusion"] | None = None

    def sanitize(self, tc: ToolContext, arg_map: ArgumentMap) -> None:
        if self.relation_type is None:
            tc.note(
                "Assuming 'support' relation type as default.", priority=.2
            ).suggest(
                "connect",
                {"from_label": self.from_label, "to_label": self.to_label, "relation_type": "attack"},
                "Create an 'attack' relation instead.",
            )
            self.relation_type = "support"
        elif self.relation_type not in ["support", "attack"]:
            tc.suggest(
                "connect",
                {"from_label": self.from_label, "to_label": self.to_label, "relation_type": "RELATION_TYPE"},
                "Create a relation of type RELATION_TYPE ('support' or 'attack').",
            )
            raise ValueError("relation_type must be either 'support' or 'attack'.")
        if self.relation_type == "support" and self.grounding_strategy not in [None, "define_equivalence", "copy_premise", "copy_conclusion"]:
            tc.suggest(
                "connect",
                {"from_label": self.from_label, "to_label": self.to_label, "relation_type": "support", "grounding_strategy": "GROUNDING_STRATEGY"},
                "Create a relation with grounding strategy GROUNDING_STRATEGY.",
            )
            raise ValueError(f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `{self.relation_type}`. Must be one of 'define_equivalence', 'copy_premise', 'copy_conclusion', or None.")
        if self.relation_type == "attack" and self.grounding_strategy not in [None, "define_negation", "negate_premise", "negate_conclusion"]:
            tc.suggest(
                "connect",
                {"from_label": self.from_label, "to_label": self.to_label, "relation_type": "attack", "grounding_strategy": "GROUNDING_STRATEGY"},
                "Create a relation with grounding strategy GROUNDING_STRATEGY.",
            )
            raise ValueError(f"grounding_strategy `{self.grounding_strategy}` is not compatible with relation_type `{self.relation_type}`. Must be one of 'define_negation', 'negate_premise', 'negate_conclusion', or None.")

@mcp.tool()
def connect(from_label: str, to_label: str, ctx: Context[ServerSession, AppContext], kwargs: Any) -> CallToolResult:
    """Create a new dialectical relation between two existing nodes.

    Example usage:

        connect(
            from_label="ARGUMENT_1",
            to_label="CLAIM_1",
            relation_type="support"
        )
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if mode == "sketch":
            if kwargs.get("grounding_strategy") is not None:
                tc.note(
                    "Ignoring grounding strategies in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to use grounding strategies."
                )
                kwargs["grounding_strategy"] = None
            if kwargs.get("target_premise_idx") is not None:
                tc.note(
                    "Ignoring target_premise_idx in 'sketch' mode.", priority=.2
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to specify target premise index."
                )
                kwargs["target_premise_idx"] = None
        elif mode == "review":
            tc.note(
                "Creating new relations in 'review' mode. Consider switching mode."
            ).suggest(
                "mode", {"mode": "author"}, "Switch to 'author' mode to create new relations."
            )

        args = parse_tool_args("connect", tc, arg_map, from_label=from_label, to_label=to_label, **kwargs)

        try:
            if not arg_map.get_dialectic_relation(args.from_label, args.to_label):
                match args.relation_type:
                    case "support":
                        return relation_authoring.new_support_relation(
                            from_label=args.from_label,
                            to_label=args.to_label,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case "attack":
                        return relation_authoring.new_attack_relation(
                            from_label=args.from_label,
                            to_label=args.to_label,
                            target_premise_idx=args.target_premise_idx,
                            grounding_strategy=args.grounding_strategy,  # type: ignore
                            arg_map=arg_map,
                            tc=tc,
                        )
                    case _:
                        return tc.failure(
                            f"Invalid relation_type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
            elif mode != "author":
                return tc.failure(
                    f"Cannot ground existing relation from `{args.from_label}` to `{args.to_label}` in '{mode}' mode.",
                    error="RelationAlreadyExists",
                ).suggest(
                    "mode", {"mode": "author"}, "Switch to 'author' mode to ground existing relations."
                ).build()
            else:
                match args.relation_type:
                    case "support":
                        for grounding_strategy in ["define_equivalence", "copy_conclusion", "copy_premise"]:
                            try:
                                return relation_authoring.ground_support_relation(
                                    from_label=args.from_label,
                                    to_label=args.to_label,
                                    strategy=grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.note(f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
                        return tc.failure(
                            f"✗ Failed to ground support relation from `{args.from_label}` to `{args.to_label}`.",
                            error="GroundingFailed",
                        ).build()                    
                    case "attack":
                        for grounding_strategy in ["define_negation", "negate_conclusion", "negate_premise"]:
                            try:
                                return relation_authoring.ground_attack_relation(
                                    from_label=args.from_label,
                                    to_label=args.to_label,
                                    strategy=grounding_strategy,  # type: ignore
                                    arg_map=arg_map,
                                    tc=tc,
                                )
                            except Exception as e:
                                tc.note(f"Failed to ground with strategy '{grounding_strategy}': {str(e)}", priority=.1)
                        return tc.failure(
                            f"✗ Failed to ground attack relation from `{args.from_label}` to `{args.to_label}`.",
                            error="GroundingFailed",
                        ).build()
                    case _:
                        return tc.failure(
                            f"Invalid relation_type '{args.relation_type}'.",
                            error="InvalidRelationType",
                        ).build()
        except Exception as e:
            return tc.failure(
                f"✗ Failed to create {args.relation_type} relation from `{args.from_label}` to `{args.to_label}`: {str(e)}", error=str(e)
            ).build()
        
        raise RuntimeError(f"Internal Error: Unhandled case when creating relation from `{args.from_label}` to `{args.to_label}`.")


@mcp.tool()
def remove(ctx: Context[ServerSession, AppContext], **kwargs: Any) -> CallToolResult:
    """Remove an existing node or relation from the argument map.

    Example usage:

        remove(label="CLAIM_1")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        # validate kwargs
        label = kwargs.get("label")
        to_label = kwargs.get("to_label")
        from_label = kwargs.get("from_label")
        if label and label.strip():
            if to_label is not None:
                tc.note("Ignoring to_label when removing a node.", priority=.2)
            if from_label is not None:
                tc.note("Ignoring from_label when removing a node.", priority=.2)
        elif to_label and to_label.strip() and from_label and from_label.strip():
            if label is not None:
                tc.note("Ignoring label when removing a relation.", priority=.2)
        else:
            return tc.issue(
                "error",
                "To remove a node, provide a non-empty 'label'. To remove a relation, provide non-empty 'from_label' and 'to_label'.",
            ).suggest(
                "remove",
                {
                    "label": "NODE_LABEL",
                },
                "Remove a node by specifying its label.",
            ).suggest(
                "remove",
                {
                    "from_label": "SOURCE_NODE_LABEL",
                    "to_label": "TARGET_NODE_LABEL",
                },
                "Remove a relation by specifying source and target node labels.",
            ).build()

        if label:
            node = arg_map.get_node(label)
            if node is None:
                return tc.failure(
                    f"Node '{label}' does not exist.",
                    error="NonExistentNode",
                ).build()

            if isinstance(node, ClaimNode):
                return node_authoring.delete_claim(
                    label=label,
                    arg_map=arg_map,
                    tc=tc,
                )
            else:
                return node_authoring.delete_argument(
                    label=label,
                    arg_map=arg_map,
                    tc=tc,
                )
        elif to_label and from_label:
            return relation_authoring.delete_relation(
                from_label=from_label,
                to_label=to_label,
                arg_map=arg_map,
                tc=tc,
            )

        raise ValueError("Internal Error: Unhandled case in remove tool.")

@mcp.tool()
def mode(
    mode: Mode,
    ctx: Context[ServerSession, AppContext],
) -> CallToolResult:
    """Switch the argument map editing mode.

    Example usage:

        mode("author")
    """

    arg_map = ctx.request_context.lifespan_context.arg_map
    old_mode = ctx.request_context.lifespan_context.mode

    with tool_context(arg_map, mode) as tc:

        if mode not in ["sketch", "author", "review"]:
            return tc.failure(
                f"Invalid mode '{mode}'. Valid modes are 'sketch', 'author', and 'review'.",
                error="InvalidMode",
            ).build()

        ctx.request_context.lifespan_context.mode = mode
        tc.success(f"✓ Switched mode from '{old_mode}' to '{mode}'.")
        return tc.build()