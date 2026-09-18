"""How the environment around the agent reads the map (§5 of the plan).

The agent has no save or export tool. The server writes these files by itself after
every change, and serves the same content through the two MCP resources.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from cedrus.derive import derive
from cedrus.model import ArgMap, Item, Relation, relation_type
from cedrus.render import render

FORMAT = "cedrus2-map/1"


def to_dict(amap: ArgMap, session_id: str | None = None) -> dict[str, Any]:
    """The map as plain data, with a stable key order."""
    d = derive(amap)
    return {
        "format": FORMAT,
        "session_id": session_id,
        "version": amap.version,
        "claims": [_item(i) for i in sorted(amap.claims, key=lambda i: i.seq)],
        "arguments": [_item(i) for i in sorted(amap.arguments, key=lambda i: i.seq)],
        "relations": [_relation(r) for r in sorted(amap.relations, key=lambda r: r.seq)],
        "deleted_ids": list(amap.deleted_ids),
        "derived": {
            "roots": list(d.roots),
            "sides": dict(d.sides) if d.sides_on else {},
            "unchallenged": list(d.unchallenged),
        },
    }


def to_json(amap: ArgMap, session_id: str | None = None) -> str:
    return json.dumps(to_dict(amap, session_id), indent=2, ensure_ascii=False) + "\n"


def from_dict(data: dict[str, Any]) -> ArgMap:
    """Rebuild a map from `to_dict` output. For tests and harnesses; no tool uses it."""
    if data.get("format") != FORMAT:
        raise ValueError(f"unknown format {data.get('format')!r}, expected {FORMAT!r}")

    amap = ArgMap()
    for kind, key in (("claim", "claims"), ("argument", "arguments")):
        for raw in data.get(key, []):
            amap.items[raw["id"]] = Item(
                id=raw["id"],
                kind=kind,  # type: ignore[arg-type]
                label=raw["label"],
                text=raw["text"],
                seq=raw["seq"],
            )
    amap.items = dict(sorted(amap.items.items(), key=lambda kv: kv[1].seq))

    for raw in data.get("relations", []):
        amap.relations.append(
            Relation(
                source=raw["source"],
                type=relation_type(raw["type"]),
                target=raw["target"],
                seq=raw["seq"],
            )
        )

    amap.deleted_ids = list(data.get("deleted_ids", []))
    amap.version = int(data.get("version", 0))

    # IDs are never reused, so the counters have to clear the deleted ones too.
    known = list(amap.items) + amap.deleted_ids
    amap.restore_counters(
        claims_created=_highest(known, "C"),
        arguments_created=_highest(known, "A"),
        seq=max([i.seq for i in amap.items.values()] + [r.seq for r in amap.relations] + [0]),
    )
    return amap


def from_json(text: str) -> ArgMap:
    return from_dict(json.loads(text))


# ----------------------------------------------------------------- the writer


def text_path_for(json_path: Path) -> Path:
    """`/tmp/m.json` → `/tmp/m.txt`; a path without `.json` just gains `.txt`."""
    if json_path.suffix == ".json":
        return json_path.with_suffix(".txt")
    return json_path.with_name(json_path.name + ".txt")


def archive_path_for(json_path: Path) -> Path:
    """`/tmp/m.json` → the first free one of `/tmp/m.1.json`, `/tmp/m.2.json`, …"""
    n = 1
    while True:
        candidate = json_path.with_name(f"{json_path.stem}.{n}{json_path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def save(amap: ArgMap, json_path: Path, session_id: str | None = None) -> None:
    """Write the map beside the agent, as JSON and as the full rendering.

    Both files are replaced atomically, so a reader never sees half of one. The text
    file has no size limit: it is for people and harnesses, not for a context window.
    """
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(json_path, to_json(amap, session_id))
    _atomic_write(text_path_for(json_path), render(amap, max_chars=None))


def _atomic_write(path: Path, content: str) -> None:
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


# --------------------------------------------------------------------- pieces


def _item(item: Item) -> dict[str, Any]:
    return {"id": item.id, "label": item.label, "text": item.text, "seq": item.seq}


def _relation(relation: Relation) -> dict[str, Any]:
    return {
        "source": relation.source,
        "type": relation.type,
        "target": relation.target,
        "seq": relation.seq,
    }


def _highest(ids: list[str], prefix: str) -> int:
    numbers = [int(i[1:]) for i in ids if i.startswith(prefix) and i[1:].isdigit()]
    return max(numbers, default=0)
