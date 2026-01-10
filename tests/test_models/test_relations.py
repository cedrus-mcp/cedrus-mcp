"""Unit tests for relation models."""

from cedrus.backend.models import DialecticalRelation


def test_create_support_relation() -> None:
    """Test creating a support relation."""
    rel = DialecticalRelation(_type="support")

    assert rel.relation_type == "support"


def test_create_attack_relation() -> None:
    """Test creating an attack relation."""
    rel = DialecticalRelation(_type="attack")

    assert rel.relation_type == "attack"


def test_relation_with_premise_index() -> None:
    """Test creating relation with target premise index."""
    rel = DialecticalRelation(_type="attack", target_premise_idx=2)

    assert rel.target_premise_idx == 2


def test_relation_with_metadata() -> None:
    """Test creating relation with metadata."""
    rel = DialecticalRelation(_type="support", metadata={"source": "paper.pdf"})

    assert rel.metadata["source"] == "paper.pdf"


def test_relation_with_review_flag() -> None:
    """Test creating relation with review flag."""
    rel = DialecticalRelation(_type="support", needs_review_flag=True)

    assert rel.needs_review_flag
