"""The one view of the map: what `show()` prints.

`render()` always describes the whole map. When the result would be too long it is
shortened in fixed steps (§3 of the plan), never by a parameter the model passes.
"""

from __future__ import annotations

import re

from cedrus.derive import Derived, derive
from cedrus.model import ArgMap, Relation

DEFAULT_MAX_CHARS = 24000

EMPTY_MAP = "The map is empty. Start with add_claim(label, text)."

RELATION_LEGEND = """\
Relation types:
  supports   X gives a reason for Y
  attacks    X gives a reason against Y
  undercuts  X gives a reason why Y fails to
             establish its conclusion, without denying the truth of Y's premises."""

ARROWS = '"X → R Y" means X R Y. "Y ← R X" is the same relation, listed under Y.'

SIDES_ON = (
    "[pro]/[con] shows which side of the root claim an item is on. It is not the "
    "relation type: a [con] argument can support another [con] argument."
)

ORDERING = (
    "Order: top-down, depth-first. Each item comes right after the one it responds to. "
    "IDs are permanent labels; their numbers reflect order of creation; they say nothing "
    "about position."
)

UNDER = '"under X" names the item\'s place in the outline.'

_SENTENCE_END = re.compile(r"(?<=[.!?])\s")
_SHORT_TEXT_CHARS = 160


def render(amap: ArgMap, max_chars: int | None = DEFAULT_MAX_CHARS) -> str:
    """The full view of `amap`, shortened in steps if it exceeds `max_chars`."""
    if not amap.items:
        return EMPTY_MAP

    d = derive(amap)
    attempts = [
        _build(amap, d, part2="full", part3=True),
        _build(amap, d, part2="full", part3=False),
        _build(amap, d, part2="short", part3=False),
        _build(amap, d, part2="none", part3=False),
    ]
    if max_chars is None:
        return attempts[0]
    for text in attempts:
        if len(text) <= max_chars:
            return text
    return attempts[-1]


def counts(amap: ArgMap, d: Derived | None = None) -> str:
    """e.g. `1 claim, 17 arguments, 19 relations` — also used in tool results."""
    d = d if d is not None else derive(amap)
    n_claims = len(amap.claims)
    roots = len(d.roots)
    claims = _plural(n_claims, "claim")
    if n_claims > roots:
        claims += f" ({roots} root)"
    arguments = _plural(len(amap.arguments), "argument")
    relations = _plural(len(amap.relations), "relation")
    return f"{claims}, {arguments}, {relations}"


# ------------------------------------------------------------------- sections


def _build(amap: ArgMap, d: Derived, part2: str, part3: bool) -> str:
    blocks = [_header(amap, d, part2, part3), _outline(amap, d), _claims(amap, d)]
    if part2 != "none":
        blocks.append(_arguments(amap, d, short=part2 == "short"))
    if part3:
        blocks.append(_structure(amap, d))
    return "\n\n".join(blocks) + "\n"


def _header(amap: ArgMap, d: Derived, part2: str, part3: bool) -> str:
    if len(d.roots) == 1:
        title = amap.items[d.roots[0]].label
    else:
        title = f"{len(d.roots)} root claims"

    lines = [f"ARGUMENT MAP: {title}", f"Map v{amap.version}. {counts(amap, d)}."]

    omitted = _omission_note(part2, part3)
    if omitted:
        lines.append(omitted)

    lines.append("")
    lines.append(RELATION_LEGEND)
    lines.append("")
    if d.sides_on:
        lines.append(f"{ARROWS} {SIDES_ON}")
    else:
        lines.append(
            f"{ARROWS} No [pro]/[con] tags are shown: the map has {len(d.roots)} root "
            "claims, and a side only means something against a single one."
        )
    lines.append("")
    lines.append(ORDERING)
    lines.append(UNDER)

    lines.extend(_notes(amap, d))
    return "\n".join(lines)


