"""Prompt templates for decision-making tasks."""

from textwrap import dedent
from cedrus.server import mcp


@mcp.prompt(
    name="deliberate_decision",
    description=dedent("""
        A prompt template for deliberating decision problems and making reasoned choices.
    """).strip()
)
def deliberate_decision(decision_problem: str) -> str:
    """A simple decision prompt template for making deliberate choices.
    
    Args:
        decision_problem: The decision problem cast as a question.
    
    Returns:
        A formatted prompt that guides a structured deliberation process and a clear final answer.
    """
    return (
        f"Decision problem: **{decision_problem}**\n"
        "\n"
        f"Think carefully and comprehensively. Use reasoning tools (from `{mcp.name}`) to structure your deliberation. "
        "Represent your thinking as a reasoning graph and iteratively refine it so that it adequately captures all "
        "considerations you regard as relevant for making the decision at hand.\n"
        "\n"
        "## Overall process\n"
        "\n"
        "You will work in five main phases to build and refine a reasoning graph, and then finalize your decision.\n"
        "\n"
        "### Phase I: Orientation and Reflection\n"
        "\n"
        "Reflect on, and clarify for your own:\n"
        "\n"
        "- What sort of decision are you facing and which kinds of considerations are pertinent to making a well-reasoned "
        "choice?\n"
        "- What are the standards and criteria your deliberation should meet in order to inform the decision you face?\n"
        "- Which scope and depth of reasoning are you aiming at (quantify in terms of arguments, reasons, objections, etc.)?\n"
        "- What are additional resources you may need to consult when deliberating the decision?\n"
        "- Which pitfalls and fallacies should you avoid, which lurking difficulties will you have to overcome in your "
        "practical deliberation?\n"
        "\n"
        "### Phase II: Outlining (`sketch` mode)\n"
        "\n"
        "- Start in `sketch` mode (resetting the graph if appropriate). Identify the decision option(s) as key claim(s). "
        "If the decision is not binary, explicitly represent the mutually exclusive decision options.\n"
        "- Capture the overall structure of the argumentation and delineate the space of reasons you want to cover.\n"
        "- When relevant, add depths by including counterarguments, back-up arguments, or alternative justifications.\n"
        "- Use clear, precise labels and gists for nodes and propositions; avoid vague wording.\n"
        "- Regularly review and improve your draft as you sketch.\n"
        "\n"
        "### Phase III: Elaborating (`elaborate` mode)\n"
        "\n"
        "- Once you have a preliminary draft of your reasoning graph, switch to `elaborate` mode to add detailed content.\n"
        "- For each argument, spell out how it works by explicitly adding premises and conclusions.\n"
        "- Ensure that (i) the premises of an argument truly _imply_ its conclusion, and (ii) the support and attack "
        "relations between arguments are properly _grounded_ in the internal premise–conclusion structure of the "
        "involved arguments.\n"
        "- These are conflicting demands on the internal premise-conclusion structure, and you will typically iterate and "
        "refine arguments multipole times before arriving at an adequate analysis and explication."
        "- Clarify and refine node labels and gists to ensure they accurately reflect the intended meaning.\n"
        "\n"
        "### Phase IV: Revising (`review` and `elaborate` modes)\n"
        "\n"
        "- After elaborating and refining your draft, switch to `review` mode to critically assess and improve the current "
        "state of your reasoning.\n"
        "- Check whether the reasoning graph adequately captures all relevant considerations for the decision at hand, "
        "including major options, supporting reasons, objections, and trade-offs.\n"
        "- Use tools to *validate* the reasoning graph.\n"
        "- Revise the reasoning graph, e.g.: improve premise-conclusion structures, clarify gists and labels, rewire "
        "dialectical relations, merge or decompose arguments, differentiate claims.\n"
        "- Iterate (between `review` and `elaborate` mode) until the graph passes all validation checks and meets your own "
        "standards of clarity and completeness."
        "- NOTE: This is typically the most work-intensive phase. So take you time.\n"
        "\n" 
        "### Phase V: Finalizing the decision\n"
        "\n"
        "- Once your deliberation is complete, make your final decision based on the reasoning graph.\n"
        "- Consider which option is best supported overall, how sensitive the decision is to key uncertainties, and "
        "whether any important perspectives are still missing.\n"
        "\n"
        "### Your final output\n"
        "\n"
        "When you are ready to answer the user, provide:\n"
        "1. **Final decision**: Clearly state the chosen option.\n"
        "2. **Overall assessment**: Briefly summarize how this decision is rooted in your overall assessment of the "
        "deliberation.\n"
        "\n"
        "## Additional instructions\n"
        "\n"
        "- If available, use todo lists to track and manage tasks during your deliberation. Adjust your plan, "
        "dynamically adding further subtasks, as you see fit. \n"
        "- Use the `get_instructions` tool to get further guidance on tools, modes, and best practices.\n"
    )


