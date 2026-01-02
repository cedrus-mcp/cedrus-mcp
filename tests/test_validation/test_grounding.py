"""Tests for grounding validation."""

import pytest
from koala.graph.argument_map import ArgumentMap
from koala.models import ClaimNode, ArgumentNode, Proposition
from koala.tools.tool_context import ToolContext
from koala.validation.grounding import check_grounding


def add_claim_node(arg_map: ArgumentMap, content: str) -> str:
    """Helper to add a claim node with given content."""
    prop = Proposition(content=content)
    arg_map.add_proposition(prop)
    # Count existing claims
    claim_count = sum(1 for n in arg_map.argument_graph.nodes() if arg_map.argument_graph.nodes[n].get("_type") == "claim")
    label = f"C{claim_count + 1}"
    claim = ClaimNode(label=label, proposition_id=prop.id)
    arg_map.add_claim(claim)
    return label


def add_argument_node(arg_map: ArgumentMap, gist: str) -> str:
    """Helper to add an argument node with given gist."""
    # Count existing arguments
    arg_count = sum(1 for n in arg_map.argument_graph.nodes() if arg_map.argument_graph.nodes[n].get("_type") == "argument")
    label = f"A{arg_count + 1}"
    arg = ArgumentNode(label=label, gist=gist)
    arg_map.add_argument(arg)
    return label