def _omission_note(part2: str, part3: bool) -> str:
    if part3:
        return ""
    if part2 == "full":
        return "Part 3 omitted (map too large); the outline shows every relation."
    if part2 == "short":
        return (
            "Part 3 omitted and Part 2 shortened to first sentences (map too large); "
            "the outline shows every relation."
        )
    return "Parts 2 and 3 omitted (map too large); the outline shows every relation."


def _notes(amap: ArgMap, d: Derived) -> list[str]:
    notes: list[str] = []

    multi = [i for i in d.order if d.extra.get(i)]
    if multi:
        notes.append("Items with more than one target (each is listed once, under the first):")
        for item_id in multi:
            extras = ", ".join(f"{r.type} {r.target}" for r in d.extra[item_id])
            notes.append(f"  {item_id} also {extras}")

    if d.mixed:
        notes.append("Mixed items (their targets are on both sides, so no single side fits):")
        notes.append(f"  {', '.join(d.mixed)}")

    if d.unchallenged:
        notes.append("Unchallenged (nothing supports, attacks or undercuts them):")
        notes.append(f"  {', '.join(d.unchallenged)}")

    if amap.deleted_ids:
        notes.append("Deleted IDs (not reused):")
        notes.append(f"  {', '.join(amap.deleted_ids)}")

    return notes


def _outline(amap: ArgMap, d: Derived) -> str:
    lines = ["## Outline", ""]
    for item_id in d.order:
        indent = "  " * d.depth[item_id]
        item = amap.items[item_id]
        line = f"{indent}- {item_id} {item.label}{d.tag(item_id)}"
        parent = d.primary.get(item_id)
        if parent is not None:
            relation = amap.relation(item_id, parent)
            assert relation is not None
            line += f" — {relation.type} {parent}"
            extras = d.extra.get(item_id) or []
            if extras:
                line += " (also " + ", ".join(f"{r.type} {r.target}" for r in extras) + ")"
        lines.append(line)
    return "\n".join(lines)


def _claims(amap: ArgMap, d: Derived) -> str:
    lines = ["## Part 1: Claims"]
    for claim in amap.claims:
        lines.append("")
        lines.append(f"{claim.id} {claim.label}{d.tag(claim.id)}:")
        lines.append(claim.text)
    return "\n".join(lines)


def _arguments(amap: ArgMap, d: Derived, short: bool) -> str:
    lines = ["## Part 2: Arguments (full text)"]
    for item_id in d.order:
        item = amap.items[item_id]
        if item.kind != "argument":
            continue
        lines.append("")
        lines.append(f"{item.id} {item.label}{d.tag(item.id)}:")
        lines.append(_first_sentence(item.text) if short else item.text)
    return "\n".join(lines)


def _structure(amap: ArgMap, d: Derived) -> str:
    lines = ["## Part 3: Dialectical structure (all relations, listed in both directions)"]
    for item_id in d.order:
        item = amap.items[item_id]
        lines.append("")
        fields = [f"{item.id} {item.label}{d.tag(item_id)}"]
        if item_id in d.roots:
            fields.append("root claim")
            fields.append("depth 0")
        else:
            fields.append(f"depth {d.depth[item_id]}")
            fields.append(f"under {d.primary[item_id]}")
        if item_id in d.unchallenged:
            fields.append("unchallenged")
        lines.append(" | ".join(fields))
        for relation in amap.outgoing(item_id):
            lines.append(f"  → {_other(amap, relation, relation.target)}")
        for relation in amap.incoming(item_id):
            lines.append(f"  ← {_other(amap, relation, relation.source)}")
    return "\n".join(lines)


def _other(amap: ArgMap, relation: Relation, other_id: str) -> str:
    return f"{relation.type.ljust(11)}{other_id} {amap.items[other_id].label}"


# --------------------------------------------------------------------- pieces


def _plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _first_sentence(text: str) -> str:
    first = _SENTENCE_END.split(text.strip(), maxsplit=1)[0]
    if len(first) > _SHORT_TEXT_CHARS:
        first = first[:_SHORT_TEXT_CHARS].rstrip()
    if first != text.strip():
        first += " …"
    return first
