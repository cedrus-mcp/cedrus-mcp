# resources/instructions.py

from koala.models.results import NextAction
from koala.server import AppContext, mcp


#####################################
# Overview and generic instructions #
#####################################

def instructions_sketch(app_ctx: AppContext) -> str:
    instructions = (
        "### Sketching Instructions\n"
        "\n"
        "Sketch mode allows you to outline an argument map without having to fill in the precise details. "
        "You can add nodes (that is: claims and arguments) quickly by focusing on their key points (proposition) or main ideas (gist). "
        "A good sketch includes all the important claims and arguments, connects them provisionally via support and attack relations, "
        "captures the main point of each claim and argument, and identifies each node by means of concise and distinct labels.\n"
        "\n"
        "Typical actions in sketch mode include:\n"
        f'{NextAction(tool="add_claim", params={"label": "Claim Label", "proposition": "The proposition maintained by this claim."}, reason="Add a new claim.", action_type="expand").model_dump()}\n'
        f'{NextAction(tool="add_argument", params={"label": "Argument Label", "gist": "The main idea of this argument."}, reason="Add a new argument.", action_type="expand").model_dump()}\n'
        f'{NextAction(tool="connect", params={"source": "Argument Label", "target": "Claim Label", "relation_type": "support"}, reason="Connect an argument to a claim with a support relation.", action_type="expand").model_dump()}\n'
        "\n"
    )
    if app_ctx.mode == "sketch":
        instructions += "Currently active mode: `sketch` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `sketch` mode call {NextAction(tool='set_mode', params={'mode': 'sketch'}, reason='Switch to sketch mode.')}."
    return instructions

def instruction_elaborate(app_ctx: AppContext) -> str:
    instructions = (
        "### Elaborating Instructions\n"
        "\n"
        "Elaborate mode is designed for fleshing out the details of your argument map. "
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
        "In the `elaborate` mode, you'd typically work on individual arguments, clarifying their conclusions and unfolding their premises. "
        "You iteratively improve the argument reconstructions, trying to ground more and more dialectical relations in order to"
        "obtain an ever more coherent and well-structured argument map.\n"
        "\n"
        "Typical actions in elaborate mode include:\n"
        f'{NextAction(tool="edit", params={"label": "Claim Label", "field": "proposition", "edit_options": {"new_value": "The revised and clarified proposition of this claim."}}, reason="Edit an existing claim to add more detail.", action_type="refine").model_dump()}\n'
        f'{NextAction(tool="edit", params={"label": "Argument Label", "field": "conclusion", "edit_options": {"new_value": "The proposition serving as the conclusion of this argument."}}, reason="Edit an existing argument to add more detail.", action_type="refine").model_dump()}\n'
        f'{NextAction(tool="edit", params={"label": "Argument Label", "field": "premises", "edit_options": {"new_value": "The proposition to be added as further premise of this argument."}}, reason="Add a premise to an existing argument.", action_type="refine").model_dump()}\n'
        f'{NextAction(tool="connect", params={"source": "Argument 1", "target": "Argument 2", "relation_type": "attack", "target_premise_idx": "2"}, reason="Ground attack relation by specifying that the conclusion of <Argument 1> negates premise (2) of <Argument 2>.", action_type="refine").model_dump()}\n'
        "\n"
    )
    if app_ctx.mode == "elaborate":
        instructions += "Currently active mode: `elaborate` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `elaborate` mode call {NextAction(tool='set_mode', params={'mode': 'elaborate'}, reason='Switch to elaborate mode.').model_dump()}."
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
        "Typical tool calls in review mode include:\n"
        f'{NextAction(tool="inspect_graph", params={}, reason="Inspect the overall structure of the argument map.", action_type="review").model_dump()}\n'
        f"{NextAction(tool='validate', params={}, reason='Run validation to identify issues in the argument map that need attention.', action_type='review').model_dump()}\n"
        f"{NextAction(tool='inspect_neighborhood', params={'label': 'Node Label'}, reason='Inspect the local neighborhood of a specific node to understand its connections and context.', action_type='review').model_dump()}\n"
        f"{NextAction(tool='inspect_node', params={'label': 'Node Label'}, reason='Inspect the details of a specific node to evaluate its content and role in the argument map.', action_type='review').model_dump()}\n"
        "\n"
    )
    if app_ctx.mode == "review":
        instructions += "Currently active mode: `review` mode."
    else:
        instructions += f"Currently active mode: `{app_ctx.mode}` mode. To switch to `review` mode call {NextAction(tool='set_mode', params={'mode': 'review'}, reason='Switch to review mode.').model_dump()}."
    return instructions

##################################
# Topic specific instructions    #
##################################