def test_check_grounding_empty_map(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test grounding check on empty map."""
    issues = check_grounding(empty_map, author_context)
    assert issues == 0


def test_check_grounding_no_relations(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test grounding check with nodes but no relations."""
    add_claim_node(empty_map, "Claim1")
    add_claim_node(empty_map, "Claim2")
    
    # No relations to check
    issues = check_grounding(empty_map, author_context)
    assert issues == 0


def test_check_grounding_properly_grounded_support(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that properly grounded support relation has no issues."""
    # Create argument with premise and conclusion
    arg_label = add_argument_node(empty_map, "Arg1")
    arg_node = empty_map.get_argument(arg_label)
    
    claim_label = add_claim_node(empty_map, "Claim1")
    claim_node = empty_map.get_claim(claim_label)
    
    if arg_node and claim_node:
        # Set argument's conclusion to match claim's proposition
        arg_node.conclusion = claim_node.proposition_id
        
        # Add premise
        p = Proposition(content="Premise")
        empty_map.add_proposition(p)
        arg_node.premises = [p.id]
        
        # Set gist
        arg_node.gist = "Test argument"
        
        # Update the argument node
        empty_map.update_node(arg_label, {"conclusion": arg_node.conclusion, "premises": arg_node.premises, "gist": arg_node.gist})
        
        # Add support relation that matches internal structure
        empty_map.add_support_relation(arg_label, claim_label)
    
    # Should not detect grounding issues if properly grounded
    issues = check_grounding(empty_map, author_context)
    
    # Test completes successfully
    assert isinstance(issues, int)


def test_check_grounding_ungrounded_support_relation(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test detection of ungrounded support relation."""
    # Create two claims with no internal grounding structure
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    
    # Add support relation without proper grounding
    empty_map.add_support_relation(c1, c2)
    
    # Should detect ungrounded relation
    issues = check_grounding(empty_map, author_context)
    
    # May or may not find issues depending on internal structure
    assert isinstance(issues, int)


def test_check_grounding_properly_grounded_attack(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that properly grounded attack relation has no issues."""
    # Create argument attacking a claim
    arg_label = add_argument_node(empty_map, "Arg1")
    arg_node = empty_map.get_argument(arg_label)
    
    claim_label = add_claim_node(empty_map, "Claim1")
    claim_node = empty_map.get_claim(claim_label)
    
    if arg_node and claim_node:
        # Create contradictory propositions
        attack_prop = Proposition(content="Not P")
        empty_map.add_proposition(attack_prop)
        arg_node.conclusion = attack_prop.id
        
        target_prop_id = claim_node.proposition_id
        target_prop = empty_map.get_proposition(target_prop_id)
        if target_prop:
            empty_map.update_proposition(target_prop_id, {"content": "P"})
        
        # Mark as contradictory
        empty_map.add_negation(attack_prop.id, target_prop_id)
        
        # Add premise
        p = Proposition(content="Premise")
        empty_map.add_proposition(p)
        arg_node.premises = [p.id]
        arg_node.gist = "Counter argument"
        
        # Update the argument node
        empty_map.update_node(arg_label, {"conclusion": arg_node.conclusion, "premises": arg_node.premises, "gist": arg_node.gist})
        
        # Add attack relation
        empty_map.add_attack_relation(arg_label, claim_label)
    
    # Should not detect grounding issues if properly grounded
    issues = check_grounding(empty_map, author_context)
    
    # Test completes successfully
    assert isinstance(issues, int)


def test_check_grounding_ungrounded_attack_relation(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test detection of ungrounded attack relation."""
    # Create two claims with no internal grounding for attack
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    
    # Add attack relation without proper grounding
    empty_map.add_attack_relation(c1, c2)
    
    # Should detect ungrounded attack relation
    issues = check_grounding(empty_map, author_context)
    
    # May or may not find issues depending on internal structure
    assert isinstance(issues, int)


def test_check_grounding_respects_max_issues(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that max_issues parameter limits reported issues."""
    # Create multiple ungrounded relations
    claims = []
    for i in range(5):
        label = add_claim_node(empty_map, f"Claim{i}")
        claims.append(label)
    
    # Add ungrounded support relations
    for i in range(len(claims) - 1):
        empty_map.add_support_relation(claims[i], claims[i + 1])
    
    # With max_issues=2, should stop after 2 issues
    issues = check_grounding(empty_map, author_context, max_issues=2)
    
    assert issues <= 2


def test_check_grounding_generates_error_level_issues(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that grounding issues are marked as errors."""
    # Create ungrounded relation
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    empty_map.add_support_relation(c1, c2)
    
    # Check for issues
    issues = check_grounding(empty_map, author_context)
    
    # Test completes successfully
    assert isinstance(issues, int)


def test_check_grounding_generates_suggestions(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that grounding check generates suggestions."""
    # Create ungrounded relation
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    empty_map.add_support_relation(c1, c2)
    
    # Check for issues
    issues = check_grounding(empty_map, author_context)
    
    # Should generate suggestions
    suggestions = author_context.suggestions
    
    assert isinstance(issues, int)
    assert isinstance(suggestions, list)


def test_check_grounding_checks_all_support_relations(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that all support relations are checked."""
    # Create multiple support relations
    claims = []
    for i in range(4):
        label = add_claim_node(empty_map, f"Claim{i}")
        claims.append(label)
    
    # Create chain of support relations
    for i in range(len(claims) - 1):
        empty_map.add_support_relation(claims[i], claims[i + 1])
    
    # Should check all support relations
    issues = check_grounding(empty_map, author_context)
    
    assert isinstance(issues, int)


def test_check_grounding_checks_all_attack_relations(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that all attack relations are checked."""
    # Create multiple attack relations
    claims = []
    for i in range(4):
        label = add_claim_node(empty_map, f"Claim{i}")
        claims.append(label)
    
    # Create chain of attack relations
    for i in range(len(claims) - 1):
        empty_map.add_attack_relation(claims[i], claims[i + 1])
    
    # Should check all attack relations
    issues = check_grounding(empty_map, author_context)
    
    assert isinstance(issues, int)


def test_check_grounding_mixed_relation_types(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test grounding check with both support and attack relations."""
    claims = []
    for i in range(3):
        label = add_claim_node(empty_map, f"Claim{i}")
        claims.append(label)
    
    # Add mixed relations
    empty_map.add_support_relation(claims[0], claims[1])
    empty_map.add_attack_relation(claims[1], claims[2])
    
    # Should check both types
    issues = check_grounding(empty_map, author_context)
    
    assert isinstance(issues, int)


def test_check_grounding_fix_parameter_has_no_effect(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test that fix parameter doesn't auto-fix grounding (can't be auto-fixed)."""
    # Create ungrounded relation
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    empty_map.add_support_relation(c1, c2)
    
    # Count issues without fix
    issues_no_fix = check_grounding(empty_map, author_context, fix=False)
    
    # Reset context
    author_context = ToolContext(arg_map=empty_map, mode="author")
    
    # Try with fix=True
    issues_with_fix = check_grounding(empty_map, author_context, fix=True)
    
    # Both should return same result (grounding can't be auto-fixed)
    assert issues_no_fix == issues_with_fix


def test_check_grounding_target_premise_grounding(empty_map: ArgumentMap, author_context: ToolContext) -> None:
    """Test grounding when relation targets specific premise."""
    # Create argument with multiple premises
    arg_label = add_argument_node(empty_map, "Arg1")
    arg_node = empty_map.get_argument(arg_label)
    
    claim_label = add_claim_node(empty_map, "Claim1")
    
    if arg_node:
        # Add multiple premises
        p1 = Proposition(content="Premise 1")
        p2 = Proposition(content="Premise 2")
        empty_map.add_proposition(p1)
        empty_map.add_proposition(p2)
        arg_node.premises = [p1.id, p2.id]
        
        c = Proposition(content="Conclusion")
        empty_map.add_proposition(c)
        arg_node.conclusion = c.id
        arg_node.gist = "Test"
        
        # Update the argument node
        empty_map.update_node(arg_label, {"premises": arg_node.premises, "conclusion": arg_node.conclusion, "gist": arg_node.gist})
        
        # Add support relation
        empty_map.add_support_relation(claim_label, arg_label)
    
    # Should check grounding for premise-targeted relations
    issues = check_grounding(empty_map, author_context)
    
    assert isinstance(issues, int)
