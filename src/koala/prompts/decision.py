"""Prompt templates for decision-making tasks."""

from textwrap import dedent
from koala.server import mcp


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
        A formatted prompt that guides the deliberation process.
    """
    return (
        f"Decide: {decision_problem} "
        "Think carefully and comprehensively. Use available thinking tools to structure your deliberation. "
        "Review and iteratively refine your reasoning graph as necessary.\n"
        "When using reasoning tools, start with `sketch` mode, and switch to `elaborate` mode for adding detailed content. "
        "Then iterate between `review` and `elaborate` mode to refine and consolidate a reasoning graph that passes "
        "all validation checks.\n"
        "Don't hesitate to consult instructions to get hints and guidance.\n"
        "Finally, remember that you're elaborating your own thinking in order to come up with a well-reasoned decision. "
        "The reasoning graph should hence comprehensively and adequately capture the considerations you deem relevant "
        "for making the decision at hand."
    )
