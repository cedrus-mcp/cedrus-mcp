"""What `show()` prints (§3 of the plan)."""

from pathlib import Path

from fixtures.soft_drugs import soft_drugs_map

from cedrus.model import ArgMap
from cedrus.render import EMPTY_MAP, render

GOLDEN = Path(__file__).parent / "golden" / "soft_drugs.txt"


def test_soft_drugs_matches_the_golden_file() -> None:
    assert render(soft_drugs_map()) == GOLDEN.read_text(encoding="utf-8")


def test_empty_map_says_how_to_start() -> None:
    assert render(ArgMap()) == EMPTY_MAP


# --------------------------------------------------------------------- header


def test_header_counts_and_version() -> None:
    text = render(soft_drugs_map())
    assert text.startswith("ARGUMENT MAP: Legalisation of Soft Drugs\n")
    assert "Map v23. 1 claim, 17 arguments, 19 relations." in text


def test_header_counts_root_claims_separately() -> None:
    m = soft_drugs_map()
    m.add_claim("Principle", "A principle several arguments rely on.")
    m.link("C2", "supports", "A5")
    assert "2 claims (1 root), 17 arguments, 20 relations." in render(m)


def test_two_roots_turn_sides_off_and_say_why() -> None:
    m = soft_drugs_map()
    m.add_claim("A second debate", "Something else entirely.")
    text = render(m)
    assert "ARGUMENT MAP: 2 root claims" in text
    assert "No [pro]/[con] tags are shown: the map has 2 root claims" in text
    assert "[con]" not in text.split("## Outline")[1]


def test_deleted_ids_are_listed() -> None:
    assert "Deleted IDs (not reused):\n  A17, A18" in render(soft_drugs_map())


def test_multi_target_items_get_their_own_note() -> None:
    text = render(soft_drugs_map())
    assert "Items with more than one target" in text
    assert "  A4 also attacks A2, supports A1" in text


def test_a_map_without_multi_target_items_has_no_such_note() -> None:
    m = ArgMap()
    m.add_claim("Root", "Text.")
    m.add_argument("C1", "supports", "For", "Text.")
    assert "more than one target" not in render(m)


def test_mixed_items_are_flagged() -> None:
    m = ArgMap()
    m.add_claim("Root", "Text.")
    m.add_argument("C1", "supports", "For", "Text.")
    m.add_argument("C1", "attacks", "Against", "Text.")
    m.add_argument("A1", "attacks", "Two-faced", "Text.")
    m.link("A3", "attacks", "A2")
    text = render(m)
    assert "Mixed items (their targets are on both sides" in text
    assert "  A3" in text
    assert "A3 Two-faced [mixed]" in text


# -------------------------------------------------------------- non-root claim


def test_a_principle_claim_can_underpin_several_arguments() -> None:
    m = soft_drugs_map()
    m.add_claim("Harm principle", "The law may only restrict conduct that harms others.")
    m.link("C2", "supports", "A5")
    m.link("C2", "supports", "A11")
    text = render(m)

    # It is placed once, under the first argument it was linked to.
    assert "    - C2 Harm principle [pro] — supports A5 (also supports A11)" in text
    assert text.count("- C2 Harm principle") == 1
    assert "  C2 also supports A11" in text

    assert "C2 Harm principle [pro]:" in text
    assert "C2 Harm principle [pro] | depth 2 | under A5" in text

    # C1 is still the only root, so the sides stay on.
    assert "2 claims (1 root), 17 arguments, 21 relations." in text
    assert "No [pro]/[con] tags are shown" not in text


# ----------------------------------------------------------------- size limits


def _sections(text: str) -> set[str]:
    return {line for line in text.splitlines() if line.startswith("## ")}


def test_full_output_fits_the_default_limit() -> None:
    text = render(soft_drugs_map())
    assert len(text) < 24000
    assert "## Part 3" in text


def test_first_step_drops_part_3() -> None:
    m = soft_drugs_map()
    full = render(m, max_chars=None)
    text = render(m, max_chars=len(full) - 1)
    assert "## Part 3" not in text
    assert "## Part 2" in text
    assert "Part 3 omitted (map too large); the outline shows every relation." in text


def test_second_step_shortens_part_2() -> None:
    m = soft_drugs_map()
    step_one = render(m, max_chars=len(render(m, max_chars=None)) - 1)
    text = render(m, max_chars=len(step_one) - 1)
    assert "## Part 2" in text
    assert "Part 2 shortened to first sentences" in text
    assert (
        "A19 Tax revenue [pro]:\nFinally, the government could use the sale of soft drugs "
        "as a source of revenue through excise duty, as is already done with alcohol and "
        "tobacco." in text
    )
    assert "Amphetamines interfere" not in text  # A4's second sentence is gone


def test_third_step_drops_part_2() -> None:
    text = render(soft_drugs_map(), max_chars=3000)
    assert _sections(text) == {"## Outline", "## Part 1: Claims"}
    assert "Parts 2 and 3 omitted (map too large); the outline shows every relation." in text


def test_the_outline_survives_a_limit_nothing_can_meet() -> None:
    text = render(soft_drugs_map(), max_chars=10)
    assert "## Outline" in text
    assert "- A19 Tax revenue [pro] — supports C1" in text


def test_shrinking_keeps_every_relation_visible() -> None:
    m = soft_drugs_map()
    outline = render(m, max_chars=3000).split("## Outline")[1].split("## Part 1")[0]
    for relation in m.relations:
        assert f"{relation.type} {relation.target}" in outline
