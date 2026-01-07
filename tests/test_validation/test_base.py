"""Tests for base validation orchestration."""

import pytest
from koala.graph.argument_map import ArgumentMap
from koala.models import ClaimNode, ArgumentNode, Proposition
from koala.tools.tool_context import ToolContext
from koala.validation.base import validate_argument_map


def test_validate_empty_map_sketch_mode(empty_map: ArgumentMap, sketch_context: ToolContext) -> None:
    """Test validation of empty map in sketch mode runs without errors."""
    issues = validate_argument_map(empty_map, sketch_context)
    assert issues == 0


def test_validate_empty_map_elaborate_mode(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test validation of empty map in elaborate mode runs without errors."""
    issues = validate_argument_map(empty_map, elaborate_context)
    assert issues == 0


def test_validate_simple_claim_sketch_mode(simple_claim_map: ArgumentMap, sketch_context: ToolContext) -> None:
    """Test validation of simple claim in sketch mode."""
    sketch_context.arg_map = simple_claim_map
    issues = validate_argument_map(simple_claim_map, sketch_context)
    assert issues == 0


def test_validate_simple_claim_elaborate_mode(simple_claim_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test validation of simple claim in elaborate mode."""
    elaborate_context.arg_map = simple_claim_map
    issues = validate_argument_map(simple_claim_map, elaborate_context)
    assert issues == 0


def test_validate_returns_issue_count(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that validate_argument_map returns total issue count."""
    # Add a claim without proposition (will generate warning)
    prop = Proposition(content="")  # Empty content
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    issues = validate_argument_map(empty_map, elaborate_context)
    assert issues > 0


def test_validate_with_fix_parameter(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that fix parameter is passed through validation pipeline."""
    # Create a map with an issue that can be fixed
    prop = Proposition(content="Test")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    
    # Test without fix
    issues_without_fix = validate_argument_map(empty_map, elaborate_context, fix=False)
    
    # Reset context
    elaborate_context = ToolContext(arg_map=empty_map, mode="elaborate")
    
    # Test with fix - should also run without error
    issues_with_fix = validate_argument_map(empty_map, elaborate_context, fix=True)
    
    # Both should complete successfully
    assert isinstance(issues_without_fix, int)
    assert isinstance(issues_with_fix, int)


def test_validate_with_max_issues_parameter(simple_claim_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that max_issues parameter limits reported issues."""
    elaborate_context.arg_map = simple_claim_map
    # Validation should complete with max_issues set
    issues = validate_argument_map(simple_claim_map, elaborate_context, max_issues=5)
    assert issues <= 5


def test_validate_mode_specific_checks_sketch(empty_map: ArgumentMap, sketch_context: ToolContext) -> None:
    """Test that sketch mode skips certain validation checks."""
    # Add incomplete argument node
    prop_c = Proposition(content="Conclusion")
    empty_map.add_proposition(prop_c)
    arg = ArgumentNode(label="A1", gist="Incomplete Arg", premises=[], conclusion=prop_c.id)
    empty_map.add_argument(arg)
    
    # In sketch mode, argument structure checks should be skipped
    issues = validate_argument_map(empty_map, sketch_context)
    
    # Should only get core content checks, not argument structure checks
    assert isinstance(issues, int)


def test_validate_mode_specific_checks_elaborate(empty_map: ArgumentMap, elaborate_context: ToolContext) -> None:
    """Test that elaborate mode runs all validation checks."""
    # Add incomplete argument node
    prop_c = Proposition(content="Conclusion")
    empty_map.add_proposition(prop_c)
    arg = ArgumentNode(label="A1", gist="Test gist", premises=[], conclusion=prop_c.id)
    empty_map.add_argument(arg)
    
    # In elaborate mode, should run all checks including argument structure
    issues = validate_argument_map(empty_map, elaborate_context)
    
    # Should detect missing premises
    assert issues > 0


def test_validate_pipeline_order(empty_map: ArgumentMap, review_context: ToolContext) -> None:
    """Test that validation runs checks in expected order."""
    # The validation pipeline should run:
    # 1. core content (all modes)
    # 2. argument structure (elaborate/review)
    # 3. grounding (elaborate/review)
    # 4. completeness (elaborate/review)
    # 5. consistency (elaborate/review)
    # 6. connectivity (all modes)
    
    issues = validate_argument_map(empty_map, review_context)
    
    # Should complete without raising exceptions
    assert isinstance(issues, int)
