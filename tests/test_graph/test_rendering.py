"""Unit tests for rendering helpers."""

import json

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.graph.rendering import (
    render_argdown,
    render_argdown_node,
    render_nested_json,
    render_nested_yaml,
)
from cedrus.backend.models import ArgumentNode, ClaimNode, Proposition


def test_render_empty_graph() -> None:
    """Test rendering an empty graph."""
    arg_map = ArgumentMap()

    result = render_argdown(arg_map)

    assert isinstance(result, str)


def test_render_graph_with_claims() -> None:
    """Test rendering a graph with claims."""
    arg_map = ArgumentMap()

    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)

    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)

    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)

    result = render_argdown(arg_map)

    assert "C1" in result
    assert "C2" in result


def test_render_graph_label_only() -> None:
    """Test rendering with label_only=True."""
    arg_map = ArgumentMap()

    prop = Proposition(content="Long proposition")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)

    result = render_argdown(arg_map, label_only=True)

    assert "C1" in result
    # Proposition text should not be included in label-only mode
    assert "Long proposition" not in result


def test_render_graph_with_details() -> None:
    """Test rendering with full details."""
    arg_map = ArgumentMap()

    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)

    result = render_argdown(arg_map, label_only=False)

    assert "C1" in result
    assert "Test claim" in result


def test_render_single_node() -> None:
    """Test rendering a single node."""
    arg_map = ArgumentMap()

    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)

    result = render_argdown_node(arg_map, label="C1", details=True)

    assert "C1" in result
    assert "Test claim" in result


def test_render_node_without_details() -> None:
    """Test rendering a node without details."""
    arg_map = ArgumentMap()

    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)

    result = render_argdown_node(arg_map, label="C1", details=False)

    assert "C1" in result


def test_render_graph_with_relations() -> None:
    """Test rendering includes relations."""
    arg_map = ArgumentMap()

    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg = ArgumentNode(label="A1", gist="Argument")

    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    arg_map.add_support_relation(from_label="A1", to_label="C1")

    result = render_argdown(arg_map)

    # Should show both nodes
    assert "C1" in result
    assert "A1" in result


def _build_sample_map_for_nested() -> ArgumentMap:
    arg_map = ArgumentMap()

    prop_claim = Proposition(content="Claim text")
    prop_p1 = Proposition(content="Premise 1")
    prop_p2 = Proposition(content="Premise 2")
    prop_conc = Proposition(content="Conclusion text")

    for prop in [prop_claim, prop_p1, prop_p2, prop_conc]:
        arg_map.add_proposition(prop)

    claim = ClaimNode(label="C1", proposition_id=prop_claim.id)
    arg = ArgumentNode(
        label="A1",
        gist="Argument gist",
        premises=[prop_p1.id, prop_p2.id],
        conclusion=prop_conc.id,
    )

    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    arg_map.add_support_relation(from_label="A1", to_label="C1")

    return arg_map


def test_render_nested_json_detailed() -> None:
    arg_map = _build_sample_map_for_nested()

    result = render_nested_json(arg_map, detailed=True)

    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1

    claim_record = data[0]
    assert claim_record["type"] == "claim"
    assert claim_record["label"] == "C1"
    assert claim_record["proposition"] == "Claim text"

    supported_by = claim_record["supported_by"]
    assert isinstance(supported_by, list)
    assert len(supported_by) == 1

    arg_record = supported_by[0]
    assert arg_record["type"] == "argument"
    assert arg_record["label"] == "A1"
    assert arg_record["gist"] == "Argument gist"
    # Premises and conclusion are only included when show_pcs=True
    assert "premises" not in arg_record
    assert "conclusion" not in arg_record


def test_render_nested_json_detailed_with_pcs() -> None:
    """Premises and conclusion are included when show_pcs is True."""
    arg_map = _build_sample_map_for_nested()

    result = render_nested_json(arg_map, detailed=True, show_pcs=True)

    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1

    claim_record = data[0]
    supported_by = claim_record["supported_by"]
    assert isinstance(supported_by, list)
    assert len(supported_by) == 1

    arg_record = supported_by[0]
    assert arg_record["premises"] == ["Premise 1", "Premise 2"]
    assert arg_record["conclusion"] == "Conclusion text"


def test_render_nested_json_thin() -> None:
    arg_map = _build_sample_map_for_nested()

    result = render_nested_json(arg_map, detailed=False)
    data = json.loads(result)

    assert isinstance(data, list)
    assert len(data) == 1

    claim_record = data[0]
    # In thin mode, nested records should still include relations for this sample
    assert claim_record["type"] == "claim"
    assert claim_record["label"] == "C1"
    assert "supported_by" in claim_record
    assert isinstance(claim_record["supported_by"], list)
    assert len(claim_record["supported_by"]) == 1

    # attacked_by is optional and only present when non-empty


def test_render_nested_yaml_roundtrip() -> None:
    arg_map = _build_sample_map_for_nested()

    yaml_text = render_nested_yaml(arg_map, detailed=True)

    import yaml as _yaml  # type: ignore[import-untyped]

    data = _yaml.safe_load(yaml_text)
    assert isinstance(data, list)
    assert data[0]["type"] == "claim"
