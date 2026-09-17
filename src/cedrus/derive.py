"""Everything the map does not store: roots, places, depths, sides, challenge status.

All of it is recomputed from `ArgMap` on every read, so it can never go stale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from cedrus.model import ArgMap, Relation

Side = Literal["pro", "con", "mixed"]

FLIP: dict[Side, Side] = {"pro": "con", "con": "pro", "mixed": "mixed"}


@dataclass
class Derived:
    """A snapshot of the derived values for one version of the map."""

    roots: list[str] = field(default_factory=list)
    primary: dict[str, str] = field(default_factory=dict)
    extra: dict[str, list[Relation]] = field(default_factory=dict)
    depth: dict[str, int] = field(default_factory=dict)
    children: dict[str, list[str]] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    sides: dict[str, Side] = field(default_factory=dict)
    sides_on: bool = False
    unchallenged: list[str] = field(default_factory=list)

    def side(self, item_id: str) -> Side | None:
        """The item's side, or `None` when the map does not show sides."""
        return self.sides.get(item_id) if self.sides_on else None

    def tag(self, item_id: str) -> str:
        """The side as it is printed, e.g. `" [con]"`, or an empty string.

        A root claim carries no tag: it is the thing the sides are measured against.
        """
        if item_id in self.roots:
            return ""
        side = self.side(item_id)
        return f" [{side}]" if side else ""

    @property
    def mixed(self) -> list[str]:
        if not self.sides_on:
            return []
        return [i for i in self.order if self.sides.get(i) == "mixed"]


def derive(amap: ArgMap) -> Derived:
    """Compute every derived value for `amap`."""
    d = Derived()
    if not amap.items:
        return d

    # Roots: claims that respond to nothing. Since every argument has a target and
    # the map is acyclic, every non-empty map has at least one, and all are claims.
    d.roots = [i.id for i in amap.items.values() if i.kind == "claim" and not amap.outgoing(i.id)]

    # Place: the oldest remaining target decides where an item sits in the outline.
    for item in amap.items.values():
        out = amap.outgoing(item.id)
        if not out:
            continue
        d.primary[item.id] = out[0].target
        d.extra[item.id] = out[1:]

    d.children = {item_id: [] for item_id in amap.items}
    for item in amap.items.values():
        parent = d.primary.get(item.id)
        if parent is not None:
            d.children[parent].append(item.id)
    for kids in d.children.values():
        kids.sort(key=lambda i: amap.items[i].seq)

    # Outline order, and depth as the number of steps up to a root.
    for root in d.roots:
        _walk(root, 0, d, d.order)

    d.sides_on = len(d.roots) == 1
    if d.sides_on:
        sides: dict[str, Side] = {}
        for item_id in amap.items:
            _side(item_id, amap, d.roots[0], sides, set())
        d.sides = sides

    d.unchallenged = [
        item.id
        for item in amap.items.values()
        if item.id not in d.roots and not amap.incoming(item.id)
    ]
    return d


def _walk(item_id: str, depth: int, d: Derived, out: list[str]) -> None:
    d.depth[item_id] = depth
    out.append(item_id)
    for child in d.children.get(item_id, []):
        _walk(child, depth + 1, d, out)


def _side(item_id: str, amap: ArgMap, root: str, sides: dict[str, Side], busy: set[str]) -> Side:
    """The side of `item_id` relative to the single root claim."""
    if item_id in sides:
        return sides[item_id]
    if item_id == root:
        sides[item_id] = "pro"
        return "pro"
    if item_id in busy:  # cannot happen in an acyclic map; keeps the recursion safe
        return "mixed"

    busy.add(item_id)
    seen: set[Side] = set()
    for relation in amap.outgoing(item_id):
        target = _side(relation.target, amap, root, sides, busy)
        seen.add(target if relation.type == "supports" else FLIP[target])
    busy.discard(item_id)

    result: Side = seen.pop() if len(seen) == 1 else "mixed"
    sides[item_id] = result
    return result