def instructions_grounding() -> str:
    return (
        "# How to make sure that dialectical relations are grounded\n"
        "\n"
        "Grounding refers to the process of establishing clear and explicit connections between the nodes in your argument map. "
        "This involves ensuring that support and attack relations are justified by the content of the nodes involved.\n"
        "\n"
        "To ground a support relation, verify that the supporting node provides a conclusion that is equivalent to a premise of the supported node. "
        "For attack relations, ensure that the attacking node has a conclusion that directly contradicts a premise of the attacked node.\n"
        "\n"
        "## Scenarios\n"
        "\n"
        "So let us suppose that you've sketched a support relation between two arguments: <A> supports <B>. There are different strategies for elaborating these "
        "two arguments, <A> and <B>, so as to ground the relation. But in any case, the first thing to do is to carefully study the current content of the two "
        "nodes <A> and <B>.\n"
        "\n"
        "**Scenario 1:** <A> and <B> have premise-conclusion structures, and one premise of <B> neatly matches the conclusion of <A>\n"
        "You judge that a premise of the supported argument <B> (with index `premise_idx`) semantically matches the conclusion of the supporting argument <A>. "
        "In this case, you can ground the support relation in alternative ways:\n"
        "\n"
        "1. To keep both propositions, do:\n"
        f"  - {NextAction(tool='connect', params={'source': 'A', 'target': 'B', 'relation_type': 'support', 'target_premise_idx': 'premise_idx', 'grounding_strategy': 'define_equivalence'}, reason='Define the conclusion of <A> to be equivalent to the premise (with index `premise_idx`) of <B>.').model_dump()}\n"
        "2. To replace the premise of the supported argument <B> with the matching conclusion, do:\n"
        f"  - {NextAction(tool='edit', params={'label': 'B', 'field': 'premises', 'edit_options': {'old_value': 'Exact content of premise at `premise_idx` in <B>.', 'new_value': 'Exact content of conclusion of <A>.'}}, reason='Replace the premise (with index `premise_idx`) of <B> with the conclusion of <A>.').model_dump()}\n"
        "3. To replace the conclusion of the supporting argument <A> with the matching premise, do:\n"
        f"  - {NextAction(tool='edit', params={'label': 'A', 'field': 'conclusion', 'edit_options': {'new_value': 'Exact content of premise at `premise_idx` in <B>.'}}, reason='Set conclusion of <A> to be equal to the premise (with index `premise_idx`) of <B>.').model_dump()}\n"
        "\n"
        "**Scenario 2:** <A> and <B> have premise-conclusion structures, but no premise of <B> matches the conclusion of <A>\n"
        "\n"
        "To ground the support relation in this case, you need to revise the internal strcuture of either <A> or <B> (or both). You can do this in alternative ways:\n"
        "1. Modify an existing premise of <B> (at `premise_idx`) so that it matches the conclusion of <A> (no string identify required):\n"
        f"  - {NextAction(tool='edit', params={'label': 'B', 'field': 'premises', 'edit_options': {'old_value': 'Exact content of old premise.', 'new_value': 'Revised premise, informally matching conclusion of <A>.'}}, reason='Revise an existing premise of <B> to match the conclusion of <A>. (1/2)').model_dump()}\n"
        f"  - {NextAction(tool='connect', params={'source': 'A', 'target': 'B', 'relation_type': 'support', 'target_premise_idx': 'premise_idx', 'grounding_strategy': 'define_equivalence'}, reason='Define the conclusion of <A> to be equivalent to the revised premise (with index `premise_idx`) of <B>.').model_dump()}\n"
        "2. Modify the conclusion of <A> so that it matches an existing premise of <B> (at `premise_idx`):\n"
        f"  - {NextAction(tool='edit', params={'label': 'A', 'field': 'conclusion', 'edit_options': {'new_value': 'Revised conclusion, informally matching premise at `premise_idx` of <B>.'}}, reason='Revise the conclusion of <A> to match the premise (with index `premise_idx`) of <B>. (1/2)').model_dump()}\n"
        f"  - {NextAction(tool='connect', params={'source': 'A', 'target': 'B', 'relation_type': 'support', 'target_premise_idx': 'premise_idx', 'grounding_strategy': 'define_equivalence'}, reason='Define the revised conclusion of <A> to be equivalent to the premise (with index `premise_idx`) of <B>.').model_dump()}\n"
        "3. Add the conclusion of <A> as an additional premise to <B>:\n"
        f"  - {NextAction(tool='edit', params={'label': 'B', 'field': 'premises', 'edit_options': {'new_value': 'Exact content of conclusion of <A>.'}}, reason='Add the conclusion of <A> as an additional premise to <B>.').model_dump()}\n"
        "4. Use a premise of <B> as the conclusion of <A>:\n"
        f"  - {NextAction(tool='edit', params={'label': 'A', 'field': 'conclusion', 'edit_options': {'new_value': 'Exact content of premise at `premise_idx` in <B>.'}}, reason='Set premise (with index `premise_idx`) of <B> as conclusion of <A> (discarding the old conclusion).').model_dump()}\n"
        "\n"
        "**Scenario 3:** <B> is fully elaborated, but <A> lacks a premise-conclusion structure\n"
        "To ground the support relation in this case, use the gist of <A> to identify which premise exactly the argument is supposed to support.\n"
        "\n"
        "1. Use an existing premise of <B> as new conclusion of <A>:\n"
        f"  - {NextAction(tool='edit', params={'label': 'A', 'field': 'conclusion', 'edit_options': {'new_value': 'Exact content of premise in <B> that is supported by <A>.'}}, reason='Set premise of <B> as conclusion of <A>.').model_dump()}\n"
        "\n"
        "**Scenario 4:** <A> is fully elaborated, but <B> lacks a premise-conclusion structure\n"
        "To ground the support relation in this case, declare the conclusion of <B>, add the conclusion of <A> as a new premise to <B>, and continue adding further premises as necessary:\n"
        "\n"
        f"  - {NextAction(tool='edit', params={'label': 'B', 'field': 'conclusion', 'edit_options': {'new_value': 'The proposition serving as the conclusion of this argument.'}}, reason='Set the conclusion of <B>.').model_dump()}\n"
        f"  - {NextAction(tool='edit', params={'label': 'B', 'field': 'premises', 'edit_options': {'new_value': 'Exact content of conclusion of <A>.'}}, reason='Add the conclusion of <A> as a premise to <B>.').model_dump()}\n"
        "\n"
        "## Further Advice\n"
        "\n"
        "When **grounding attack relations** elaborate and revise the premise conclusion structures of the adjacent nodes until the conclusion of the attacking "
        "argument clearly and plainly contradicts a premise of the attacked argument (at `premise_idx`). Then, ground the relation by defining these two statements "
        "as contradictory with:\n"
        f"- {NextAction(tool='connect', params={'source': 'A', 'target': 'B', 'relation_type': 'attack', 'target_premise_idx': 'premise_idx', 'grounding_strategy': 'define_negation'}, reason='Define the conclusion of <A> to contradict the premise (with index `premise_idx`) of <B>.').model_dump()}\n"
        "\n"
        "Keep in mind that changing the content of the arguments will affect the **correctness of the inference** from premises to conclusion. Dropping premises, or revising a conclusion "
        "may turn a previously valid argument into an invalid one, so proceed with caution and consider revising other parts of the arguments than those adjusted for grounding purposes.\n"
        "\n"
        "Attempts to ground a sketched dialectic relation may fail for different reasons, e.g. because the conclusion of the supporting/attacking argument is not related to any relevant premise "
        "of the supported/attacked argument -- no matter how exactly you elaborate the latter one. In such cases, the original dialectical relation should be reconsidered and possibly removed from "
        "the argument map. Reconsider whether the supporting/attacking argument has another dialectical function:\n"
        "- maybe an argument A, rather than supporting B, is an alternatiove justification of the B's conclusion, in which case A and be would be parallel arguments supporting the "
        "same claims / arguments;\n"
        "- maybe an argument A, rather than supporting claim C, is attacking an argument B that attacks C, in which case A would defend C against an objection (posed by B);\n"
        "- maybe an argument A, rather than attacking B, is actually attacking the claim C that B supports, in which case A would be a direct objection to C; etc.\n"
    )


