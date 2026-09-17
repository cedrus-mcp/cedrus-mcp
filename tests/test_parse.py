"""Loose input, strict meaning (§2 of the plan)."""

import pytest
from fixtures.soft_drugs import soft_drugs_map

from cedrus.model import ArgMap, MapError
from cedrus.parse import (
    clean_label,
    clean_text,
    did_you_mean,
    duplicate_label_warning,
    resolve_id,
    resolve_relation,
)
from cedrus.result import Session, error, ok

# ------------------------------------------------------------------------ IDs


@pytest.mark.parametrize(
    "written",
    ["A7", "a7", " A7 ", "[A7]", "(a7)", '"A7"', "**A7**", "A-7", "A_7", "A 7", "A07", "A7."],
)
def test_ids_are_matched_loosely(written: str) -> None:
    assert resolve_id(soft_drugs_map(), written) == "A7"


def test_an_id_with_its_label_attached_still_resolves() -> None:
    m = soft_drugs_map()
    assert resolve_id(m, "A7 Alcohol and tobacco analogy") == "A7"
    assert resolve_id(m, "C1 Legalisation of Soft Drugs") == "C1"


def test_a_pasted_label_resolves_to_its_id() -> None:
    m = soft_drugs_map()
    assert resolve_id(m, "Alcohol and tobacco analogy") == "A7"
    assert resolve_id(m, "alcohol and TOBACCO analogy") == "A7"


def test_an_unknown_id_names_the_nearest_real_ones() -> None:
    with pytest.raises(MapError) as caught:
        resolve_id(soft_drugs_map(), "A21")
    message = str(caught.value)
    assert message.startswith('"A21" does not exist.')
    assert "Did you mean" in message
    for suggested in ("A2", "A12", "A1"):
        if f"{suggested} " in message:
            break
    else:  # pragma: no cover - the suggestion list is never empty here
        pytest.fail(f"no plausible suggestion in {message!r}")


def test_a_deleted_id_is_reported_as_gone() -> None:
    with pytest.raises(MapError, match='"A17" does not exist'):
        resolve_id(soft_drugs_map(), "A17")


def test_an_empty_id_says_what_is_expected() -> None:
    with pytest.raises(MapError, match="is empty"):
        resolve_id(soft_drugs_map(), "  ")


def test_an_empty_map_points_at_add_claim() -> None:
    with pytest.raises(MapError, match="Start with add_claim"):
        resolve_id(ArgMap(), "C1")


def test_an_unknown_claim_id_is_answered_with_claims() -> None:
    m = soft_drugs_map()
    m.add_claim("Harm principle", "Only harm to others justifies a ban.")
    assert did_you_mean(m, "C3") == (
        ' Did you mean C1 "Legalisation of Soft Drugs" or C2 "Harm principle"?'
    )


def test_suggestions_fall_back_to_listing_a_small_map() -> None:
    m = ArgMap()
    m.add_claim("Root", "Text.")
    m.add_argument("C1", "supports", "For", "Text.")
    assert did_you_mean(m, "zzzzzzzz") == " The map has: C1, A1."


def test_suggestions_do_not_list_a_large_map() -> None:
    sentence = did_you_mean(soft_drugs_map(), "qqqqqqqqqqqq")
    assert "Call show() to see them all." in sentence


# ------------------------------------------------------------------ relations


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("supports", "supports"),
        ("support", "supports"),
        ("SUPPORTS", "supports"),
        (" Support ", "supports"),
        ("attacks", "attacks"),
        ("attack", "attacks"),
        ("Undercut", "undercuts"),
        ("undercuts.", "undercuts"),
    ],
)
def test_relations_are_matched_loosely(written: str, expected: str) -> None:
    assert resolve_relation(written) == expected


def test_an_unknown_relation_lists_the_three_valid_ones() -> None:
    with pytest.raises(MapError) as caught:
        resolve_relation("rebuts")
    message = str(caught.value)
    assert '"rebuts" is not a relation' in message
    assert '"supports", "attacks", "undercuts"' in message


# ------------------------------------------------------------ labels and texts


def test_a_long_label_is_cut_and_the_cut_is_reported() -> None:
    label, warning = clean_label("word " * 40)
    assert len(label) <= 80
    assert warning == "The label was cut to 80 characters."


def test_a_short_label_passes_without_a_warning() -> None:
    assert clean_label("  Tax   revenue\n") == ("Tax revenue", "")


def test_an_empty_label_is_refused() -> None:
    with pytest.raises(MapError, match="label is empty"):
        clean_label("   ")


def test_a_duplicate_label_only_warns() -> None:
    m = soft_drugs_map()
    assert duplicate_label_warning(m, "Tax revenue") == 'A19 already has the label "Tax revenue".'
    assert duplicate_label_warning(m, "Tax revenue", ignore="A19") == ""
    assert duplicate_label_warning(m, "Something new") == ""


def test_an_over_long_text_says_how_long_it_is() -> None:
    with pytest.raises(MapError, match="3001 characters long; the limit is 3000"):
        clean_text("x" * 3001)


def test_an_empty_text_is_refused() -> None:
    with pytest.raises(MapError, match="text is empty"):
        clean_text("\n\n")


# -------------------------------------------------------------------- results


def test_a_result_gives_the_version_and_the_counts() -> None:
    session = Session(amap=soft_drugs_map())
    text = ok('Added A20 "Tax evasion" [con]. It attacks A19 "Tax revenue" (under A19).', session)
    assert text == (
        'OK: Added A20 "Tax evasion" [con]. It attacks A19 "Tax revenue" (under A19).\n'
        "Map v23: 1 claim, 17 arguments, 19 relations."
    )


def test_staleness_appears_only_after_a_show() -> None:
    session = Session(amap=soft_drugs_map())
    assert "since your last show()" not in ok("Done.", session)

    session.mark_shown()
    assert "since your last show()" not in ok("Done.", session)

    session.amap.add_argument("C1", "supports", "One", "Text.")
    assert "The map changed once since your last show()." in ok("Done.", session)

    session.amap.add_argument("C1", "supports", "Two", "Text.")
    assert "The map changed 2 times since your last show()." in ok("Done.", session)


def test_notes_ride_on_the_first_line() -> None:
    session = Session(amap=soft_drugs_map())
    first = ok("Added A20.", session, notes="The label was cut to 80 characters.").splitlines()[0]
    assert first == "OK: Added A20. The label was cut to 80 characters."


def test_hints_are_off_unless_asked_for() -> None:
    session = Session(amap=soft_drugs_map())
    assert "Hint:" not in ok("Added A20.", session, hint="A20 has no replies yet.")

    session.hints = True
    assert ok("Added A20.", session, hint="A20 has no replies yet.").endswith(
        "\nHint: A20 has no replies yet."
    )


def test_an_error_says_that_nothing_changed() -> None:
    session = Session(amap=soft_drugs_map())
    assert error('"A21" does not exist.', session) == (
        '"A21" does not exist.\nNothing was changed (map v23).'
    )


def test_an_error_adds_no_marker_of_its_own() -> None:
    # The SDK prefixes every ToolError with "Error executing tool <name>: ".
    assert not error("Nope.", Session(amap=soft_drugs_map())).startswith("ERROR")
