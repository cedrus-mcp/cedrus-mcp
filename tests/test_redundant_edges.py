import pytest
from cedrus.graph.argument_map import ArgumentMap
from cedrus.models.nodes import ArgumentNode, ClaimNode
import networkx as nx

@pytest.fixture
def argument_map():
    # Create a fixture for the ArgumentMap instance
    arg_map = ArgumentMap()
    arg_map.argument_graph = nx.DiGraph()
    return arg_map

def test_redundant_edges_support_case(argument_map):
    # Add nodes using ArgumentMap methods
    argument_map.add_argument(ArgumentNode(label="A"))
    argument_map.add_argument(ArgumentNode(label="B"))
    argument_map.add_claim(ClaimNode(label="C", proposition_id=""))

    # Add edges
    argument_map.argument_graph.add_edge("A", "B", _type="support")
    argument_map.argument_graph.add_edge("A", "C", _type="support")
    argument_map.argument_graph.add_edge("C", "B", _type="support")

    # Check redundant edges
    redundant = argument_map.redundant_edges()
    assert ("A", "B") in redundant

def test_redundant_edges_attack_case(argument_map):
    # Add nodes using ArgumentMap methods
    argument_map.add_argument(ArgumentNode(label="A"))
    argument_map.add_argument(ArgumentNode(label="B"))
    argument_map.add_claim(ClaimNode(label="C", proposition_id=""))

    # Add edges
    argument_map.argument_graph.add_edge("A", "B", _type="attack")
    argument_map.argument_graph.add_edge("A", "C", _type="attack")
    argument_map.argument_graph.add_edge("C", "B", _type="support")

    # Check redundant edges
    redundant = argument_map.redundant_edges()
    assert ("A", "B") in redundant

def test_no_redundant_edges(argument_map):
    # Add nodes using ArgumentMap methods
    argument_map.add_argument(ArgumentNode(label="A"))
    argument_map.add_argument(ArgumentNode(label="B"))
    argument_map.add_claim(ClaimNode(label="C", proposition_id=""))

    # Add edges
    argument_map.argument_graph.add_edge("A", "B", _type="support")
    argument_map.argument_graph.add_edge("A", "C", _type="attack")

    # Check redundant edges
    redundant = argument_map.redundant_edges()
    assert len(redundant) == 0

def test_invalid_edge_types(argument_map):
    # Add nodes using ArgumentMap methods
    argument_map.add_argument(ArgumentNode(label="A"))
    argument_map.add_argument(ArgumentNode(label="B"))
    argument_map.add_claim(ClaimNode(label="C", proposition_id=""))

    # Add edges with invalid types
    argument_map.argument_graph.add_edge("A", "B", _type="invalid")
    argument_map.argument_graph.add_edge("A", "C", _type="support")
    argument_map.argument_graph.add_edge("C", "B", _type="support")

    # Check redundant edges
    redundant = argument_map.redundant_edges()
    assert len(redundant) == 0