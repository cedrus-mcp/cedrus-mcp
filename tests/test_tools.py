"""The eight tools, called directly on a Session (§2 and §8 of the plan)."""

import pytest
from fixtures.soft_drugs import soft_drugs_map

from cedrus import tools
from cedrus.model import MapError
from cedrus.result import Session


def loaded() -> Session:
    return Session(amap=soft_drugs_map(), session_id="test")


def first_line(text: str) -> str:
    return text.splitlines()[0]


# ----------------------------------------------------------------------- show


def test_show_renders_the_map_and_marks_it_seen() -> None:
    session = loaded()
    text = tools.show(session, max_chars=24000)
    assert text.startswith("ARGUMENT MAP: Legalisation of Soft Drugs")
    assert session.last_shown == 23


def test_show_on_an_empty_map_says_how_to_start() -> None:
    assert tools.show(Session(), max_chars=24000).startswith("The map is empty.")


def test_show_obeys_the_size_limit() -> None:
    assert "## Part 3" not in tools.show(loaded(), max_chars=3000)


# ------------------------------------------------------------------ add_claim


def test_add_claim_reports_the_new_id() -> None:
    session = Session()
    text = tools.add_claim(session, "Legalisation of Soft Drugs", "Soft drugs should be legal.")
    assert first_line(text) == (
        'OK: Added C1 "Legalisation of Soft Drugs". It is a root claim, so nothing is above it.'
    )
    assert "Map v1: 1 claim, 0 arguments, 0 relations." in text


def test_add_claim_warns_about_a_duplicate_label() -> None:
    session = loaded()
    text = tools.add_claim(session, "Tax revenue", "Another item with the same title.")
    assert 'A19 already has the label "Tax revenue".' in first_line(text)


def test_add_claim_warns_when_it_cuts_a_long_label() -> None:
    session = Session()
    text = tools.add_claim(session, "word " * 40, "Text.")
    assert "The label was cut to 80 characters." in first_line(text)


# --------------------------------------------------------------- add_argument


def test_add_argument_names_the_target_and_the_side() -> None:
    session = loaded()
    text = tools.add_argument(
        session, "a19", "attacks", "Tax evasion", "A legal market would be evaded."
    )
    # Both sides are named: a [con] argument attacking a [pro] one is the pattern the
    # view is built around, and the result is the model's closest look at it.
    assert first_line(text) == (
        'OK: Added A20 "Tax evasion" [con]. It attacks A19 "Tax revenue" [pro] (under A19).'
    )
    assert "Map v24: 1 claim, 18 arguments, 20 relations." in text


def test_add_argument_refuses_an_undercut_aimed_at_a_claim() -> None:
    session = loaded()
    with pytest.raises(MapError) as caught:
        tools.add_argument(session, "C1", "undercuts", "Bad undercut", "Text.")
    message = str(caught.value)
    assert '"undercuts" needs an argument as its target, but C1 is a claim' in message
    assert 'use "attacks"' in message
    assert session.amap.version == 23


def test_add_argument_refuses_an_unknown_target() -> None:
    session = loaded()
    with pytest.raises(MapError, match='"A21" does not exist'):
        tools.add_argument(session, "A21", "supports", "Nowhere", "Text.")


def test_add_argument_refuses_an_unknown_relation() -> None:
    session = loaded()
    with pytest.raises(MapError, match="is not a relation"):
        tools.add_argument(session, "A19", "rebuts", "Label", "Text.")


def test_a_refused_call_leaves_the_map_alone() -> None:
    session = loaded()
    before = session.amap.version
    for call in (
        lambda: tools.add_argument(session, "A21", "supports", "L", "T."),
        lambda: tools.link(session, "A1", "supports", "A1"),
        lambda: tools.unlink(session, "A19", "C1"),
        lambda: tools.delete(session, "A7"),
        lambda: tools.edit(session, "A1"),
    ):
        with pytest.raises(MapError):
            call()
    assert session.amap.version == before


# ----------------------------------------------------------------------- link


def test_link_adds_a_second_target_and_says_where_the_item_sits() -> None:
    session = loaded()
    text = tools.link(session, "A19", "supports", "A11")
    assert first_line(text) == (
        'OK: A19 "Tax revenue" [pro] now supports A11 "Listen to society" [pro]. '
        "It is shown under C1."
    )


def test_link_changes_an_existing_relation() -> None:
    session = loaded()
    text = tools.link(session, "A19", "attacks", "C1")
    assert "where it supports it before." in first_line(text)


def test_link_says_when_there_is_nothing_to_do() -> None:
    session = loaded()
    text = tools.link(session, "A19", "supports", "C1")
    assert "A19 already supports C1, so nothing changed." in first_line(text)
    assert session.amap.version == 23


