"""Pytest fixtures and configuration."""

from pathlib import Path

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models import ArgumentNode, ClaimNode, Proposition
from cedrus.server import AppContext


@pytest.fixture
def empty_arg_map() -> ArgumentMap:
    """Create an empty ArgumentMap for testing."""
    return ArgumentMap()


@pytest.fixture
def sample_arg_map() -> ArgumentMap:
    """Create a pre-populated ArgumentMap with test data."""
    arg_map = ArgumentMap()

    # Create propositions
    prop1 = Proposition(content="Climate change is real")
    prop2 = Proposition(content="We should reduce emissions")
    prop3 = Proposition(content="97% of scientists agree")
    prop4 = Proposition(content="Evidence is overwhelming")

    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    arg_map.add_proposition(prop3)
    arg_map.add_proposition(prop4)

    # Add claims
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)

    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)

    # Add an argument
    arg1 = ArgumentNode(
        label="A1",
        gist="Scientific consensus argument",
        premises=[prop3.id, prop4.id],
        conclusion=prop1.id,
    )

    arg_map.add_argument(arg1)

    # Add relations
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")

    return arg_map


@pytest.fixture
def temp_data_file(tmp_path: Path) -> Path:
    """Provide a temporary file path for data isolation."""
    return tmp_path / "test_argmap.json"


@pytest.fixture
def mock_app_context(empty_arg_map: ArgumentMap) -> AppContext:
    """Create a mock AppContext for tool testing."""
    return AppContext(arg_map=empty_arg_map, mode="sketch")
