"""Unit tests for graph persistence (save/load)."""

from pathlib import Path
from koala.graph.argument_map import ArgumentMap
from koala.graph.persistence import save_graph, load_graph
from koala.models import ClaimNode, ArgumentNode, Proposition


def test_save_empty_graph(temp_data_file: Path) -> None:
    """Test saving an empty graph."""
    arg_map = ArgumentMap()
    
    save_graph(arg_map, temp_data_file)
    
    # Note: save_graph is currently a stub, so file won't exist
    # This test documents current behavior
    assert not temp_data_file.exists()


def test_load_empty_graph(temp_data_file: Path) -> None:
    """Test loading returns empty graph when file doesn't exist."""
    # load_graph is a stub that always returns empty ArgumentMap
    loaded = load_graph(temp_data_file)
    
    assert len(loaded.argument_graph.nodes) == 0


def test_save_and_load_with_claims(temp_data_file: Path) -> None:
    """Test that save/load are stubs (not implemented yet)."""
    arg_map = ArgumentMap()
    
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)
    
    save_graph(arg_map, temp_data_file)
    loaded = load_graph(temp_data_file)
    
    # load_graph is a stub, returns empty graph
    assert len(loaded.argument_graph.nodes) == 0


def test_save_and_load_with_arguments(temp_data_file: Path) -> None:
    """Test that save/load are stubs (not implemented yet)."""
    arg_map = ArgumentMap()
    
    prop1 = Proposition(content="Premise 1")
    prop2 = Proposition(content="Conclusion")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    arg = ArgumentNode(
        label="A1",
        gist="Test argument",
        premises=[prop1.id],
        conclusion=prop2.id
    )
    
    arg_map.add_argument(arg)
    
    save_graph(arg_map, temp_data_file)
    loaded = load_graph(temp_data_file)
    
    # load_graph is a stub, returns empty graph
    assert len(loaded.argument_graph.nodes) == 0


def test_save_and_load_with_relations(temp_data_file: Path) -> None:
    """Test that save/load are stubs (not implemented yet)."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    
    save_graph(arg_map, temp_data_file)
    loaded = load_graph(temp_data_file)
    
    # load_graph is a stub, returns empty graph
    rel = loaded.get_dialectic_relation("A1", "C1")
    assert rel is None


def test_load_nonexistent_file() -> None:
    """Test loading a non-existent file returns empty graph (stub behavior)."""
    # load_graph is a stub that doesn't check if file exists
    loaded = load_graph(Path("/nonexistent/file.json"))
    assert len(loaded.argument_graph.nodes) == 0