def test_link_refuses_a_cycle() -> None:
    session = loaded()
    with pytest.raises(MapError, match="circular"):
        tools.link(session, "C1", "supports", "A4")


def test_link_accepts_a_claim_as_the_source() -> None:
    session = loaded()
    tools.add_claim(session, "Harm principle", "Only harm to others justifies a ban.")
    text = tools.link(session, "C2", "supports", "A5")
    assert "It is shown under A5." in first_line(text)


# --------------------------------------------------------------------- unlink


def test_unlink_reports_what_is_left() -> None:
    session = loaded()
    text = tools.unlink(session, "A4", "A3")
    assert first_line(text) == (
        "OK: A4 no longer supports A3. It still responds to A2, A1. It is shown under A2."
    )


def test_unlink_refuses_to_strand_an_argument() -> None:
    session = loaded()
    with pytest.raises(MapError, match="would be left without a target"):
        tools.unlink(session, "A19", "C1")


def test_unlink_needs_a_relation_that_exists() -> None:
    session = loaded()
    with pytest.raises(MapError, match="has no relation to"):
        tools.unlink(session, "A19", "A11")


# ----------------------------------------------------------------------- edit


def test_edit_changes_the_label() -> None:
    session = loaded()
    text = tools.edit(session, "A19", label="Excise duty")
    assert first_line(text) == 'OK: Updated the label of A19 "Excise duty" [pro].'
    assert session.amap.items["A19"].label == "Excise duty"


def test_edit_changes_both_fields() -> None:
    session = loaded()
    text = tools.edit(session, "A19", label="Excise duty", text="New text.")
    assert "Updated the label and the text of" in first_line(text)
    assert session.amap.items["A19"].text == "New text."


def test_edit_with_nothing_given_is_refused() -> None:
    session = loaded()
    with pytest.raises(MapError, match="nothing to change on A19"):
        tools.edit(session, "A19")


def test_edit_keeps_the_relations() -> None:
    session = loaded()
    tools.edit(session, "A4", text="A shorter text.")
    assert len(session.amap.outgoing("A4")) == 3


# --------------------------------------------------------------------- delete


def test_delete_reports_the_id_and_that_it_is_gone_for_good() -> None:
    session = loaded()
    text = tools.delete(session, "A19")
    assert first_line(text) == (
        'OK: Deleted A19 "Tax revenue". Deleted IDs are never given to a new item.'
    )
    assert "A19" in session.amap.deleted_ids


def test_delete_refuses_to_strand_replies_and_names_them() -> None:
    session = loaded()
    with pytest.raises(MapError) as caught:
        tools.delete(session, "A7")
    message = str(caught.value)
    assert "A8, A9, A10 respond only to it" in message
    assert 'delete(id="A7", with_replies=true)' in message


def test_delete_with_replies_names_everything_it_took() -> None:
    session = loaded()
    text = tools.delete(session, "A7", with_replies=True)
    assert 'Deleted A7 "Alcohol and tobacco analogy", and with it A8, A9, A10.' in first_line(text)
    assert "A7" not in session.amap


def test_delete_keeps_a_reply_that_has_another_target() -> None:
    session = loaded()
    tools.delete(session, "A3", with_replies=True)
    assert "A4" in session.amap  # A4 also attacks A2 and supports A1


# ------------------------------------------------------------------ staleness


def test_results_report_how_far_the_map_moved_since_the_last_show() -> None:
    session = loaded()
    tools.show(session, max_chars=24000)
    tools.add_argument(session, "C1", "supports", "One", "Text.")
    text = tools.add_argument(session, "C1", "supports", "Two", "Text.")
    assert "The map changed 2 times since your last show()." in text

    tools.show(session, max_chars=24000)
    text = tools.add_argument(session, "C1", "supports", "Three", "Text.")
    assert "The map changed once since your last show()." in text


def test_the_tool_list_is_the_eight_of_the_plan() -> None:
    assert tools.TOOL_NAMES == (
        "show",
        "add_claim",
        "add_argument",
        "link",
        "unlink",
        "edit",
        "delete",
        "new_map",
    )


def test_new_map_starts_again_from_nothing() -> None:
    session = loaded()
    tools.show(session, max_chars=24000)

    text = tools.new_map(session)
    assert text == "OK: Started a new, empty map.\nMap v0: 0 claims, 0 arguments, 0 relations."
    assert session.last_shown is None

    added = tools.add_claim(session, "Fresh", "A new statement.")
    assert first_line(added).startswith('OK: Added C1 "Fresh".')
