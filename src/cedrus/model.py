"""The argument map: claims, arguments, relations, and the rules the server enforces.

Nothing derived is stored here. Sides, depths, parents and challenge status are
computed from this structure in `derive.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NamedTuple

RelationType = Literal["supports", "attacks", "undercuts"]
RELATION_TYPES: tuple[RelationType, ...] = ("supports", "attacks", "undercuts")

Kind = Literal["claim", "argument"]

MAX_LABEL_CHARS = 80
MAX_TEXT_CHARS = 3000


class MapError(Exception):
    """A change the map refuses. The message is written for the model to read."""


@dataclass
class Item:
    """A claim or an argument."""

    id: str
    kind: Kind
    label: str
    text: str
    seq: int

    @property
    def is_claim(self) -> bool:
        return self.kind == "claim"


@dataclass
class Relation:
    """A directed relation from one item to another."""

    source: str
    type: RelationType
    target: str
    seq: int


class LinkResult(NamedTuple):
    """What `link` did: added a relation, changed its type, or found it already so."""

    relation: Relation
    status: Literal["added", "retyped", "unchanged"]
    previous: RelationType | None


def _check_label(label: str) -> str:
    label = " ".join(label.split())
    if not label:
        raise MapError("the label is empty. Give a short title of a few words.")
    if len(label) > MAX_LABEL_CHARS:
        raise MapError(f"the label is longer than {MAX_LABEL_CHARS} characters.")
    return label


def _check_text(text: str) -> str:
    text = text.strip()
    if not text:
        raise MapError("the text is empty. Write out the claim or the argument in full.")
    if len(text) > MAX_TEXT_CHARS:
        raise MapError(f"the text is longer than {MAX_TEXT_CHARS} characters.")
    return text


class ArgMap:
    """An argument map. Every method that changes it raises `MapError` or bumps `version`."""

    def __init__(self) -> None:
        self.items: dict[str, Item] = {}
        self.relations: list[Relation] = []
        self.deleted_ids: list[str] = []
        self.version = 0
        self._claims_created = 0
        self._arguments_created = 0
        self._seq = 0

    def restore_counters(self, claims_created: int, arguments_created: int, seq: int) -> None:
        """Set the counters after loading a map, so reused IDs stay impossible."""
        self._claims_created = claims_created
        self._arguments_created = arguments_created
        self._seq = seq

    # ---------------------------------------------------------------- reading

    def __contains__(self, item_id: object) -> bool:
        return item_id in self.items

    def get(self, item_id: str) -> Item | None:
        return self.items.get(item_id)

    def require(self, item_id: str) -> Item:
        item = self.items.get(item_id)
        if item is None:
            raise MapError(f'"{item_id}" does not exist.')
        return item

    @property
    def claims(self) -> list[Item]:
        return [i for i in self.items.values() if i.kind == "claim"]

    @property
    def arguments(self) -> list[Item]:
        return [i for i in self.items.values() if i.kind == "argument"]

    def outgoing(self, item_id: str) -> list[Relation]:
        """Relations that start at `item_id`, oldest first."""
        return [r for r in self.relations if r.source == item_id]

    def incoming(self, item_id: str) -> list[Relation]:
        """Relations that end at `item_id`, oldest first."""
        return [r for r in self.relations if r.target == item_id]

    def relation(self, source: str, target: str) -> Relation | None:
        for r in self.relations:
            if r.source == source and r.target == target:
                return r
        return None

    # ---------------------------------------------------------------- changes

    def add_claim(self, label: str, text: str) -> Item:
        label = _check_label(label)
        text = _check_text(text)
        self._claims_created += 1
        self._seq += 1
        item = Item(
            id=f"C{self._claims_created}",
            kind="claim",
            label=label,
            text=text,
            seq=self._seq,
        )
        self.items[item.id] = item
        self.version += 1
        return item

    def add_argument(self, target: str, relation: RelationType, label: str, text: str) -> Item:
        label = _check_label(label)
        text = _check_text(text)
        target_item = self.require(target)
        self._check_relation_type(relation, target_item)
        self._arguments_created += 1
        self._seq += 1
        item = Item(
            id=f"A{self._arguments_created}",
            kind="argument",
            label=label,
            text=text,
            seq=self._seq,
        )
        self.items[item.id] = item
        self._seq += 1
        self.relations.append(Relation(source=item.id, type=relation, target=target, seq=self._seq))
        self.version += 1
        return item

    def link(self, source: str, relation: RelationType, target: str) -> LinkResult:
        """Add a relation, or change the type of the one that is already there."""
        self.require(source)
        target_item = self.require(target)
        self._check_relation_type(relation, target_item)
        if source == target:
            raise MapError(f"{source} cannot relate to itself.")

        existing = self.relation(source, target)
        if existing is not None:
            if existing.type == relation:
                return LinkResult(existing, "unchanged", relation)
            previous = existing.type
            existing.type = relation
            self.version += 1
            return LinkResult(existing, "retyped", previous)

        self._check_no_cycle(source, target)
        self._seq += 1
        new = Relation(source=source, type=relation, target=target, seq=self._seq)
        self.relations.append(new)
        self.version += 1
        return LinkResult(new, "added", None)

    def unlink(self, source: str, target: str) -> Relation:
        source_item = self.require(source)
        self.require(target)
        existing = self.relation(source, target)
        if existing is None:
            raise MapError(f"{source} has no relation to {target}.")
        if source_item.kind == "argument" and len(self.outgoing(source)) == 1:
            raise MapError(
                f"{source} would be left without a target. "
                "Every argument responds to at least one claim or argument. "
                "Link it to its new target first, or delete it."
            )
        self.relations.remove(existing)
        self.version += 1
        return existing

    def edit(self, item_id: str, label: str = "", text: str = "") -> Item:
        item = self.require(item_id)
        if not label.strip() and not text.strip():
            raise MapError(
                f"nothing to change on {item_id}. Give a new label, a new text, or both."
            )
        if label.strip():
            item.label = _check_label(label)
        if text.strip():
            item.text = _check_text(text)
        self.version += 1
        return item

    def orphaned_by(self, item_ids: set[str]) -> list[str]:
        """Arguments that would lose every target if `item_ids` were deleted."""
        orphans: list[str] = []
        for item in self.items.values():
            if item.kind != "argument" or item.id in item_ids:
                continue
            targets = [r.target for r in self.outgoing(item.id)]
            if targets and all(t in item_ids for t in targets):
                orphans.append(item.id)
        return orphans

    def deletion_closure(self, item_id: str) -> list[str]:
        """`item_id` plus every argument that deleting it would strand, transitively."""
        doomed = {item_id}
        while True:
            more = self.orphaned_by(doomed)
            if not more:
                return sorted(doomed, key=lambda i: self.items[i].seq)
            doomed.update(more)

    def delete(self, item_id: str, with_replies: bool = False) -> list[str]:
        """Delete an item and its relations. Returns the IDs that were deleted."""
        self.require(item_id)
        orphans = self.orphaned_by({item_id})
        if orphans and not with_replies:
            listed = ", ".join(orphans)
            raise MapError(
                f"{item_id} cannot be deleted: {listed} "
                f"{'responds' if len(orphans) == 1 else 'respond'} only to it and would be left "
                f"without a target. Link {'it' if len(orphans) == 1 else 'them'} elsewhere first, "
                f'or call delete(id="{item_id}", with_replies=true) to delete '
                f"{'it' if len(orphans) == 1 else 'them'} too."
            )

        doomed = self.deletion_closure(item_id) if with_replies else [item_id]
        for gone in doomed:
            del self.items[gone]
            self.deleted_ids.append(gone)
        self.relations = [
            r for r in self.relations if r.source not in doomed and r.target not in doomed
        ]
        self.version += 1
        return doomed

    # ------------------------------------------------------------ rule checks

    def _check_relation_type(self, relation: RelationType, target: Item) -> None:
        if relation == "undercuts" and target.kind == "claim":
            raise MapError(
                f'"undercuts" needs an argument as its target, but {target.id} is a claim. '
                "An undercut says that an argument's reasons do not lead to its conclusion, "
                f'and a claim has no reasons. To give a reason against {target.id}, use "attacks".'
            )

    def _check_no_cycle(self, source: str, target: str) -> None:
        """Refuse a relation whose target already reaches back to its source."""
        seen: set[str] = set()
        stack = [target]
        while stack:
            current = stack.pop()
            if current == source:
                raise MapError(
                    f"{source} → {target} would make the map circular: "
                    f"{target} already responds, directly or indirectly, to {source}."
                )
            if current in seen:
                continue
            seen.add(current)
            stack.extend(r.target for r in self.outgoing(current))


def relation_type(value: str) -> RelationType:
    """Narrow a plain string to a `RelationType`, for callers that already checked it."""
    if value not in RELATION_TYPES:
        raise MapError(f'"{value}" is not a relation type.')
    return value
