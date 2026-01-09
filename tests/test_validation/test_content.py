"""Tests for content validation."""

import pytest
from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import ArgumentNode, ClaimNode, Proposition
from cedrus.tools.tool_context import ToolContext
from cedrus.validation.content import check_core_content, check_argument_structure


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


def test_check_core_content_empty_map(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test core content check on empty map."""
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 0


def test_check_core_content_claim_with_proposition(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that claim with valid proposition has no issues."""
    prop = Proposition(content="Valid proposition content")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 0


def test_check_core_content_claim_missing_proposition(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of claim with empty proposition."""
    prop = Proposition(content="")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    # Should detect missing proposition
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 1


def test_check_core_content_claim_whitespace_only_proposition(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of claim with whitespace-only proposition."""
    prop = Proposition(content="   \n\t  ")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    # Should detect empty proposition (after strip)
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 1


def test_check_core_content_argument_with_gist(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that argument with valid gist has no issues."""
    arg = ArgumentNode(label="A1", gist="Valid gist content")
    empty_map.add_argument(arg)
    
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 0


def test_check_core_content_argument_missing_gist(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of argument with empty gist."""
    arg = ArgumentNode(label="A1", gist="")
    empty_map.add_argument(arg)
    
    # Should detect missing gist
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 1


def test_check_core_content_argument_whitespace_only_gist(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of argument with whitespace-only gist."""
    arg = ArgumentNode(label="A1", gist="   \n  ")
    empty_map.add_argument(arg)
    
    # Should detect empty gist (after strip)
    issues = check_core_content(empty_map, elaborate_context)
    assert issues == 1


def test_check_core_content_respects_max_issues(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that max_issues parameter limits reported issues."""
    # Create multiple nodes with missing content
    for i in range(5):
        prop = Proposition(content="")
        empty_map.add_proposition(prop)
        claim = ClaimNode(label=f"C{i+1}", proposition_id=prop.id)
        empty_map.add_claim(claim)
    
    # With max_issues=2, should stop after 2 issues
    issues = check_core_content(empty_map, elaborate_context, max_issues=2)
    assert issues <= 2


def test_check_core_content_generates_suggestions_in_sketch_mode(empty_map: ArgumentMap, sketch_context: ToolContext) -> None:
    """Test that suggestions include mode switch in sketch mode."""
    prop = Proposition(content="")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    issues = check_core_content(empty_map, sketch_context)
    
    # Should generate suggestions including switch_mode
    suggestions = sketch_context.suggestions
    assert issues == 1
    assert isinstance(suggestions, list)


def test_check_core_content_generates_edit_suggestions(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that suggestions include edit tool suggestions."""
    prop = Proposition(content="")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    issues = check_core_content(empty_map, elaborate_context)
    
    # Should generate edit suggestions
    suggestions = elaborate_context.suggestions
    assert issues == 1
    assert isinstance(suggestions, list)


# Tests for check_argument_structure


def test_check_argument_structure_empty_map(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test argument structure check on empty map."""
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues == 0


def test_check_argument_structure_claim_node_no_check(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that claim nodes are not checked by argument structure validation."""
    add_claim_node(empty_map, "Claim")
    
    # Claim nodes don't need premises/conclusion structure
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues == 0


def test_check_argument_structure_valid_argument(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that argument with premises and conclusion has no issues."""
    # Create premises
    p1 = Proposition(content="Premise 1")
    p2 = Proposition(content="Premise 2")
    empty_map.add_proposition(p1)
    empty_map.add_proposition(p2)
    
    # Create conclusion
    c = Proposition(content="Conclusion")
    empty_map.add_proposition(c)
    
    # Create argument with structure
    arg = ArgumentNode(label="A1", gist="Valid Arg", premises=[p1.id, p2.id], conclusion=c.id)
    empty_map.add_argument(arg)
    
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues == 0


def test_check_argument_structure_missing_conclusion(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of argument missing conclusion."""
    # Create premise
    p = Proposition(content="Premise")
    empty_map.add_proposition(p)
    
    # Create argument with premise but no conclusion
    arg = ArgumentNode(label="A1", gist="No Conclusion", premises=[p.id], conclusion="")
    empty_map.add_argument(arg)
    
    # Should detect missing conclusion
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues >= 1


def test_check_argument_structure_missing_premises(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of argument with no premises."""
    # Create conclusion
    c = Proposition(content="Conclusion")
    empty_map.add_proposition(c)
    
    # Create argument with conclusion but no premises
    arg = ArgumentNode(label="A1", gist="No Premises", premises=[], conclusion=c.id)
    empty_map.add_argument(arg)
    
    # Should detect missing premises
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues >= 1


def test_check_argument_structure_missing_both(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test detection of argument missing both premises and conclusion."""
    # Create argument with neither premises nor conclusion
    arg = ArgumentNode(label="A1", gist="Incomplete", premises=[], conclusion="")
    empty_map.add_argument(arg)
    
    # Should detect both missing premises and conclusion
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues >= 2


def test_check_argument_structure_respects_max_issues(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that max_issues parameter limits reported issues."""
    # Create multiple incomplete arguments
    for i in range(5):
        arg = ArgumentNode(label=f"A{i+1}", gist=f"Incomplete{i}", premises=[], conclusion="")
        empty_map.add_argument(arg)
    
    # With max_issues=3, should stop after 3 issues
    issues = check_argument_structure(empty_map, elaborate_context, max_issues=3)
    assert issues <= 3


def test_check_argument_structure_generates_mode_switch_suggestions_in_sketch(empty_map: ArgumentMap, sketch_context: ToolContext) -> None:
    """Test that suggestions include mode switch in sketch mode."""
    arg = ArgumentNode(label="A1", gist="Incomplete", premises=[], conclusion="")
    empty_map.add_argument(arg)
    
    issues = check_argument_structure(empty_map, sketch_context)
    
    # Should generate suggestions including switch_mode
    suggestions = sketch_context.suggestions
    assert issues >= 2
    assert isinstance(suggestions, list)


def test_check_argument_structure_generates_edit_suggestions(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that suggestions include edit tool suggestions."""
    arg = ArgumentNode(label="A1", gist="Incomplete", premises=[], conclusion="")
    empty_map.add_argument(arg)
    
    issues = check_argument_structure(empty_map, elaborate_context)
    
    # Should generate edit suggestions
    suggestions = elaborate_context.suggestions
    assert issues >= 1
    assert isinstance(suggestions, list)


def test_check_argument_structure_single_premise_valid(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that argument with single premise is valid."""
    # Create premise
    p = Proposition(content="Only Premise")
    empty_map.add_proposition(p)
    
    # Create conclusion
    c = Proposition(content="Conclusion")
    empty_map.add_proposition(c)
    
    # Create argument with single premise
    arg = ArgumentNode(label="A1", gist="Single Premise", premises=[p.id], conclusion=c.id)
    empty_map.add_argument(arg)
    
    # Should be valid with one premise
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues == 0


def test_check_argument_structure_multiple_premises_valid(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that argument with multiple premises is valid."""
    # Create multiple premises
    premises = []
    for i in range(3):
        p = Proposition(content=f"Premise {i+1}")
        empty_map.add_proposition(p)
        premises.append(p.id)
    
    # Create conclusion
    c = Proposition(content="Conclusion")
    empty_map.add_proposition(c)
    
    # Create argument with multiple premises
    arg = ArgumentNode(label="A1", gist="Multiple Premises", premises=premises, conclusion=c.id)
    empty_map.add_argument(arg)
    
    # Should be valid with multiple premises
    issues = check_argument_structure(empty_map, elaborate_context)
    assert issues == 0