def instructions_validity() -> str:
    return (
        "# How to make sure that an argument's inference from premises to conclusions is valid\n"
        "\n"
        "Validity in argument maps refers to the logical soundness of the arguments presented. "
        "An argument is considered valid if the conclusion logically follows from the premises provided.\n"
        "\n"
        "To ensure validity, review the argument in your map to confirm that:\n"
        "- The argument's conclusion cannot be false if all its premises are true.\n"
        "\n"
        "If you find that an argument is invalid, consider revising it by:\n"
        "- Adding missing premises that are necessary for the conclusion to follow.\n"
        "- Modifying existing premises to better support the conclusion.\n"
        "- Rephrasing (typically weakening) the conclusion to ensure it accurately reflects (i.e., follows from) the premises.\n"
        "\n"
        "Also, ensure that all premises are actually relevant and necessary to infer the conclusion.\n"
        "- Remove any premises that may be deleted without affecting the argument's validity.\n"
        "- Remove in particular redundant premises, e.g. those that are logically implied by other premises.\n"
        "- Consider splitting complex arguments into simpler sub-arguments, or parallel arguments, if they contain multiple lines of reasoning.\n"
    )



@mcp.resource("argmap://instructions")
async def instruction_resource() -> str:
    """Provide instruction text for different modes."""
    app_ctx = mcp.get_context().request_context.lifespan_context
    mode = app_ctx.mode
    match mode:
        case "sketch":
            return instructions_sketch(app_ctx)
        case "elaborate":
            return instruction_elaborate(app_ctx)
        case "review":
            return instruction_review(app_ctx)
        case _:
            return f"Unknown mode {mode}. Available modes: sketch, elaborate, review."


# @mcp.resource("argmap://instructions/grounding")


# @mcp.resource("argmap://instructions/merging")

