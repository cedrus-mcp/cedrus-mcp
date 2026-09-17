"""The seven tools, as plain functions over a `Session`.

Each one parses what the model wrote, asks the map to change, and describes the result.
Nothing here imports the MCP SDK, so the whole tool layer is testable on its own;
`server.py` wraps these and turns a `MapError` into a tool error.
"""

from __future__ import annotations

from cedrus.derive import derive
from cedrus.model import MapError
from cedrus.parse import (
    clean_label,
    clean_text,
    duplicate_label_warning,
    resolve_id,
    resolve_relation,
)
from cedrus.render import render
from cedrus.result import Session, ok

TOOL_NAMES = ("show", "add_claim", "add_argument", "link", "unlink", "edit", "delete")


def show(session: Session, max_chars: int | None) -> str:
    """The whole map. Not an `OK:` result: it replaces whatever `show()` printed before."""
    text = render(session.amap, max_chars=max_chars)
    session.mark_shown()
    return text


def add_claim(session: Session, label: str, text: str) -> str:
    amap = session.amap
    label, cut = clean_label(label)
    body = clean_text(text)
    item = amap.add_claim(label, body)

    d = derive(amap)
    if item.id in d.roots:
        headline = f"Added {_name(session, item.id)}. It is a root claim, so nothing is above it."
    else:  # unreachable today: a new claim has no relations yet
        headline = f"Added {_name(session, item.id)}."
    return ok(headline, session, _notes(cut, duplicate_label_warning(amap, label, item.id)))


def add_argument(session: Session, target: str, relation: str, label: str, text: str) -> str:
    amap = session.amap
    target_id = resolve_id(amap, target, "target")
    kind = resolve_relation(relation)
    label, cut = clean_label(label)
    body = clean_text(text)

    item = amap.add_argument(target_id, kind, label, body)
    headline = (
        f"Added {_name(session, item.id)}. "
        f"It {kind} {_name(session, target_id)} (under {target_id})."
    )
    return ok(headline, session, _notes(cut, duplicate_label_warning(amap, label, item.id)))


def link(session: Session, source: str, relation: str, target: str) -> str:
    amap = session.amap
    source_id = resolve_id(amap, source, "source")
    target_id = resolve_id(amap, target, "target")
    kind = resolve_relation(relation)

    result = amap.link(source_id, kind, target_id)
    if result.status == "added":
        headline = f"{_name(session, source_id)} now {kind} {_name(session, target_id)}."
    elif result.status == "unchanged":
        headline = f"{source_id} already {kind} {target_id}, so nothing changed."
    else:
        headline = (
            f"{_name(session, source_id)} now {kind} {_name(session, target_id)}, "
            f"where it {result.previous} it before."
        )
    return ok(headline, session, _placed(session, source_id))


def unlink(session: Session, source: str, target: str) -> str:
    amap = session.amap
    source_id = resolve_id(amap, source, "source")
    target_id = resolve_id(amap, target, "target")

    removed = amap.unlink(source_id, target_id)
    headline = f"{source_id} no longer {removed.type} {target_id}."
    left = [r.target for r in amap.outgoing(source_id)]
    if left:
        headline += f" It still responds to {', '.join(left)}."
    else:
        headline += f" {source_id} now responds to nothing."
    return ok(headline, session, _placed(session, source_id))


def edit(session: Session, item_id: str, label: str = "", text: str = "") -> str:
    amap = session.amap
    resolved = resolve_id(amap, item_id)

    changed: list[str] = []
    cut = ""
    new_label = ""
    if label.strip():
        new_label, cut = clean_label(label)
        changed.append("label")
    body = clean_text(text) if text.strip() else ""
    if body:
        changed.append("text")
    if not changed:
        raise MapError(f"nothing to change on {resolved}. Give a new label, a new text, or both.")

    amap.edit(resolved, label=new_label, text=body)
    headline = f"Updated the {' and the '.join(changed)} of {_name(session, resolved)}."
    duplicate = duplicate_label_warning(amap, new_label, resolved) if new_label else ""
    return ok(headline, session, _notes(cut, duplicate))


def delete(session: Session, item_id: str, with_replies: bool = False) -> str:
    amap = session.amap
    resolved = resolve_id(amap, item_id)
    label = amap.require(resolved).label

    gone = amap.delete(resolved, with_replies=with_replies)
    if len(gone) == 1:
        headline = f'Deleted {resolved} "{label}".'
    else:
        others = ", ".join(gone[1:])
        headline = f'Deleted {resolved} "{label}", and with it {others}.'
    headline += " Deleted IDs are never given to a new item."
    return ok(headline, session)


# --------------------------------------------------------------------- pieces


def _name(session: Session, item_id: str) -> str:
    """`A20 "Tax evasion" [con]` — the ID, the label and the side, as the view shows it."""
    item = session.amap.items[item_id]
    return f'{item.id} "{item.label}"{derive(session.amap).tag(item_id)}'


def _placed(session: Session, item_id: str) -> str:
    """Where the item sits now, when a relation change may have moved it."""
    d = derive(session.amap)
    parent = d.primary.get(item_id)
    if parent is None:
        return f"{item_id} is now a root claim."
    return f"It is shown under {parent}."


def _notes(*parts: str) -> str:
    return " ".join(part for part in parts if part)
