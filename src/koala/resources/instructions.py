# resources/instructions.py

from typing import Literal

import json

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from koala.models.results import NextAction
from koala.server import AppContext, mcp

def instructions_sketch(app_ctx: AppContext) -> str:
    instructions = (
        "### Sketching Instructions\n"
        "\n"
        "Sketch mode allows you to outline an argument map without having to fill in the precise details. "
        "You can add nodes (that is: claims and arguments) quickly by focusing on their key points (proposition) or main ideas (gist). "
        "A good sketch includes all the important claims and arguments, connects them provisionally via support and attack relations, "
        "captures the main point of each claim and argument, and identifies each node by means of concise and distinct labels.\n\n"
        "Typical actions in sketch mode include:\n"
        f'{NextAction(tool="add", params={"label": "Claim Label", "node_options": {"proposition": "The proposition maintained by this claim."}}, reason="Add a new claim.", action_type="expand").model_dump()}\n'
        f'{NextAction(tool="add", params={"label": "Argument Label", "node_options": {"gist": "The main idea of this argument."}}, reason="Add a new argument.", action_type="expand").model_dump()}\n'
        f'{NextAction(tool="connect", params={"from_label": "Argument Label", "to_label": "Claim Label", "relation_options": {"relation_type": "support"}}, reason="Connect an argument to a claim with a support relation.", action_type="expand").model_dump()}\n'
        "\n"
    )
    if app_ctx.mode == "sketch":
        instructions += "Currently active mode: `sketch` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `sketch` mode call {NextAction(tool='mode', params={'mode': 'sketch'}, reason='Switch to sketch mode.')}."
    return instructions

def instruction_author(app_ctx: AppContext) -> str:
    instructions = (
        "### Authoring Instructions\n"
        "\n"
        "Author mode is designed for fleshing out the details of your argument map. "
        "This includes, in particular, reconstructing the arguments as premise-conclusion structures, "
        "and 'grounding' the support and attack relations.\n"
        "\n"
        "A good reconstruction of an argument provides the argument's conclusion and the premises "
        "which are used to infer and justify that conclusion.\n"
        "\n"
        "A dialectical relation should be 'grounded' in the logical connections between the nodes' constituent propositions in the following sense:\n"
        "- A claim C supports an argument A if C is used as a premise in A's reconstruction.\n"
        "- A claim C attacks an argument A if C negates a premise in A's reconstruction.\n"
        "- An argument A supports a claim C if A's conclusion is C's proposition.\n"
        "- An argument A attacks a claim C if A's conclusion negates C's proposition.\n"
        "- An argument A1 supports an argument A2 if A1's conclusion is used as a premise in A2's reconstruction.\n"
        "- An argument A1 attacks an argument A2 if A1's conclusion negates a premise in A2's reconstruction.\n"
        "\n"
        "In the `author` mode, you'd typically work on individual arguments, clarifying their conclusions and unfolding their premises. "
        "You iteratively improve the argument reconstructions, trying to ground more and more dialectical relations in order to"
        "obtain an ever more coherent and well-structured argument map.\n"
        "\n"
        "Typical actions in author mode include:\n"
        f'{NextAction(tool="edit", params={"label": "Claim Label", "field": "proposition", "edit_options": {"new_value": "The revised and clarified proposition of this claim."}}, reason="Edit an existing claim to add more detail.", action_type="refine").model_dump()}\n'
        f'{NextAction(tool="edit", params={"label": "Argument Label", "field": "conclusion", "edit_options": {"new_value": "The proposition serving as the conclusion of this argument."}}, reason="Edit an existing argument to add more detail.", action_type="refine").model_dump()}\n'
        f'{NextAction(tool="connect", params={"from_label": "Argument 1", "to_label": "Argument 2", "relation_options": {"relation_type": "attack", "target_premise_idx": "2"}}, reason="Ground attack relation by specifying that the conclusion of <Argument 1> negates premise (2) of <Argument 2>.", action_type="refine").model_dump()}\n'
        "\n"
    )
    if app_ctx.mode == "author":
        instructions += "Currently active mode: `author` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `author` mode call {NextAction(tool='mode', params={'mode': 'author'}, reason='Switch to author mode.').model_dump()}."
    return instructions

def instruction_review(app_ctx: AppContext) -> str:
    instructions: str = (
        "### Review Instructions\n"
        "\n"
        "Review mode is intended for critically evaluating the argument map as a whole. "
        "In this mode, you assess the quality and coherence of the arguments presented, "
        "identify any gaps or weaknesses in reasoning, and suggest improvements or revisions.\n"
        "\n"
        "A thorough review involves in particular\n"
        "- checking that root claims are clearly stated, mutually exclusive, collectively exhaustive, and address the main issue at hand,\n"
        "- merging duplicate arguments and redundant claims,\n"
        "- disentangling distinct lines of reasoning that are presented in one and the same argument, but should be separated,\n"
        "- streamlining the structure of the argument map, e.g. by removing irrelevant or unsupported nodes,\n"
        "- verifying that the inferences made by arguments are correct, especially in case the argument has been automatically revised,\n"
        "\n"
        "Typical workflows in review mode include:\n"
        "- Compare similiar arguments > merge duplicates > rephrase labels and gists to improve clarity and distinctness > revisit premise-conclusion reconstructions"
        "- Identify complex and elaborate arguments > split into simpler sub-arguments > ensure each sub-argument is properly reconstructed > connect sub-arguments through grounded support relations\n"
        "- Start reviewing from main claims and root arguments and work your way against the direction of the dialectical relations \n"
        "\n"
    )
    if app_ctx.mode == "review":
        instructions += "Currently active mode: `review` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `review` mode call {NextAction(tool='mode', params={'mode': 'review'}, reason='Switch to review mode.').model_dump()}."
    return instructions

@mcp.resource("argmap://instructions")
async def instruction_resource() -> str:
    """Provide instruction text for different modes."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    mode = app_ctx.mode
    match mode:
        case "sketch":
            return instructions_sketch(app_ctx)
        case "author":
            return instruction_author(app_ctx)
        case "review":
            return instruction_review(app_ctx)
        case _:
            return f"Unknown mode {mode}. Available modes: sketch, author, review."


# @mcp.resource("argmap://instructions/grounding")


# @mcp.resource("argmap://instructions/merging")

