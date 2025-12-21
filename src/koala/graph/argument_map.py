# src/koala/graph/argument_map.py

from __future__ import annotations
import textwrap

from mcp.server.fastmcp.utilities.logging import get_logger

from datetime import datetime
import re
import networkx as nx
from typing import Any, Dict, Iterator, List, Optional
from koala.models.base import PropositionID, NodeLabel
from koala.models.nodes import ClaimNode, ArgumentNode
from koala.models.propositions import Proposition
from koala.models.relations import DialecticalRelation, LogicalRelation


logger = get_logger("koala.graph")  # Creates 'FastMCP.koala' logger


class ArgumentMap:
    """NetworkX-based argument map."""

    def __init__(self) -> None:
        self.argument_graph: nx.DiGraph[NodeLabel] = nx.DiGraph()
        self.proposition_graph: nx.Graph[PropositionID] = nx.Graph()

    # === Node Operations ===

    def add_claim(self, node: ClaimNode) -> None:
        """Add a claim node to the graph."""
        if not self.is_unique_label(node.label):
            raise ValueError(f"Label '{node.label}' already exists.")
        self.argument_graph.add_node(node.label, **node.model_dump(by_alias=True))

    def add_argument(self, node: ArgumentNode) -> None:
        """Add an argument node to the graph."""
        if not self.is_unique_label(node.label):
            raise ValueError(f"Label '{node.label}' already exists.")
        self.argument_graph.add_node(node.label, **node.model_dump(by_alias=True))

    def get_node(self, label: NodeLabel) -> ClaimNode | ArgumentNode:
        """Get a node by label."""
        data = dict(self.argument_graph.nodes[label])
        if data["_type"] == "claim":
            return ClaimNode(**data)
        return ArgumentNode(**data)

    def get_argument(self, label: NodeLabel) -> ArgumentNode | None:
        """Get an argument node by label."""
        data = dict(self.argument_graph.nodes[label])
        if data["_type"] == "argument":
            return ArgumentNode(**data)
        return None

    def get_claim(self, label: NodeLabel) -> ClaimNode | None:
        """Get a claim node by label."""
        data = dict(self.argument_graph.nodes[label])
        if data["_type"] == "claim":
            return ClaimNode(**data)
        return None

    def update_label(self, old_label: NodeLabel, new_label: NodeLabel) -> None:
        """Update a node's label."""
        if not self.is_unique_label(new_label):
            raise ValueError(f"Label '{new_label}' already exists.")
        if not self.argument_graph.has_node(old_label):
            logger.warning(f"Node with label '{old_label}' does not exist.")
            return

        self.update_node(old_label, updates={"label": new_label})
        nx.relabel_nodes(self.argument_graph, {old_label: new_label}, copy=False)

    def update_node(self, label: NodeLabel, updates: Dict[str, Any]) -> None:
        """Update node attributes."""
        node = self.get_node(label)
        for key, value in updates.items():
            setattr(node, key, value)
            setattr(node, "_last_modified", datetime.now())
        self.argument_graph.nodes[label].update(node.model_dump(by_alias=True))

    def delete_node(self, label: NodeLabel) -> None:
        """Delete a node and its relations."""
        self.argument_graph.remove_node(label)

    # === Relation Operations ===

    def get_dialectic_relation(
        self, from_label: str, to_label: str
    ) -> Optional[DialecticalRelation]:
        """Get a dialectical relation."""
        if self.argument_graph.has_edge(from_label, to_label):
            data = dict(self.argument_graph.edges[from_label, to_label])
            return DialecticalRelation(**data)
        return None

    def add_support_relation(
        self, from_label: NodeLabel, to_label: NodeLabel, target_premise_idx: int | None = None
    ) -> None:
        """Add a support relation."""

        # Checks
        if not self.argument_graph.has_node(from_label):
            raise ValueError(f"From node '{from_label}' does not exist.")
        if not self.argument_graph.has_node(to_label):
            raise ValueError(f"To node '{to_label}' does not exist.")
        existing_relation = self.get_dialectic_relation(from_label, to_label)
        if existing_relation:
            if existing_relation.relation_type == "support":
                logger.info(f"Support relation from '{from_label}' to '{to_label}' already exists.")
                return
            else:
                raise ValueError(
                    f"An attack relation from '{from_label}' to '{to_label}' already exists, cannot add additional support relation."
                )
        if target_premise_idx is not None:
            target_node = self.get_node(to_label)
            if not isinstance(target_node, ArgumentNode):
                raise ValueError(
                    f"Target node '{to_label}' is not an argument, cannot specify target_premise_idx."
                )
            if target_premise_idx < 0 or target_premise_idx >= len(target_node.premises):
                raise ValueError(
                    f"target_premise_idx {target_premise_idx} is out of bounds for argument '{to_label}'."
                )

        # Add relation
        support = DialecticalRelation(_type="support", target_premise_idx=target_premise_idx)
        self.argument_graph.add_edge(from_label, to_label, **support.model_dump(by_alias=True))

    def add_attack_relation(
        self, from_label: str, to_label: str, target_premise_idx: int | None = None
    ) -> None:
        """Add an attack relation."""

        # Checks
        if not self.argument_graph.has_node(from_label):
            raise ValueError(f"From node '{from_label}' does not exist.")
        if not self.argument_graph.has_node(to_label):
            raise ValueError(f"To node '{to_label}' does not exist.")
        existing_relation = self.get_dialectic_relation(from_label, to_label)
        if existing_relation:
            if existing_relation.relation_type == "attack":
                logger.info(f"Attack relation from '{from_label}' to '{to_label}' already exists.")
                return
            else:
                raise ValueError(
                    f"A support relation from '{from_label}' to '{to_label}' already exists, cannot add additional attack relation."
                )
        if target_premise_idx is not None:
            target_node = self.get_node(to_label)
            if not isinstance(target_node, ArgumentNode):
                raise ValueError(
                    f"Target node '{to_label}' is not an argument, cannot specify target_premise_idx."
                )
            if target_premise_idx < 0 or target_premise_idx >= len(target_node.premises):
                raise ValueError(
                    f"target_premise_idx {target_premise_idx} is out of bounds for argument '{to_label}'."
                )

        # Add relation
        attack = DialecticalRelation(_type="attack", target_premise_idx=target_premise_idx)
        self.argument_graph.add_edge(from_label, to_label, **attack.model_dump(by_alias=True))

    def update_relation(
        self, from_label: str,
        to_label: str,
        updates: Dict[str, Any]
    ) -> None:
        """Update a relation's attributes."""
        relation = self.get_dialectic_relation(from_label, to_label)
        if not relation:
            raise ValueError(f"Relation from '{from_label}' to '{to_label}' does not exist.")
        for key, value in updates.items():
            setattr(relation, key, value)
            setattr(relation, "_last_modified", datetime.now())
        self.argument_graph.edges[from_label, to_label].update(relation.model_dump(by_alias=True))

    def delete_relation(self, from_label: str, to_label: str) -> None:
        """Delete a relation."""
        if self.argument_graph.has_edge(from_label, to_label):
            self.argument_graph.remove_edge(from_label, to_label)
        else:
            logger.warning(
                f"Cannot delete relation from '{from_label}' to '{to_label}' because it does not exist."
            )

    # === Proposition Operations ===

    def add_proposition(self, prop: Proposition) -> None:
        """Add a proposition."""
        self.proposition_graph.add_node(prop.id, **prop.model_dump(by_alias=True))

    def get_proposition(self, prop_id: PropositionID) -> Optional[Proposition]:
        """Get a proposition by ID."""
        if self.proposition_graph.has_node(prop_id):
            data = dict(self.proposition_graph.nodes[prop_id])
            return Proposition(**data)
        return None

    def update_proposition(self, prop_id: PropositionID, updates: Dict[str, Any]) -> None:
        """Update proposition attributes."""
        prop = self.get_proposition(prop_id)
        if not prop:
            raise ValueError(f"Proposition with ID '{prop_id}' does not exist.")
        for key, value in updates.items():
            setattr(prop, key, value)
            setattr(prop, "_last_modified", datetime.now())
        self.proposition_graph.nodes[prop_id].update(prop.model_dump(by_alias=True))

    def delete_proposition(self, prop_id: PropositionID) -> None:
        """Delete a proposition."""
        try:
            self.proposition_graph.remove_node(prop_id)
        except nx.NetworkXError:
            logger.warning(
                f"Cannot delete proposition with ID '{prop_id}' because it does not exist."
            )

    # === Logical Relation Operations ===

    def get_logical_relation(
        self, prop1: PropositionID, prop2: PropositionID
    ) -> Optional[LogicalRelation]:
        """Get a logical relation between two propositions."""
        if self.proposition_graph.has_edge(prop1, prop2):
            data = dict(self.proposition_graph.edges[prop1, prop2])
            return LogicalRelation(**data)
        return None

    def are_equivalent(self, prop1: PropositionID, prop2: PropositionID) -> bool:
        """Check if two propositions are equivalent."""
        equiv_graph: nx.Graph[PropositionID] = self._get_equivalence_graph()
        return nx.has_path(equiv_graph, prop1, prop2)

    def are_contradictory(self, prop1: PropositionID, prop2: PropositionID) -> bool:
        """Check if two propositions are contradictory."""
        # check whether any q1 equivalent to prop1 has a negation relation with any q2 equivalent to prop2

        equiv_graph: nx.Graph[PropositionID] = self._get_equivalence_graph()
        equivs1 = nx.node_connected_component(equiv_graph, prop1)
        equivs2 = nx.node_connected_component(equiv_graph, prop2)

        for q1 in equivs1 | {prop1}:
            for q2 in equivs2 | {prop2}:
                if self.proposition_graph.has_edge(q1, q2):
                    if self.proposition_graph.edges[q1, q2]["_type"] == "negation":
                        return True
        return False

    def add_equivalence(self, prop1: PropositionID, prop2: PropositionID) -> None:
        """Add an equivalence relation."""
        if self.are_contradictory(prop1, prop2):
            raise ValueError(
                f"Cannot add equivalence relation between contradictory propositions {prop1} and {prop2}."
            )
        if prop1 == prop2:
            logger.warning(
                f"Skipping adding equivalence relation between identical propositions {prop1} and {prop2}."
            )
            return
        if existing_relation := self.get_logical_relation(prop1, prop2):
            if existing_relation.relation_type == "equivalence":
                logger.info(f"Equivalence relation between '{prop1}' and '{prop2}' already exists.")
                return
        if self.are_equivalent(prop1, prop2):
            logger.info(
                f"Propositions '{prop1}' and '{prop2}' are already equivalent via transitive relation. Will declare direct equivalence relation nonetheless."
            )

        relation = LogicalRelation(_type="equivalence")
        self.proposition_graph.add_edge(prop1, prop2, **relation.model_dump(by_alias=True))

    def add_negation(self, prop1: PropositionID, prop2: PropositionID) -> None:
        """Add a negation relation."""
        if self.are_equivalent(prop1, prop2):
            raise ValueError(
                f"Cannot add negation relation between equivalent propositions {prop1} and {prop2}."
            )
        if existing_relation := self.get_logical_relation(prop1, prop2):
            if existing_relation.relation_type == "negation":
                logger.info(f"Negation relation between '{prop1}' and '{prop2}' already exists.")
                return
        if self.are_contradictory(prop1, prop2):
            logger.info(
                f"Propositions '{prop1}' and '{prop2}' are already contradictory via transitive relation. Will declare direct negation relation nonetheless."
            )

        relation = LogicalRelation(_type="negation")
        self.proposition_graph.add_edge(prop1, prop2, **relation.model_dump(by_alias=True))

    def remove_equivalence(self, prop1: PropositionID, prop2: PropositionID) -> None:
        """Removes all equivalence relations between prop1 and any proposition q that is equivalent to prop2."""
        equiv_graph: nx.Graph[PropositionID] = self._get_equivalence_graph()
        equivs2 = nx.node_connected_component(equiv_graph, prop2)

        for q in equivs2 | {prop2}:
            if self.proposition_graph.has_edge(prop1, q):
                if self.proposition_graph.edges[prop1, q]["_type"] == "equivalence":
                    self.proposition_graph.remove_edge(prop1, q)

    def remove_negation(self, prop1: PropositionID, prop2: PropositionID) -> None:
        """Removes all negation relations between any q equivalent to prop1 and any q equivalent to prop2."""
        equiv_graph: nx.Graph[PropositionID] = self._get_equivalence_graph()
        equivs1 = nx.node_connected_component(equiv_graph, prop1)
        equivs2 = nx.node_connected_component(equiv_graph, prop2)

        for q1 in equivs1 | {prop1}:
            for q2 in equivs2 | {prop2}:
                if self.proposition_graph.has_edge(q1, q2):
                    if self.proposition_graph.edges[q1, q2]["_type"] == "negation":
                        self.proposition_graph.remove_edge(q1, q2)

    # === Query Operations ===

    def is_node(self, label: NodeLabel) -> bool:
        """Check if a node exists."""
        return self.argument_graph.has_node(label)

    def is_proposition(self, prop_id: PropositionID) -> bool:
        """Check if a proposition exists."""
        return self.proposition_graph.has_node(prop_id)

    def list_claims(self) -> List[ClaimNode]:
        """Get all claim nodes."""
        return [
            ClaimNode(**dict(self.argument_graph.nodes[n]))
            for n in self.argument_graph.nodes()
            if self.argument_graph.nodes[n]["_type"] == "claim"
        ]

    def list_arguments(self) -> List[ArgumentNode]:
        """Get all argument nodes."""
        return [
            ArgumentNode(**dict(self.argument_graph.nodes[n]))
            for n in self.argument_graph.nodes()
            if self.argument_graph.nodes[n]["_type"] == "argument"
        ]
    
    def list_roots(self) -> List[NodeLabel]:
        """Get all root nodes (nodes with no incoming edges)."""
        return [n for n in self.argument_graph.nodes() if self.argument_graph.out_degree(n) == 0]

    def get_supporters(self, label: NodeLabel) -> List[NodeLabel]:
        """Get nodes that support this node."""
        return [
            u
            for u in self.argument_graph.predecessors(label)
            if self.argument_graph.edges[u, label]["_type"] == "support"
        ]

    def get_supported(self, label: NodeLabel) -> List[NodeLabel]:
        """Get nodes that this node supports."""
        return [
            v
            for v in self.argument_graph.successors(label)
            if self.argument_graph.edges[label, v]["_type"] == "support"
        ]

    def get_attackers(self, label: NodeLabel) -> List[NodeLabel]:
        """Get nodes that attack this node."""
        return [
            u
            for u in self.argument_graph.predecessors(label)
            if self.argument_graph.edges[u, label]["_type"] == "attack"
        ]

    def get_attacked(self, label: NodeLabel) -> List[NodeLabel]:
        """Get nodes that this node attacks."""
        return [
            v
            for v in self.argument_graph.successors(label)
            if self.argument_graph.edges[label, v]["_type"] == "attack"
        ]
    
    def get_k_neighborhood(self, label: NodeLabel, k: int) -> List[NodeLabel]:
        """Get k-neighborhood of a node (all nodes within distance k, including the node itself)."""
        return list(nx.single_source_shortest_path_length(
            self.argument_graph.to_undirected(), label, cutoff=k
        ).keys())

    def get_negation_of(self, prop_id: PropositionID) -> Iterator[Proposition]:
        """Get propositions that are negations of the given proposition."""
        for neighbor in self.proposition_graph.neighbors(prop_id):
            if self.proposition_graph.edges[prop_id, neighbor]["_type"] == "negation":
                data = dict(self.proposition_graph.nodes[prop_id])
                yield Proposition(**data)

    def connected_components(self) -> List[List[NodeLabel]]:
        """Get weakly connected components of the argument graph."""
        return [list(c) for c in nx.weakly_connected_components(self.argument_graph)]

    def find_proposition_by_content(self, content: str) -> Iterator[Proposition]:
        """Get propositions by content."""
        for node in self.proposition_graph.nodes:
            data = dict(self.proposition_graph.nodes[node])
            proposition = Proposition(**data)
            if proposition.content == content:
                yield proposition

    def is_acyclic(self) -> bool:
        """Check if the argument graph is acyclic."""
        return nx.is_directed_acyclic_graph(self.argument_graph)

    def longest_path(self) -> List[NodeLabel]:
        """Get the longest simple path in the argument graph.
        
        A simple path is a path with no repeated nodes. For directed acyclic graphs,
        this uses an efficient algorithm. For graphs with cycles, this enumerates
        all simple paths between all node pairs, which may be slow for large graphs.
        
        Returns:
            The longest simple path as a list of node labels, or an empty list if
            the graph has no nodes.
        """
        if not self.argument_graph.nodes():
            return []
        
        # For DAGs, use the efficient algorithm
        if self.is_acyclic():
            return nx.dag_longest_path(self.argument_graph)
        
        # For graphs with cycles, find longest simple path by checking all pairs
        longest_path: List[NodeLabel] = []
        nodes = list(self.argument_graph.nodes())
        
        for source in nodes:
            for target in nodes:
                # Find all simple paths from source to target
                try:
                    for path in nx.all_simple_paths(self.argument_graph, source, target):
                        if len(path) > len(longest_path):
                            longest_path = path
                except nx.NetworkXNoPath:
                    continue
        
        return longest_path

    # === Analytics ===

    def get_central_nodes(self, k: int = 5) -> List[tuple[str, float]]:
        """Get most central nodes by degree centrality."""
        centrality = nx.degree_centrality(self.argument_graph)
        return sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:k]

    def get_connected_components(self) -> int:
        """Get number of weakly connected components."""
        return nx.number_weakly_connected_components(self.argument_graph)

    # === Utils ===

    def is_unique_label(self, label: str) -> bool:
        """Check if a node label is unique."""
        return label not in self.argument_graph.nodes

    def maybe_make_unique_label(self, label: str) -> str:
        """Return a unique label by appending suffix if needed."""
        if self.is_unique_label(label):
            return label
        # check if label has int suffix and extract base
        match = re.match(r"^(.*)_(\d+)$", label)
        if match:
            original_base_label = match.group(1)
            counter = int(match.group(2)) + 1
        else:
            original_base_label = label
            counter = 1
        while not self.is_unique_label(label):
            label = f"{original_base_label}_{counter}"
            counter += 1
        return label

    def is_proposition_used(self, prop_id: PropositionID) -> bool:
        """Check if proposition is referenced by any node."""
        for node_label in self.argument_graph.nodes:
            node = self.get_node(node_label)
            if isinstance(node, ClaimNode):
                if node.proposition_id == prop_id:
                    return True
            elif isinstance(node, ArgumentNode):
                if node.conclusion == prop_id or prop_id in node.premises:
                    return True
        return False

    def maybe_remove_unused_proposition(self, prop_id: PropositionID) -> None:
        """Remove proposition if not referenced by any node."""
        if not self.is_proposition_used(prop_id):
            self.delete_proposition(prop_id)

    def _get_equivalence_graph(self) -> nx.Graph[PropositionID]:
        """Get equivalence graph."""
        equiv_graph: nx.Graph[PropositionID] = nx.Graph()
        for u, v, data in self.proposition_graph.edges(data=True):
            if data["_type"] == "equivalence":
                equiv_graph.add_edge(u, v)
        return equiv_graph

    def negate_proposition_content(self, content: str) -> str:
        """Generate negated proposition content."""
        # Simple heuristic for negation
        if content.lower().startswith("it is not the case that"):
            return content[len("It is not the case that ") :]
        elif content.lower().startswith("not "):
            return content[len("Not ") :]
        elif content.lower().startswith("not:"):
            return content[len("Not: ") :]
        else:
            return f"It is not the case that {content}"

    # === Serialization ===

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "argument_graph": nx.node_link_data(self.argument_graph),
            "proposition_graph": nx.node_link_data(self.proposition_graph),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArgumentMap":
        """Deserialize from dictionary."""
        map = cls()
        map.argument_graph = nx.node_link_graph(data["argument_graph"])
        map.proposition_graph = nx.node_link_graph(data["proposition_graph"])
        return map
