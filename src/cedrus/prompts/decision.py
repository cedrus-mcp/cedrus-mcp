"""Prompt templates for decision-making tasks."""

from textwrap import dedent

from cedrus.server import mcp


@mcp.prompt(
    name="deliberate_decision",
    description=dedent("""
        A prompt template for deliberating decision problems and making reasoned choices.
    """).strip(),
)
def deliberate_decision(decision_problem: str) -> str:
    """A simple decision prompt template for making deliberate choices.

    Args:
        decision_problem: The decision problem cast as a question.

    Returns:
        A formatted prompt that guides a structured deliberation process and a clear final answer.
    """

    return dedent(f"""
            Decision problem: **{decision_problem}**

            Think carefully and comprehensively. Use reasoning tools (from `{mcp.name}`) to structure your deliberation. Gradually unfold and refine your thoughts by building a reasoning graph that adequately captures and clarifies all considerations you deem relevant for making the decision at hand.

            You are *not* following a linear pipeline; instead, repeatedly cycle through reflection, focused building,
            and critical review until your deliberation meets your own standards.

            ## Overall process (SCRUM)

            - **Reflect (Backlog & Definition of Done)**: Clarify the decision, success criteria, and what a “good enough” deliberation looks like. Identify major work items (topics, options, uncertainties) for your reasoning backlog.
            - **Sprint (Focused build cycles)**: In short, focused mini-sprints, expand and update the reasoning graph on a subset of the backlog: add claims, arguments, objections, and counterarguments that seem most important right now.
            - **Iterate (Review, refine, reprioritize)**: Frequently step back to inspect the current graph, test its quality, and reprioritize what to improve next. Expect to loop between reflection, sketching, and refinement multiple times before making a decision.
            - **Finalize (Decision & Communication)**: When your reasoning graph meets your “definition of done”, extract the key insights, make a clear choice.

            ## 1. Initial reflection and orientation

            - Clarify the **decision problem** in your own words. If needed, restate it so that options, constraints, and key uncertainties are explicit.
            - Identify the **main decision options** you might consider. When appropriate, formulate them as clear, mutually exclusive claims in your reasoning graph.
            - Define your **evaluation standards and goals**:
              - What counts as a good decision here (e.g., risk profile, fairness, long-term vs short-term payoffs)?
              - What constraints or non-negotiables must be respected?
            - Set a **“definition of done” for deliberation**:
              - How thorough do you need to be (roughly how many key reasons, objections, uncertainties must be addressed)?
              - Which types of considerations (moral, practical, empirical, emotional, stakeholder-related, etc.) must be at least touched on?
            - Identify **known pitfalls and biases** that are relevant to this decision (e.g., wishful thinking, status quo bias, overconfidence) and note how you intend to guard against them.
            - Optionally create a **reasoning backlog**: a rough list of topics/angles to cover (e.g., “short-term costs”, “long-term upside”, “stakeholder impacts”, “key uncertainties”, “alternatives”).

            Treat this step as setting up your **deliberation backlog** and your criteria for when the reasoning is good enough to inform a choice. You can revisit and adjust these as you learn more.

            ## 2. Sketching a first draft

            - Start with a **lightweight, wide-coverage sketch** of the reasoning graph rather than a detailed analysis.
            - In `sketch` mode:
              - Add nodes for the **main decision options** as claims.
              - Add a first pass of **supporting reasons, objections, and trade-offs** for each option.
              - Recursively add higher-order considerations that support or challenge previously added arguments.
            - Focus on **scope over detail**:
              - Capture all major considerations that come to mind, even if they are vague or preliminary.
              - Prefer rough but explicit nodes over keeping ideas implicit.
            - Annotate **uncertainties and open questions** as you go (e.g., through tags “need-better-data”, or notes “not sure if Y really matters”), and treat these as backlog items for later sprints.
            - Do not aim for perfection at this stage:
              - Allow redundancy, imperfect labels, and fuzzy dialectical relations.
              - The goal of this sprint is a **minimum viable reasoning graph** that roughly maps the space of considerations.
            - After the first sketch, briefly **review the graph**:
              - Check whether any obviously important consideration is missing.
              - Eliminate obvious duplicates and redundancies.
              - Update your backlog with newly discovered subtopics or questions.
              - Decide which parts of the graph should be elaborated in the next sprint.

            Expect to return to this sketching step later to add new branches as your understanding evolves.

            ## 3. Elaborate and refine

            - Work in **short, focused mini-sprints** on selected parts of the graph rather than trying to perfect everything at once.
            - For a chosen subset of nodes (e.g., a key option or a contentious argument):
              - Switch to `elaborate` mode and **spell out premises and conclusions**.
              - Ensure that each argument’s premises plausibly imply its conclusion.
              - Clarify whether each inter-node relation is **supporting** or **attacking**, and why.
            - After each mini-sprint, switch mindset to **review**:
              - Use `review` mode and validation tools to check for gaps, inconsistencies, or unclear structures.
              - Ask whether there are hidden assumptions, missing counterarguments, or irrelevant premises, a mismatch between gist and premise-conclusion structure, etc.
            - Use the review to **reprioritize your backlog**:
              - Mark parts of the graph as “good enough for now”.
              - Identify fragile or central parts that need further refinement.
              - Add new tasks (e.g., “clarify trade-off between A and B”, “add counterarguments to C”).
            - Iterate this **build–review loop**:
              - Merge or split nodes where helpful.
              - Rephrase vague labels to be more precise.
              - Rewire relations to better match the underlying reasoning.
            - Continue iterating until:
              - Major options have both supporting reasons and serious objections.
              - Key uncertainties and trade-offs are explicitly represented.
              - The graph feels **coherent, balanced, and aligned with your “definition of done”**, which you may also
                refine as you go.

            Think of each pass as a sprint: pick a small part of the graph, improve it, then review and update your plan.
            Avoid waiting for a single “perfect” final pass.

            ## 4. Making a choice

            - Transition from **building and refining** to **harvesting insights** from the reasoning graph.
            - Before deciding, briefly **inspect the graph as a whole**:
              - Which option is overall best supported?
              - Which objections remain most serious, and are they acceptable or addressable?
              - How sensitive is your judgment to key uncertainties you identified?
            - Check against your **original standards and “definition of done”**:
              - Have you addressed the categories of considerations you deemed important?
              - If something crucial is still missing, decide whether to run another mini-sprint or accept this as residual uncertainty.
            - Once your deliberation is complete, make your final decision based on the reasoning graph.
            - Provide:
                a. **Final decision**: Clearly state the chosen option.
                b. **Overall assessment**: Briefly summarize how this decision is rooted in your overall assessment of the deliberation (which clusters of reasons mattered most, how you weighed trade-offs, and how you handled remaining uncertainty).

            ## Additional instructions

            - If available, use todo lists to track and manage tasks during your deliberation. Adjust your plan,
              dynamically adding further subtasks, as you see fit.
            - Use the `get_instructions` tool to get further guidance on tools, modes, and best practices.
        """).strip()
