"""Unit tests for node models."""

from cedrus.backend.models import ArgumentNode, ClaimNode, Proposition


def test_create_claim_node() -> None:
    """Test creating a claim node."""
    prop = Proposition(content="Test claim")
    claim = ClaimNode(label="C1", proposition_id=prop.id)

    assert claim.label == "C1"
    assert claim.proposition_id == prop.id


def test_create_argument_node() -> None:
    """Test creating an argument node."""
    arg = ArgumentNode(label="A1", gist="Test argument")

    assert arg.label == "A1"
    assert arg.gist == "Test argument"


def test_argument_with_premises() -> None:
    """Test creating an argument with premises."""
    prop1 = Proposition(content="Premise 1")
    prop2 = Proposition(content="Premise 2")

    arg = ArgumentNode(label="A1", gist="Test", premises=[prop1.id, prop2.id])

    assert len(arg.premises) == 2
    assert arg.premises[0] == prop1.id


def test_argument_with_conclusion() -> None:
    """Test creating an argument with conclusion."""
    prop = Proposition(content="Conclusion")

    arg = ArgumentNode(label="A1", gist="Test", conclusion=prop.id)

    assert arg.conclusion == prop.id


def test_claim_with_tags() -> None:
    """Test creating a claim with tags."""
    prop = Proposition(content="Test")
    claim = ClaimNode(label="C1", proposition_id=prop.id, tags=["important", "verified"])

    assert "important" in claim.tags
    assert "verified" in claim.tags


def test_claim_with_metadata() -> None:
    """Test creating a claim with metadata."""
    prop = Proposition(content="Test")
    claim = ClaimNode(
        label="C1", proposition_id=prop.id, metadata={"source": "paper.pdf", "page": "5"}
    )

    assert claim.metadata["source"] == "paper.pdf"
    assert claim.metadata["page"] == "5"


def test_node_equality() -> None:
    """Test node equality based on all fields."""
    prop1 = Proposition(content="Test 1")
    prop2 = Proposition(content="Test 2")

    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C1", proposition_id=prop2.id)
    claim3 = ClaimNode(label="C2", proposition_id=prop1.id)

    # Different proposition IDs = not equal
    assert claim1 != claim2
    # Different labels = not equal
    assert claim1 != claim3
