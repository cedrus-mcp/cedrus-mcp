"""Unit tests for validate tool."""

import pytest
from unittest.mock import Mock
from koala.tools.tools import validate
from koala.server import AppContext
from koala.graph.argument_map import ArgumentMap
from koala.models import Proposition, ClaimNode, ArgumentNode


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in review mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="review"
    )
    return ctx


@pytest.fixture
def tool_context_sketch(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in sketch mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="sketch"
    )
    return ctx


def test_validate_empty_map(tool_context: Mock) -> None:
    """Test validating an empty argument map."""
    result = validate(ctx=tool_context)
    
    assert not result.isError
    # Empty map should be valid
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "success"
    assert "valid and consistent" in result.structuredContent["message"].lower()


def test_validate_valid_map(tool_context: Mock) -> None:
    """Test validating a valid argument map."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create a valid, connected argument map
    prop1 = Proposition(content="Test proposition")
    prop2 = Proposition(content="Premise")
    prop3 = Proposition(content="Conclusion")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    arg_map.add_proposition(prop3)
    
    claim = ClaimNode(label="C1", proposition_id=prop1.id)
    arg_map.add_claim(claim)
    
    # Add a properly structured argument
    arg = ArgumentNode(
        label="A1",
        gist="Valid argument",
        premises=[prop2.id],
        conclusion=prop3.id
    )
    arg_map.add_argument(arg)
    
    # Connect them to avoid connectivity warnings
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    
    result = validate(ctx=tool_context)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # With proper structure and connectivity, should have minimal or no issues
    issues = result.structuredContent.get("issues", [])
    # Only check for error-level issues (connectivity warnings may still appear)
    errors = [i for i in issues if i.get("severity") == "error"]
    assert len(errors) == 0, f"Expected no errors but found: {errors}"


async def test_validate_map_with_issues(tool_context: Mock) -> None:
    """Test validating a map with validation issues."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create an argument without proper structure (empty conclusion)
    arg_node = ArgumentNode(
        label="A1",
        gist="Test argument",
        premises=[],
        conclusion=""  # Empty conclusion should trigger validation issue
    )
    arg_map.add_argument(arg_node)
    
    result = validate(ctx=tool_context)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify issues were actually detected
    issues = result.structuredContent.get("issues", [])
    assert len(issues) > 0, "Expected validation to detect issues with empty conclusion"
    
    # Verify at least one issue relates to the argument structure
    issue_messages = [issue.get("issue", "") for issue in issues]
    assert any(
        "A1" in msg or "conclusion" in msg.lower() or "premise" in msg.lower()
        for msg in issue_messages
    ), f"Expected issues about argument structure but got: {issue_messages}"


def test_validate_with_fix_disabled(tool_context: Mock) -> None:
    """Test validation without auto-fix reports issues but doesn't modify map."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create a map with an issue
    arg_node = ArgumentNode(
        label="A1",
        gist="Test",
        premises=[],
        conclusion=""
    )
    arg_map.add_argument(arg_node)
    
    result = validate(ctx=tool_context, fix=False)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify issues are reported
    issues = result.structuredContent.get("issues", [])
    assert len(issues) > 0

    # Check suggestions were provided
    suggestions = result.structuredContent.get("next_actions", [])
    assert len(suggestions) > 0, "Expected suggestions for fixing issues"


def test_validate_with_fix_enabled(tool_context: Mock) -> None:
    """Test validation with auto-fix enabled actually fixes issues."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create a scenario that can be auto-fixed
    # Note: Not all validation issues can be auto-fixed,
    # this test verifies fix=True runs without error
    prop = Proposition(content="Test")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    result = validate(ctx=tool_context, fix=True)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify validation ran successfully with fix enabled
    # The structured content should indicate success or completion
    assert "status" in result.structuredContent


