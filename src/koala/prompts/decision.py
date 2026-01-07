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
    return f"Decide: {decision_problem} Think carefully and comprehensively. Use available thinking tools to structure your deliberation. Review and iteratively refine your reasoning graph as necessary."
