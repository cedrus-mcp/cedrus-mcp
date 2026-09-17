"""Roots, places, depths, sides and challenge status (§1 of the plan)."""

from cedrus.derive import derive
from cedrus.model import ArgMap


def small() -> ArgMap:
    """C1 ← A1 (supports) ← A2 (attacks); C1 ← A3 (attacks)."""
    m = ArgMap()
    m.add_claim("Root", "Soft drugs should be legal.")
    m.add_argument("C1", "supports", "For", "A reason for.")
    m.add_argument("A1", "attacks", "Against the reason", "Text.")
    m.add_argument("C1", "attacks", "Against", "A reason against.")
    return m


def test_empty_map_derives_nothing() -> None:
    d = derive(ArgMap())
    assert d.roots == []
    assert d.order == []
    assert d.sides_on is False


def test_roots_are_claims_without_targets() -> None:
    d = derive(small())
    assert d.roots == ["C1"]


def test_outline_order_is_depth_first_over_children() -> None:
    d = derive(small())
    assert d.order == ["C1", "A1", "A2", "A3"]
    assert d.depth == {"C1": 0, "A1": 1, "A2": 2, "A3": 1}


def test_primary_target_is_the_oldest_relation() -> None:
    m = small()
    m.link("A2", "attacks", "C1")
    d = derive(m)
    assert d.primary["A2"] == "A1"
    assert [r.target for r in d.extra["A2"]] == ["C1"]
    assert d.order == ["C1", "A1", "A2", "A3"]


def test_unlinking_the_primary_target_moves_the_item() -> None:
    m = small()
    m.link("A2", "attacks", "C1")
    m.unlink("A2", "A1")
    d = derive(m)
    assert d.primary["A2"] == "C1"
    assert d.depth["A2"] == 1


# ---------------------------------------------------------------------- sides


def test_sides_follow_supports_and_flip_on_attacks() -> None:
    d = derive(small())
    assert d.sides_on is True
    assert d.sides == {"C1": "pro", "A1": "pro", "A2": "con", "A3": "con"}


def test_undercuts_flips_like_attacks() -> None:
    m = small()
    m.add_argument("A1", "undercuts", "Bad step", "Text.")
    d = derive(m)
    assert d.sides["A4"] == "con"


def test_a_con_argument_can_support_another_con_argument() -> None:
    m = small()
    m.add_argument("A3", "supports", "Backing", "Text.")
    d = derive(m)
    assert d.sides["A3"] == "con"
    assert d.sides["A4"] == "con"


def test_sides_are_off_with_two_root_claims() -> None:
    m = small()
    m.add_claim("Another root", "Text.")
    d = derive(m)
    assert d.roots == ["C1", "C2"]
    assert d.sides_on is False
    assert d.side("A1") is None
    assert d.tag("A1") == ""


def test_conflicting_targets_make_an_item_mixed() -> None:
    m = small()
    m.link("A2", "attacks", "A3")  # attacks a pro argument and a con one
    d = derive(m)
    assert d.sides["A2"] == "mixed"
    assert d.mixed == ["A2"]


def test_mixed_spreads_to_whatever_responds_to_it() -> None:
    m = small()
    m.link("A2", "attacks", "A3")
    m.add_argument("A2", "supports", "Backing the mixed one", "Text.")
    d = derive(m)
    assert d.sides["A4"] == "mixed"


# ----------------------------------------------------------- non-root claims


def test_a_non_root_claim_sits_under_its_primary_target() -> None:
    m = small()
    m.add_claim("Principle", "A principle several arguments rely on.")
    m.link("C2", "supports", "A1")
    d = derive(m)
    assert d.roots == ["C1"]
    assert d.sides_on is True
    assert d.primary["C2"] == "A1"
    assert d.depth["C2"] == 2
    assert d.sides["C2"] == "pro"
    assert d.order == ["C1", "A1", "A2", "C2", "A3"]


# --------------------------------------------------------------- unchallenged


def test_unchallenged_lists_items_with_nothing_pointing_at_them() -> None:
    d = derive(small())
    assert d.unchallenged == ["A2", "A3"]


def test_root_claims_are_never_called_unchallenged() -> None:
    m = ArgMap()
    m.add_claim("Lonely", "Nothing responds to it.")
    d = derive(m)
    assert d.unchallenged == []
    assert d.order == ["C1"]
