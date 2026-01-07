"""Shared fixtures for validation tests."""

import pytest
from koala.graph.argument_map import ArgumentMap
from koala.models import ClaimNode, ArgumentNode, Proposition
from koala.tools.tool_context import ToolContext


@pytest.fixture
def empty_map() -> ArgumentMap:
    """Create an empty argument map for testing."""
    return ArgumentMap()


@pytest.fixture
def sketch_context(empty_map: ArgumentMap) -> ToolContext:
    """Create a tool context in sketch mode."""
    tc = ToolContext(arg_map=empty_map, mode="sketch")
    return tc


@pytest.fixture
def elaborate_context(empty_map: ArgumentMap) -> ToolContext:
    """Create a tool context in elaborate mode."""
    tc = ToolContext(arg_map=empty_map, mode="elaborate")
    return tc


@pytest.fixture
def review_context(empty_map: ArgumentMap) -> ToolContext:
    """Create a tool context in review mode."""
    tc = ToolContext(arg_map=empty_map, mode="review")
    return tc


@pytest.fixture
def simple_claim_map(empty_map: ArgumentMap) -> ArgumentMap:
    """Create a simple map with one claim node."""
    arg_map = empty_map
    prop = Proposition(content="This is a test claim.")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    return arg_map
