import logging
from copy import deepcopy
from packages.core.models import WorldState, ModDNA, OntologicalNode, DramaBudget

logger = logging.getLogger(__name__)

class SafeInjectionEngine:
    def __init__(self):
        # The DNA Sanitizer Rules (Day 22 logic adapted for Mods)
        # We define a list of "forbidden" concepts that shouldn't appear in a safe JSON mod.
        self.restricted_keywords = ["lua", "script", "eval", "exec", "system", "rm -rf", "javascript"]

    def _sanitize_mod(self, mod: ModDNA, world: WorldState, budget: DramaBudget) -> bool:
        """
        The Bouncer. Checks if the mod respects the laws of our universe.
        """
        # 1. Check Drama Budget (Performance Safety)
        # If adding this mod pushes us over the limit, we reject it to save the i3 laptop.
        current_entities = len(world.nodes)
        added_entities = len(mod.injected_nodes)
        if current_entities + added_entities > budget.max_entities:
            logger.warning(f"Mod {mod.mod_name} REJECTED: Exceeds Drama Budget (Max Entities).")
            return False

        # 2. Check Security (Content Safety)
        # We scan the tags and names for forbidden concepts.
        for node in mod.injected_nodes:
            # Check Tags
            for tag in node.get("semantic_tags", []):
                if any(keyword in tag.lower() for keyword in self.restricted_keywords):
                    logger.warning(f"Mod {mod.mod_name} REJECTED: Forbidden tag detected ({tag}).")
                    return False
            
            # Check Node ID (Prevent overwriting core nodes)
            # We ensure the mod isn't trying to spoof a core system node ID.
            if node.get("node_id") in ["core_player", "system_camera", "main_light"]:
                 logger.warning(f"Mod {mod.mod_name} REJECTED: Attempted to overwrite core system node.")
                 return False

        return True

    def inject_mod(self, world_state: WorldState, mod: ModDNA, budget: DramaBudget) -> WorldState:
        """
        The Merger. Deterministically combines the new DNA with the existing World.
        """
        logger.info(f"Initiating Safe Injection for: {mod.mod_name}")

        # Step 1: Sanitize
        if not self._sanitize_mod(mod, world_state, budget):
            raise ValueError(f"Injection Failed: Mod '{mod.mod_name}' failed safety checks.")

        # Step 2: Deep Copy (Immutability)
        # We NEVER touch the original WorldState directly. 
        # We create a clone, modify the clone, and return it.
        # This prevents accidental corruption if something goes wrong halfway through.
        new_world = deepcopy(world_state)

        # Step 3: Merge
        for node_dict in mod.injected_nodes:
            try:
                # We force the raw JSON dict to become a strict Pydantic Object.
                # If the mod creator made a mistake (e.g., sent a string instead of a number),
                # Pydantic catches it here and prevents a crash.
                new_node = OntologicalNode(**node_dict)
                new_world.nodes.append(new_node)
                logger.info(f"Successfully injected node: {new_node.node_id}")
            except Exception as e:
                # If a single node is bad, we log it and skip it, but we don't crash the whole app.
                logger.error(f"Skipped invalid node in mod {mod.mod_name}: {e}")
                continue

        logger.info(f"Injection Complete. World now has {len(new_world.nodes)} nodes.")
        return new_world

# Singleton instance for easy access
engine = SafeInjectionEngine()