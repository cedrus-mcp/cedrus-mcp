"""Prompt templates for decision-making tasks."""

from koala.server import mcp


@mcp.prompt()
def simple_decision(decision_problem: str) -> str:
    """A simple decision prompt template for making deliberate choices.
    
    Args:
        decision_problem: The decision problem cast as a question.
    
    Returns:
        A formatted prompt that guides the deliberation process.
    """
    return f"Decide: {decision_problem} Think carefully and comprehensively. Use available thinking tools to structure your deliberation. Review and iteratively refine your reasoning graph as necessary."
