"""Unit tests for ArgumentMap operations."""

import pytest
from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import ClaimNode, ArgumentNode, Proposition


def test_create_empty_argument_map() -> None:
    """Test creating an empty ArgumentMap."""
    arg_map = ArgumentMap()
    assert len(arg_map.argument_graph.nodes) == 0


def test_add_claim_node() -> None:
    """Test adding a claim node."""
    arg_map = ArgumentMap()
    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    
    arg_map.add_claim(claim)
    
    assert len(arg_map.argument_graph.nodes) == 1
    assert arg_map.get_node("C1") is not None


def test_add_argument_node() -> None:
    """Test adding an argument node."""
    arg_map = ArgumentMap()
    prop1 = Proposition(content="P1")
    prop2 = Proposition(content="C")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    arg = ArgumentNode(
        label="A1",
        gist="Test argument",
        premises=[prop1.id],
        conclusion=prop2.id
    )
    
    arg_map.add_argument(arg)
    
    assert len(arg_map.argument_graph.nodes) == 1
    assert arg_map.get_node("A1") is not None


def test_get_nonexistent_node() -> None:
    """Test getting a non-existent node raises KeyError."""
    arg_map = ArgumentMap()
    with pytest.raises(KeyError):
        arg_map.get_node("NONEXISTENT")


def test_add_support_relation() -> None:
    """Test adding a support relation."""
    arg_map = ArgumentMap()
    
    # Add nodes
    prop1 = Proposition(content="Claim")
    arg_map.add_proposition(prop1)
    claim = ClaimNode(label="C1", proposition_id=prop1.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    
    # Add relation
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "support"


def test_add_attack_relation() -> None:
    """Test adding an attack relation."""
    arg_map = ArgumentMap()
    
    # Add nodes
    prop1 = Proposition(content="Claim")
    arg_map.add_proposition(prop1)
    claim = ClaimNode(label="C1", proposition_id=prop1.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    
    # Add relation
    arg_map.add_attack_relation(from_label="A1", to_label="C1")
    
    rel = arg_map.get_dialectic_relation("A1", "C1")
    assert rel is not None
    assert rel.relation_type == "attack"


def test_list_claims() -> None:
    """Test listing all claims."""
    arg_map = ArgumentMap()
    
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)
    arg_map.add_argument(arg)
    
    claims = arg_map.list_claims()
    assert len(claims) == 2


def test_list_arguments() -> None:
    """Test listing all arguments."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg1 = ArgumentNode(label="A1", gist="Argument 1")
    arg2 = ArgumentNode(label="A2", gist="Argument 2")
    
    arg_map.add_claim(claim)
    arg_map.add_argument(arg1)
    arg_map.add_argument(arg2)
    
    args = arg_map.list_arguments()
    assert len(args) == 2


def test_list_roots() -> None:
    """Test listing root nodes (no incoming edges)."""
    arg_map = ArgumentMap()
    
    # Create a simple chain: A1 -> C1 -> C2
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)
    arg_map.add_argument(arg)
    
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    
    roots = arg_map.list_roots()
    # C2 should be the only leaf (out_degree == 0)
    assert len(roots) == 1
    assert "C2" in roots


def test_delete_node() -> None:
    """Test deleting a node."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    assert arg_map.get_node("C1") is not None
    
    arg_map.delete_node("C1")
    
    # After deletion, node should not exist
    with pytest.raises(KeyError):
        arg_map.get_node("C1")


def test_delete_relation() -> None:
    """Test deleting a relation."""
    arg_map = ArgumentMap()
    
    # Add nodes and relation
    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    
    assert arg_map.get_dialectic_relation("A1", "C1") is not None
    
    arg_map.delete_relation("A1", "C1")
    
    assert arg_map.get_dialectic_relation("A1", "C1") is None


def test_redundant_edges_with_subset() -> None:
    """Test redundant_edges with a subset of nodes."""
    arg_map = ArgumentMap()

    # Add propositions
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    prop3 = Proposition(content="Claim 3")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    arg_map.add_proposition(prop3)

    # Add claim nodes
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)

    # Add argument nodes
    arg1 = ArgumentNode(label="A1", gist="Argument 1", premises=[prop1.id], conclusion=prop2.id)
    arg2 = ArgumentNode(label="A2", gist="Argument 2", premises=[prop2.id], conclusion=prop3.id)
    arg_map.add_argument(arg1)
    arg_map.add_argument(arg2)

    # Add relations
    arg_map.add_support_relation("A1", "A2")
    arg_map.add_support_relation("A1", "C1")
    arg_map.add_support_relation("C1", "A2")

    # Test redundant edges with a subset
    subset = ["A1", "C1", "A2"]
    redundant = arg_map.redundant_edges(subset=subset)
    assert ("A1", "A2") in redundant

    subset = ["A1", "A2"]
    redundant = arg_map.redundant_edges(subset=subset)
    assert ("A1", "A2") not in redundant

def test_most_similar_label() -> None:
    """Test finding the most similar label."""
    arg_map = ArgumentMap()
    
    # Add nodes
    claim = ClaimNode(label="ClimateChange", proposition_id="P1")
    arg = ArgumentNode(label="GlobalWarming", gist="Argument")
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    
    similar_label, _ = next(arg_map.most_similar_labels("ClimateChnge"))
    assert similar_label == "ClimateChange"
    
    similar_label, _ = next(arg_map.most_similar_labels("GlobaWarming"))
    assert similar_label == "GlobalWarming"
    
