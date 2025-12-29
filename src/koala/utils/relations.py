
from koala.graph import ArgumentMap
from koala.models import ClaimNode, NodeLabel
from koala.models.relations import DialecticalRelationType


def has_grounding(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
) -> bool:
    """Check if a (hypothetical) relation were grounded.
    
    Args:
        from_label: Source node label
        to_label: Target node label
        relation_type: Type of relation ('support' or 'attack')
        arg_map: The argument map
        
    Returns:
        True if the relation is grounded, False otherwise
    """
    source_node = arg_map.get_node(from_label)
    target_node = arg_map.get_node(to_label)
    source_prop_id = (
        source_node.proposition_id if isinstance(source_node, ClaimNode) else source_node.conclusion
    )
    target_prop_ids = (
        [target_node.proposition_id] if isinstance(target_node, ClaimNode) else target_node.premises
    )


    if not source_prop_id:
        return False

    if relation_type == "support":
        return any(arg_map.are_equivalent(source_prop_id, pid) for pid in target_prop_ids if pid)
    elif relation_type == "attack":
        return any(arg_map.are_contradictory(source_prop_id, pid) for pid in target_prop_ids if pid)
    else:
        return False


def is_grounded_relation(
    from_label: NodeLabel,
    to_label: NodeLabel,
    relation_type: DialecticalRelationType,
    arg_map: ArgumentMap,
) -> bool:
    """Check if a dialectical relation is grounded.
    
    Args:
        from_label: Source node label
        to_label: Target node label
        relation_type: Type of relation ('support' or 'attack')
        arg_map: The argument map
        
    Returns:
        True if the relation is grounded, False otherwise
    """
    rel = arg_map.get_dialectic_relation(from_label, to_label)
    if rel is None:
        return False
    return has_grounding(from_label, to_label, relation_type, arg_map)