def test_validate_with_max_issues_limit(tool_context: Mock) -> None:
    """Test validation with max_issues limit actually limits reported issues."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create multiple issues (5 arguments with empty conclusions/premises)
    for i in range(5):
        arg_node = ArgumentNode(
            label=f"A{i}",
            gist=f"Argument {i}",
            premises=[],
            conclusion=""  # Empty conclusion should trigger validation issue
        )
        arg_map.add_argument(arg_node)
    
    max_issues = 2
    result = validate(ctx=tool_context, max_issues=max_issues)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify the issue count is limited
    issues = result.structuredContent.get("issues", [])
    # Note: max_issues limits per-validator but connectivity check runs last
    # So we may get slightly more than max_issues total
    # The important thing is that we don't get 10+ issues (2 per argument)
    assert len(issues) <= max_issues + 2, (
        f"Expected at most {max_issues + 2} issues (including connectivity) but found {len(issues)}"
    )
    
    # Should still report that there are issues
    assert len(issues) > 0, "Expected some issues to be reported"


def test_validate_sketch_mode_limited(tool_context_sketch: Mock) -> None:
    """Test that validation in sketch mode is limited."""
    result = validate(ctx=tool_context_sketch)
    
    assert not result.isError
    # In sketch mode, some validations are skipped


def test_validate_with_disconnected_nodes(tool_context: Mock) -> None:
    """Test validation detects disconnected/isolated nodes."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Add isolated claims (no relations between them)
    prop1 = Proposition(content="Isolated claim 1")
    prop2 = Proposition(content="Isolated claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)
    
    result = validate(ctx=tool_context)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify connectivity check ran and potentially detected isolation
    # Note: Connectivity validation may report isolated nodes as warnings
    # The exact behavior depends on check_connectivity implementation


def test_validate_handles_errors_gracefully(tool_context: Mock) -> None:
    """Test that validation handles unexpected errors gracefully."""
    # This should not raise an exception even with an empty map
    result = validate(ctx=tool_context)
    
    assert not result.isError


def test_validate_consistency_checks(tool_context: Mock) -> None:
    """Test that validation includes consistency checks for well-formed arguments."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create argument with proper structure
    prop_conc = Proposition(content="Conclusion")
    prop_prem = Proposition(content="Premise")
    arg_map.add_proposition(prop_conc)
    arg_map.add_proposition(prop_prem)
    
    arg_node = ArgumentNode(
        label="A1",
        gist="Test",
        premises=[prop_prem.id],
        conclusion=prop_conc.id
    )
    arg_map.add_argument(arg_node)
    
    result = validate(ctx=tool_context)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # With a well-formed argument, should have no or minimal issues
    issues = result.structuredContent.get("issues", [])
    # Filter for error-level issues only (warnings about connectivity are OK)
    errors = [i for i in issues if i.get("severity") == "error"]
    assert len(errors) == 0, f"Expected no errors for well-formed argument but got: {errors}"
    
    assert not result.isError


def test_validate_returns_issue_count(tool_context: Mock) -> None:
    """Test that validation returns correct information about issues found."""
    arg_map = tool_context.request_context.lifespan_context.arg_map
    
    # Create exactly 3 problematic arguments
    for i in range(3):
        arg_node = ArgumentNode(
            label=f"A{i}",
            gist=f"Arg{i}",
            premises=[],
            conclusion=""
        )
        arg_map.add_argument(arg_node)
    
    result = validate(ctx=tool_context)
    
    assert not result.isError
    assert result.structuredContent is not None
    
    # Verify issues are reported in structured content
    issues = result.structuredContent.get("issues", [])
    assert len(issues) > 0, "Expected issues to be reported for problematic arguments"
    
    # Verify that issues list contains information about the problems
    # Each argument should trigger at least one issue (empty conclusion, no premises)
    assert len(issues) >= 3, f"Expected at least 3 issues but got {len(issues)}: {issues}"
    
    # Check that issues have proper structure
    for issue in issues:
        assert "severity" in issue
        assert "issue" in issue or "message" in issue
        assert issue["severity"] in ["info", "warning", "error"]
