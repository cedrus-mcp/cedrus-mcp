"""Reading what a small model actually types (§2 of the plan, "Shared input handling").

Everything here is forgiving about form and strict about meaning: `a7`, `[A7]` and
`A7 Alcohol and tobacco analogy` all mean `A7`, but `A21` in a map without an A21 is an
error that names the nearest real IDs instead of guessing.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from cedrus.model import (
    MAX_LABEL_CHARS,
    MAX_TEXT_CHARS,
    RELATION_TYPES,
    ArgMap,
    MapError,
    RelationType,
)

_ID = re.compile(r"^[\s\[\(\{\"'`*_#]*([CcAa])[\s\-_.:#]*(\d+)")

_RELATIONS: dict[str, RelationType] = {
    "support": "supports",
    "supports": "supports",
    "attack": "attacks",
    "attacks": "attacks",
    "undercut": "undercuts",
    "undercuts": "undercuts",
}

_SUGGESTION_SCORE = 60
_MAX_SUGGESTIONS = 2
_MAX_LISTED_IDS = 12


def resolve_id(amap: ArgMap, raw: str, field: str = "id") -> str:
    """Turn whatever the model wrote into an ID that exists, or raise `MapError`."""
    text = raw.strip()
    if not text:
        raise MapError(f'{field} is empty. Give the ID of a claim or an argument, e.g. "C1".')

    match = _ID.match(text)
    if match:
        candidate = f"{match.group(1).upper()}{int(match.group(2))}"
        if candidate in amap:
            return candidate

    for item in amap.items.values():  # the model may have pasted a label instead
        if item.label.casefold() == text.casefold():
            return item.id

    raise MapError(f'"{text}" does not exist.{did_you_mean(amap, text)}')


def resolve_relation(raw: str) -> RelationType:
    """Accept `support`, `Supports`, `UNDERCUT` and so on; refuse anything else."""
    key = raw.strip().strip(".,;:!\"'").casefold()
    if key in _RELATIONS:
        return _RELATIONS[key]
    valid = ", ".join(f'"{r}"' for r in RELATION_TYPES)
    raise MapError(f'"{raw.strip()}" is not a relation. Use one of {valid}.')


def clean_label(raw: str) -> tuple[str, str]:
    """A one-line label, plus a warning when it had to be cut."""
    label = " ".join(raw.split())
    if not label:
        raise MapError("the label is empty. Give a short title of a few words.")
    if len(label) <= MAX_LABEL_CHARS:
        return label, ""
    label = label[:MAX_LABEL_CHARS].rstrip()
    return label, f"The label was cut to {MAX_LABEL_CHARS} characters."


def clean_text(raw: str, field: str = "text") -> str:
    text = raw.strip()
    if not text:
        raise MapError(f"{field} is empty. Write out the claim or the argument in full.")
    if len(text) > MAX_TEXT_CHARS:
        raise MapError(
            f"{field} is {len(text)} characters long; the limit is {MAX_TEXT_CHARS}. "
            "Shorten it, or split the argument into two."
        )
    return text


def duplicate_label_warning(amap: ArgMap, label: str, ignore: str = "") -> str:
    """Two items may share a label; the model should still know that they do."""
    same = [i.id for i in amap.items.values() if i.id != ignore and i.label == label]
    if not same:
        return ""
    return f'{", ".join(same)} already has the label "{label}".'


def did_you_mean(amap: ArgMap, raw: str) -> str:
    """A sentence naming real IDs, or an empty string when there is nothing to name."""
    if not amap.items:
        return " The map is empty. Start with add_claim(label, text)."

    # "C3" asks for a claim, so claims come first even when some argument reads closer.
    match = _ID.match(raw.strip())
    wanted = f"{match.group(1).upper()}" if match else ""

    ranked = [
        (
            max(fuzz.WRatio(raw, item.id), fuzz.WRatio(raw, item.label)),
            item.id.startswith(wanted) if wanted else False,
            item,
        )
        for item in amap.items.values()
    ]
    ranked.sort(key=lambda row: (not row[1], -row[0], row[2].seq))
    close = [
        item
        for score, _, item in ranked[:_MAX_SUGGESTIONS]
        # A near miss, or the right kind of item: "C3" is best answered with real claims.
        if score >= _SUGGESTION_SCORE or (wanted and item.id.startswith(wanted))
    ]

    if close:
        named = _join([f'{i.id} "{i.label}"' for i in close], "or")
        return f" Did you mean {named}?"

    ids = list(amap.items)
    if len(ids) <= _MAX_LISTED_IDS:
        return f" The map has: {', '.join(ids)}."
    shown = ", ".join(ids[:_MAX_LISTED_IDS])
    return f" The map has {len(ids)} items, among them {shown}. Call show() to see them all."


def _join(parts: list[str], word: str) -> str:
    if len(parts) == 1:
        return parts[0]
    return f"{', '.join(parts[:-1])} {word} {parts[-1]}"
