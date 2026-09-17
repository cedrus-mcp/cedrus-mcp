"""The rules of §1 of the plan, and every refusal."""

import pytest

from cedrus.model import ArgMap, MapError


def tiny() -> ArgMap:
    """C1 with one supporting and one attacking argument."""
    m = ArgMap()
    m.add_claim("Root", "Soft drugs should be legal.")
    m.add_argument("C1", "supports", "For", "A reason for.")
    m.add_argument("C1", "attacks", "Against", "A reason against.")
    return m


# ------------------------------------------------------------------- creation


def test_ids_count_up_per_kind() -> None:
    m = tiny()
    m.add_claim("Principle", "A principle.")
    assert [i.id for i in m.items.values()] == ["C1", "A1", "A2", "C2"]


def test_version_counts_changes() -> None:
    m = ArgMap()
    assert m.version == 0
    m.add_claim("Root", "Text.")
    assert m.version == 1
    m.add_argument("C1", "supports", "For", "Text.")
    assert m.version == 2


def test_add_argument_creates_its_relation() -> None:
    m = tiny()
    assert [(r.source, r.type, r.target) for r in m.relations] == [
        ("A1", "supports", "C1"),
        ("A2", "attacks", "C1"),
    ]


def test_add_argument_needs_an_existing_target() -> None:
    m = tiny()
    with pytest.raises(MapError, match="does not exist"):
        m.add_argument("C9", "supports", "Nowhere", "Text.")
    assert m.version == 3


def test_labels_and_texts_are_checked() -> None:
    m = ArgMap()
    with pytest.raises(MapError, match="label is empty"):
        m.add_claim("   ", "Text.")
    with pytest.raises(MapError, match="text is empty"):
        m.add_claim("Root", "  ")
    with pytest.raises(MapError, match="longer than 80"):
        m.add_claim("x" * 81, "Text.")
    with pytest.raises(MapError, match="longer than 3000"):
        m.add_claim("Root", "x" * 3001)
    assert m.version == 0


def test_label_whitespace_is_collapsed_to_one_line() -> None:
    m = ArgMap()
    item = m.add_claim("Two\n  words", "Text.")
    assert item.label == "Two words"


# -------------------------------------------------------------------- linking


def test_link_adds_a_second_target() -> None:
    m = tiny()
    result = m.link("A2", "supports", "A1")
    relation = result.relation
    assert (relation.source, relation.type, relation.target) == ("A2", "supports", "A1")
    assert result.status == "added"
    assert result.previous is None
    assert len(m.outgoing("A2")) == 2


def test_link_changes_the_type_of_an_existing_relation() -> None:
    m = tiny()
    before = m.version
    result = m.link("A1", "attacks", "C1")
    assert result.status == "retyped"
    assert result.previous == "supports"
    assert result.relation.type == "attacks"
    assert len(m.outgoing("A1")) == 1
    assert m.version == before + 1


def test_repeating_an_identical_link_changes_nothing() -> None:
    m = tiny()
    before = m.version
    result = m.link("A1", "supports", "C1")
    assert result.status == "unchanged"
    assert m.version == before
    assert len(m.relations) == 2
    assert result.relation.type == "supports"


def test_a_claim_may_support_an_argument() -> None:
    m = tiny()
    m.add_claim("Principle", "A principle several arguments rely on.")
    m.link("C2", "supports", "A1")
    assert [r.target for r in m.outgoing("C2")] == ["A1"]


def test_self_link_is_refused() -> None:
    m = tiny()
    with pytest.raises(MapError, match="cannot relate to itself"):
        m.link("A1", "supports", "A1")


def test_cycles_are_refused() -> None:
    m = tiny()
    m.add_argument("A1", "supports", "Deeper", "Text.")
    with pytest.raises(MapError, match="circular"):
        m.link("C1", "supports", "A3")
    with pytest.raises(MapError, match="circular"):
        m.link("A1", "supports", "A3")


def test_undercut_needs_an_argument_as_target() -> None:
    m = tiny()
    with pytest.raises(MapError, match='"undercuts" needs an argument'):
        m.add_argument("C1", "undercuts", "Bad undercut", "Text.")
    with pytest.raises(MapError, match='use "attacks"'):
        m.link("A1", "undercuts", "C1")
    m.link("A1", "undercuts", "A2")  # an argument target is fine


# ------------------------------------------------------------------ unlinking


def test_unlink_removes_a_relation() -> None:
    m = tiny()
    m.link("A2", "supports", "A1")
    m.unlink("A2", "C1")
    assert [r.target for r in m.outgoing("A2")] == ["A1"]


def test_unlink_refuses_to_strand_an_argument() -> None:
    m = tiny()
    with pytest.raises(MapError, match="without a target"):
        m.unlink("A1", "C1")


def test_a_claim_may_lose_all_its_relations() -> None:
    m = tiny()
    m.add_claim("Principle", "Text.")
    m.link("C2", "supports", "A1")
    m.unlink("C2", "A1")
    assert m.outgoing("C2") == []


def test_unlink_needs_an_existing_relation() -> None:
    m = tiny()
    with pytest.raises(MapError, match="no relation to"):
        m.unlink("A1", "A2")


# ---------------------------------------------------------------------- edits


def test_edit_keeps_id_and_relations() -> None:
    m = tiny()
    m.edit("A1", label="Renamed")
    assert m.items["A1"].label == "Renamed"
    assert m.items["A1"].text == "A reason for."
    assert [r.target for r in m.outgoing("A1")] == ["C1"]


def test_edit_with_nothing_to_change_is_refused() -> None:
    m = tiny()
    with pytest.raises(MapError, match="nothing to change"):
        m.edit("A1")


# ------------------------------------------------------------------ deletions


def test_delete_removes_the_item_and_its_relations() -> None:
    m = tiny()
    assert m.delete("A1") == ["A1"]
    assert "A1" not in m
    assert [r.source for r in m.relations] == ["A2"]
    assert m.deleted_ids == ["A1"]


def test_deleted_ids_are_never_reused() -> None:
    m = tiny()
    m.delete("A2")
    new = m.add_argument("C1", "attacks", "Replacement", "Text.")
    assert new.id == "A3"


def test_delete_refuses_to_strand_replies() -> None:
    m = tiny()
    m.add_argument("A1", "supports", "Deeper", "Text.")
    with pytest.raises(MapError, match="with_replies=true"):
        m.delete("A1")
    assert "A1" in m


def test_delete_with_replies_cascades() -> None:
    m = tiny()
    m.add_argument("A1", "supports", "Deeper", "Text.")
    m.add_argument("A3", "supports", "Deeper still", "Text.")
    assert m.delete("A1", with_replies=True) == ["A1", "A3", "A4"]
    assert set(m.items) == {"C1", "A2"}


def test_a_reply_with_another_target_survives() -> None:
    m = tiny()
    m.add_argument("A1", "supports", "Deeper", "Text.")
    m.link("A3", "supports", "A2")
    m.delete("A1")
    assert "A3" in m
    assert [r.target for r in m.outgoing("A3")] == ["A2"]


def test_deleting_a_claim_leaves_non_root_claims_alone() -> None:
    m = tiny()
    m.add_claim("Principle", "Text.")
    m.link("C2", "supports", "A1")
    m.delete("A1", with_replies=True)
    assert "C2" in m
    assert m.outgoing("C2") == []
