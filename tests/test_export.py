"""JSON export and the files the environment reads (§5 of the plan)."""

import json
from pathlib import Path

import pytest
from fixtures.soft_drugs import soft_drugs_map

from cedrus.export import from_json, save, text_path_for, to_dict, to_json
from cedrus.model import ArgMap
from cedrus.render import render


def test_round_trip_gives_back_the_same_map() -> None:
    original = soft_drugs_map()
    rebuilt = from_json(to_json(original))
    assert to_dict(rebuilt) == to_dict(original)
    assert render(rebuilt) == render(original)


def test_round_trip_keeps_counters_so_ids_are_not_reused() -> None:
    rebuilt = from_json(to_json(soft_drugs_map()))
    assert rebuilt.add_argument("C1", "supports", "Next", "Text.").id == "A20"
    assert rebuilt.add_claim("Another", "Text.").id == "C2"


def test_an_empty_map_round_trips() -> None:
    rebuilt = from_json(to_json(ArgMap()))
    assert rebuilt.items == {}
    assert rebuilt.add_claim("First", "Text.").id == "C1"


def test_json_has_the_documented_shape() -> None:
    data = json.loads(to_json(soft_drugs_map(), session_id="abc"))
    assert list(data) == [
        "format",
        "session_id",
        "version",
        "claims",
        "arguments",
        "relations",
        "deleted_ids",
        "derived",
    ]
    assert data["format"] == "cedrus2-map/1"
    assert data["session_id"] == "abc"
    assert data["version"] == 23
    assert data["claims"][0] == {
        "id": "C1",
        "label": "Legalisation of Soft Drugs",
        "text": "Soft drugs should be legal.",
        "seq": 1,
    }
    assert data["relations"][0] == {"source": "A1", "type": "attacks", "target": "C1", "seq": 3}
    assert data["deleted_ids"] == ["A17", "A18"]
    assert data["derived"]["roots"] == ["C1"]
    assert data["derived"]["sides"]["A4"] == "con"
    assert "A4" in data["derived"]["unchallenged"]


def test_derived_is_left_out_when_sides_are_off() -> None:
    m = soft_drugs_map()
    m.add_claim("A second debate", "Something else.")
    data = to_dict(m)
    assert data["derived"]["roots"] == ["C1", "C2"]
    assert data["derived"]["sides"] == {}


def test_an_unknown_format_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown format"):
        from_json('{"format": "something-else/9"}')


# ---------------------------------------------------------------- the writer


def test_save_writes_both_files(tmp_path: Path) -> None:
    target = tmp_path / "map.json"
    m = soft_drugs_map()
    save(m, target, session_id="s1")

    assert json.loads(target.read_text())["version"] == 23
    text = (tmp_path / "map.txt").read_text()
    assert text.startswith("ARGUMENT MAP: Legalisation of Soft Drugs")
    assert "## Part 3" in text


def test_the_text_file_has_no_size_limit(tmp_path: Path) -> None:
    target = tmp_path / "map.json"
    m = soft_drugs_map()
    save(m, target)
    assert (tmp_path / "map.txt").read_text() == render(m, max_chars=None)


def test_save_keeps_up_with_every_change(tmp_path: Path) -> None:
    target = tmp_path / "map.json"
    m = ArgMap()
    for label in ("Root", "Second", "Third"):
        if label == "Root":
            m.add_claim(label, "Text.")
        else:
            m.add_argument("C1", "supports", label, "Text.")
        save(m, target)
        assert json.loads(target.read_text())["version"] == m.version


def test_save_creates_missing_directories(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "map.json"
    save(soft_drugs_map(), target)
    assert target.exists()


def test_save_leaves_no_temporary_files_behind(tmp_path: Path) -> None:
    save(soft_drugs_map(), tmp_path / "map.json")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["map.json", "map.txt"]


def test_an_overwritten_file_is_never_seen_half_written(tmp_path: Path) -> None:
    target = tmp_path / "map.json"
    save(ArgMap(), target)
    first = target.read_text()
    save(soft_drugs_map(), target)
    assert target.read_text() != first
    assert json.loads(target.read_text())["version"] == 23


@pytest.mark.parametrize(
    ("given", "expected"),
    [("map.json", "map.txt"), ("map", "map.txt"), ("map.data", "map.data.txt")],
)
def test_text_path_sits_next_to_the_json(tmp_path: Path, given: str, expected: str) -> None:
    assert text_path_for(tmp_path / given) == tmp_path / expected
