"""Unit tests for proposition models."""

import pytest

from cedrus.backend.models import Proposition


def test_create_proposition() -> None:
    """Test creating a proposition."""
    prop = Proposition(content="This is a proposition")

    assert prop.content == "This is a proposition"


def test_proposition_equality() -> None:
    """Test proposition equality."""
    prop1 = Proposition(content="Same text")
    prop2 = Proposition(content="Same text")
    prop3 = Proposition(content="Different text")

    # Propositions are equal if IDs match (which they won't in different instances)
    assert prop1 != prop2  # Different IDs
    assert prop1 != prop3


def test_proposition_empty_text() -> None:
    """Test creating proposition with empty text."""
    prop = Proposition(content="")

    assert prop.content == ""


def test_proposition_str_representation() -> None:
    """Test string representation of proposition."""
    prop = Proposition(content="Test proposition")

    # String representation includes the content
    assert "Test proposition" in str(prop)
