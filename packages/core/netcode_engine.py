import json
from typing import Dict, Any, List
from datetime import datetime
from packages.core.models import StateDelta

class NetcodeEngine:
    """
    The Math Diffing Engine. 
    Calculates exactly what changed between two states to save massive bandwidth.
    We reject the Old Paradigm of sending the whole world; we only send the Delta.
    """

    @staticmethod
    def calculate_delta(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> StateDelta:
        """
        Takes the old JSON dictionary and the new JSON dictionary.
        Returns a pure Pydantic StateDelta object containing only the differences.
        """
        # 1. Initialize our empty buckets for the differences
        changed_nodes = []
        removed_node_ids = []
        changed_tokens = {}

        # Extract nodes from both states. If they don't exist, default to empty lists.
        old_nodes_list = old_state.get('nodes', [])
        new_nodes_list = new_state.get('nodes', [])

        # Convert lists to dictionaries with the 'id' as the key for lightning-fast math lookups
        old_nodes_dict = {node['id']: node for node in old_nodes_list if 'id' in node}
        new_nodes_dict = {node['id']: node for node in new_nodes_list if 'id' in node}

        # 2. DIFFING THE NODES (What was added? What was modified?)
        for node_id, new_node in new_nodes_dict.items():
            if node_id not in old_nodes_dict:
                # This node is brand new! Add it to the delta.
                changed_nodes.append(new_node)
            elif old_nodes_dict[node_id] != new_node:
                # This node existed, but its data changed (e.g., a door opened, health dropped).
                # We only send the new version of the node.
                changed_nodes.append(new_node)

        # 3. DIFFING THE REMOVALS (What was deleted?)
        for node_id in old_nodes_dict:
            if node_id not in new_nodes_dict:
                # This node was in the old state but is gone in the new state.
                removed_node_ids.append(node_id)

        # 4. DIFFING THE WORLD TOKENS (What environmental variables changed?)
        # We look inside the 'world_state' or 'extra_attributes' bucket.
        old_tokens = old_state.get('world_state', {})
        new_tokens = new_state.get('world_state', {})

        for key, value in new_tokens.items():
            if old_tokens.get(key) != value:
                # The heat level changed, or the time of day shifted. Record it.
                changed_tokens[key] = value

        # 5. ASSEMBLE THE DNA
        # We pack all our mathematical findings into our strict Pydantic StateDelta model.
        delta = StateDelta(
            timestamp=datetime.utcnow(),
            changed_nodes=changed_nodes,
            changed_tokens=changed_tokens,
            removed_node_ids=removed_node_ids
        )

        return delta

    @staticmethod
    def apply_delta_to_state(current_state: Dict[str, Any], delta: StateDelta) -> Dict[str, Any]:
        """
        The Client-Side Math: Takes the current state and applies the Delta to it deterministically.
        This is how the receiving players update their screens without reloading!
        """
        # We make a copy so we don't mutate the original memory directly
        updated_state = current_state.copy()
        
        # Ensure lists/dicts exist
        if 'nodes' not in updated_state:
            updated_state['nodes'] = []
        if 'world_state' not in updated_state:
            updated_state['world_state'] = {}

        # 1. Apply removed nodes
        updated_state['nodes'] = [
            node for node in updated_state['nodes'] 
            if node.get('id') not in delta.removed_node_ids
        ]

        # 2. Apply changed/new nodes
        node_map = {node.get('id'): node for node in updated_state['nodes']}
        for changed_node in delta.changed_nodes:
            node_map[changed_node['id']] = changed_node
        updated_state['nodes'] = list(node_map.values())

        # 3. Apply changed tokens
        for key, value in delta.changed_tokens.items():
            updated_state['world_state'][key] = value

        return updated_state