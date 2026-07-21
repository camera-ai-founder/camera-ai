# packages/core/social_engine.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

try:
    from .models import (
        SocialDNA,
        SocialAction,
        FactionDNA,
        RelationshipTensor,
        SocialRule,
    )
except ImportError:
    from models import (
        SocialDNA,
        SocialAction,
        FactionDNA,
        RelationshipTensor,
        SocialRule,
    )


class SocialMatrixEngine:
    """
    The Deterministic Social Matrix and Ripple Resolver.

    This engine stores society as a weighted mathematical graph.

    Entities can be:
    - factions
    - NPCs
    - guilds
    - cities
    - the player

    Relationship weights:
    -1.0 = hostility / hatred
     0.0 = neutral
    +1.0 = alliance / deep trust

    This engine does NOT hardcode reputation.
    It computes disposition from the mathematical web.

    When a SocialAction occurs, the engine mathematically propagates
    that action through direct and indirect relationship paths.
    """

    def __init__(
        self,
        social_dna: Optional[SocialDNA] = None,
        player_id: str = "player",
        propagation_strength: float = 0.75,
        indirect_decay: float = 0.5,
        refusal_threshold: float = -0.5,
        alliance_threshold: float = 0.6,
    ):
        self.player_id: str = str(player_id).strip() or "player"

        self.propagation_strength: float = self._clamp_confidence(propagation_strength)
        self.indirect_decay: float = self._clamp_confidence(indirect_decay)

        self.refusal_threshold: float = self._clamp_weight(refusal_threshold)
        self.alliance_threshold: float = self._clamp_weight(alliance_threshold)

        self._entities: Set[str] = set()
        self._faction_ids: Set[str] = set()
        self._factions: Dict[str, FactionDNA] = {}
        self._social_rules: List[SocialRule] = []

        # _weights[source_id][target_id] = float weight
        self._weights: Dict[str, Dict[str, float]] = {}

        # _edge_meta[source_id][target_id] = metadata dictionary
        self._edge_meta: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # _interaction_blocks[source_id] = set of target IDs refused by source
        self._interaction_blocks: Dict[str, Set[str]] = {}

        if social_dna is not None:
            self.load_dna(social_dna)
        else:
            self._ensure_entity(self.player_id)
            self._recompute_interaction_blocks()

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================

    @staticmethod
    def _clamp_weight(weight: float) -> float:
        """
        Keep relationship weights safely between -1.0 and +1.0.
        """
        return max(-1.0, min(1.0, float(weight)))

    @staticmethod
    def _clamp_confidence(confidence: float) -> float:
        """
        Keep confidence safely between 0.0 and 1.0.
        """
        return max(0.0, min(1.0, float(confidence)))

    def _ensure_entity(self, entity_id: str) -> str:
        """
        Make sure an entity exists inside the matrix.

        An entity can be a faction, NPC, guild, city, or player.
        """
        entity_id = str(entity_id).strip()

        if not entity_id:
            raise ValueError("Entity ID cannot be empty.")

        if entity_id not in self._entities:
            self._entities.add(entity_id)
            self._weights.setdefault(entity_id, {})
            self._edge_meta.setdefault(entity_id, {})
            self._interaction_blocks.setdefault(entity_id, set())

            # Every entity has a perfect relationship with itself.
            self._weights[entity_id][entity_id] = 1.0
            self._edge_meta[entity_id][entity_id] = {
                "relationship_type": "identity",
                "confidence": 1.0,
                "notes": "Self relationship is always stable.",
            }

        return entity_id

    @staticmethod
    def _action_payload(action: SocialAction) -> Dict[str, Any]:
        """
        Safely convert a SocialAction into a dictionary for reports.
        """
        try:
            payload = action.model_dump()
        except AttributeError:
            payload = action.dict()

        timestamp = payload.get("timestamp")
        if hasattr(timestamp, "isoformat"):
            payload["timestamp"] = timestamp.isoformat()

        return payload

    # ======================================================
    # DNA LOADING
    # ======================================================

    def reset(self) -> None:
        """
        Clear the entire social matrix.
        """
        self._entities.clear()
        self._faction_ids.clear()
        self._factions.clear()
        self._social_rules.clear()
        self._weights.clear()
        self._edge_meta.clear()
        self._interaction_blocks.clear()

    def load_dna(self, social_dna: SocialDNA) -> None:
        """
        Load a SocialDNA structure into the mathematical matrix.
        """
        self.reset()

        for faction in social_dna.factions:
            self.add_faction(faction)

        for relationship in social_dna.relationship_tensors:
            self.set_relationship(
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                weight=relationship.weight,
                relationship_type=relationship.relationship_type,
                confidence=relationship.confidence,
                notes=relationship.notes,
                metadata=relationship.metadata,
            )

        self._social_rules = list(social_dna.social_rules)

        self._ensure_entity(self.player_id)
        self._sync_faction_player_dispositions()
        self._recompute_interaction_blocks()

    def to_social_dna(self) -> SocialDNA:
        """
        Convert the living mathematical matrix back into SocialDNA.
        """
        relationship_tensors: List[RelationshipTensor] = []

        for source_id in sorted(self._weights.keys()):
            for target_id in sorted(self._weights[source_id].keys()):
                # Skip self-relationships because they are automatic.
                if source_id == target_id:
                    continue

                meta = self.get_relationship_meta(source_id, target_id)

                relationship_tensors.append(
                    RelationshipTensor(
                        source_id=source_id,
                        target_id=target_id,
                        weight=self.get_relationship(source_id, target_id),
                        relationship_type=meta.get("relationship_type", "neutral"),
                        confidence=float(meta.get("confidence", 1.0)),
                        notes=str(meta.get("notes", "")),
                        metadata=meta.get("metadata", {}),
                    )
                )

        return SocialDNA(
            factions=list(self._factions.values()),
            relationship_tensors=relationship_tensors,
            social_rules=list(self._social_rules),
            metadata={
                "entity_count": len(self._entities),
                "faction_count": len(self._faction_ids),
                "player_id": self.player_id,
                "interaction_blocks": self.get_interaction_blocks(),
            },
        )

    # ======================================================
    # ENTITY + FACTION MANAGEMENT
    # ======================================================

    def add_entity(self, entity_id: str) -> str:
        """
        Add a non-faction entity, such as an NPC or the player.
        """
        return self._ensure_entity(entity_id)

    def add_faction(self, faction: FactionDNA) -> str:
        """
        Add a faction to the social matrix.
        """
        faction_id = self._ensure_entity(faction.faction_id)
        self._faction_ids.add(faction_id)
        self._factions[faction_id] = faction

        # Keep the player present so faction-to-player disposition can exist.
        self._ensure_entity(self.player_id)

        # If the faction already has an initial disposition toward the player,
        # express it as a mathematical relationship edge.
        if float(faction.disposition_toward_player) != 0.0:
            self.set_relationship(
                source_id=faction_id,
                target_id=self.player_id,
                weight=float(faction.disposition_toward_player),
                relationship_type="player_disposition",
                confidence=1.0,
                notes="Initial faction disposition toward player.",
            )

        return faction_id

    def get_entity_ids(self) -> List[str]:
        """
        Return all entity IDs in deterministic sorted order.
        """
        return sorted(self._entities)

    def get_faction_ids(self) -> List[str]:
        """
        Return all faction IDs in deterministic sorted order.
        """
        return sorted(self._faction_ids)

    def get_faction(self, faction_id: str) -> Optional[FactionDNA]:
        """
        Get a faction by ID.
        """
        return self._factions.get(str(faction_id).strip())

    def set_player_id(self, player_id: str) -> None:
        """
        Set the canonical player entity ID.
        """
        self.player_id = str(player_id).strip() or "player"
        self._ensure_entity(self.player_id)
        self._sync_faction_player_dispositions()
        self._recompute_interaction_blocks()

    # ======================================================
    # RELATIONSHIP MANAGEMENT
    # ======================================================

    def set_relationship(
        self,
        source_id: str,
        target_id: str,
        weight: float,
        relationship_type: str = "neutral",
        confidence: float = 1.0,
        notes: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set a directed relationship weight from source to target.

        Example:
        source_id = "faction_merchants"
        target_id = "faction_thieves"
        weight = -0.8
        relationship_type = "rivalry"
        """
        source_id = self._ensure_entity(source_id)
        target_id = self._ensure_entity(target_id)

        old_meta = self.get_relationship_meta(source_id, target_id)
        old_metadata: Dict[str, Any] = dict(old_meta.get("metadata", {}))

        if metadata is not None:
            old_metadata.update(metadata)

        # Self-relationship is always stable.
        if source_id == target_id:
            weight = 1.0
            relationship_type = "identity"
            confidence = 1.0
            notes = "Self relationship is always stable."

        weight = self._clamp_weight(weight)
        confidence = self._clamp_confidence(confidence)

        self._weights[source_id][target_id] = weight

        edge_meta: Dict[str, Any] = {
            "relationship_type": str(relationship_type),
            "confidence": confidence,
            "notes": str(notes),
        }

        if old_metadata:
            edge_meta["metadata"] = old_metadata

        self._edge_meta[source_id][target_id] = edge_meta

    def get_relationship(self, source_id: str, target_id: str) -> float:
        """
        Get the relationship weight from source to target.

        If no relationship exists, return 0.0 (neutral).
        """
        source_id = str(source_id).strip()
        target_id = str(target_id).strip()

        if source_id not in self._weights:
            return 0.0

        return float(self._weights[source_id].get(target_id, 0.0))

    def get_relationship_meta(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        Get metadata for a relationship edge.
        """
        source_id = str(source_id).strip()
        target_id = str(target_id).strip()

        if source_id not in self._edge_meta:
            return {
                "relationship_type": "neutral",
                "confidence": 0.0,
                "notes": "",
            }

        return dict(self._edge_meta[source_id].get(target_id, {}))

    def get_outgoing_relationships(self, entity_id: str) -> Dict[str, float]:
        """
        Get all relationships from this entity to others.
        """
        entity_id = str(entity_id).strip()

        if entity_id not in self._weights:
            return {}

        return dict(self._weights[entity_id])

    def get_incoming_relationships(self, entity_id: str) -> Dict[str, float]:
        """
        Get all relationships from others toward this entity.
        """
        entity_id = str(entity_id).strip()
        incoming: Dict[str, float] = {}

        for source_id, targets in self._weights.items():
            if entity_id in targets:
                incoming[source_id] = float(targets[entity_id])

        return incoming

    # ======================================================
    # MATRIX VIEWS
    # ======================================================

    def get_edges(self) -> List[Dict[str, Any]]:
        """
        Return all relationship edges as simple dictionaries.
        """
        edges: List[Dict[str, Any]] = []

        for source_id in sorted(self._weights.keys()):
            for target_id in sorted(self._weights[source_id].keys()):
                if source_id == target_id:
                    continue

                meta = self.get_relationship_meta(source_id, target_id)

                edges.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "weight": self.get_relationship(source_id, target_id),
                        "relationship_type": meta.get("relationship_type", "neutral"),
                        "confidence": meta.get("confidence", 1.0),
                        "notes": meta.get("notes", ""),
                    }
                )

        return edges

    def get_dense_matrix(self) -> Dict[str, Any]:
        """
        Return the social matrix as a deterministic 2D grid.

        This is useful for debugging, visualization, and math.
        """
        entity_ids = self.get_entity_ids()
        matrix: List[List[float]] = []

        for source_id in entity_ids:
            row: List[float] = []

            for target_id in entity_ids:
                row.append(self.get_relationship(source_id, target_id))

            matrix.append(row)

        return {
            "entities": entity_ids,
            "matrix": matrix,
        }

    def summary(self) -> Dict[str, Any]:
        """
        Return a lightweight summary of the social matrix.
        """
        block_count = 0

        for targets in self._interaction_blocks.values():
            block_count += len(targets)

        return {
            "entity_count": len(self._entities),
            "faction_count": len(self._faction_ids),
            "edge_count": len(self.get_edges()),
            "interaction_block_count": block_count,
            "faction_ids": self.get_faction_ids(),
            "player_id": self.player_id,
        }

    def describe(self) -> str:
        """
        Return a simple human-readable description.
        """
        lines: List[str] = []
        lines.append("Social Matrix Engine")
        lines.append(f"Entities: {len(self._entities)}")
        lines.append(f"Factions: {len(self._faction_ids)}")
        lines.append("")

        edges = self.get_edges()

        if not edges:
            lines.append("No social relationships have been defined yet.")
        else:
            lines.append("Relationships:")

            for edge in edges:
                source = edge["source_id"]
                target = edge["target_id"]
                weight = edge["weight"]
                relationship_type = edge["relationship_type"]

                lines.append(
                    f"- {source} -> {target} | weight={weight:.2f} | type={relationship_type}"
                )

        blocks = self.get_interaction_blocks()

        if blocks:
            lines.append("")
            lines.append("Interaction Refusals:")

            for source_id, target_ids in blocks.items():
                for target_id in target_ids:
                    lines.append(f"- {source_id} refuses interaction with {target_id}")

        return "\n".join(lines)

    # ======================================================
    # RIPPLE RESOLVER
    # ======================================================

    def apply_action(self, action: SocialAction) -> Dict[str, Any]:
        """
        Apply a SocialAction to the matrix and mutate reality.

        This is the deterministic consequence engine.
        """
        return self._compute_ripple(action=action, mutate=True)

    def simulate_action(self, action: SocialAction) -> Dict[str, Any]:
        """
        Simulate a SocialAction without mutating the matrix.
        """
        return self._compute_ripple(action=action, mutate=False)

    def _compute_ripple(self, action: SocialAction, mutate: bool) -> Dict[str, Any]:
        """
        Compute the mathematical ripple of a SocialAction.

        Direct effect:
        target -> actor changes by action.magnitude.

        Indirect effect:
        Every observer is influenced through direct and indirect paths
        to the target.

        Example:
        If Faction B hates Faction A,
        and the player helps Faction A,
        then Faction B's disposition toward the player drops.

        If NPC Ivan is allied with Faction B,
        Ivan may also turn against the player.
        """
        if mutate:
            actor_id = self._ensure_entity(action.actor_id)
            target_id = self._ensure_entity(action.target_id)
        else:
            actor_id = str(action.actor_id).strip()
            target_id = str(action.target_id).strip()

        magnitude = float(action.magnitude)

        report: Dict[str, Any] = {
            "action": self._action_payload(action),
            "mutated": mutate,
            "direct_effects": [],
            "ripple_effects": [],
            "interaction_blocks": [],
            "summary": {},
        }

        if not actor_id or not target_id:
            report["error"] = "SocialAction requires both actor_id and target_id."
            return report

        # ==================================================
        # DIRECT EFFECT
        # ==================================================
        old_direct_weight = self.get_relationship(target_id, actor_id)
        direct_delta = magnitude
        new_direct_weight = self._clamp_weight(old_direct_weight + direct_delta)

        direct_effect = {
            "source_id": target_id,
            "target_id": actor_id,
            "old_weight": old_direct_weight,
            "delta": direct_delta,
            "new_weight": new_direct_weight,
            "reason": f"Direct result of {action.action_type}",
        }

        report["direct_effects"].append(direct_effect)

        if mutate and actor_id != target_id:
            direct_meta = self.get_relationship_meta(target_id, actor_id)
            direct_type = str(action.action_type or direct_meta.get("relationship_type", "social_action"))

            self.set_relationship(
                source_id=target_id,
                target_id=actor_id,
                weight=new_direct_weight,
                relationship_type=direct_type,
                confidence=float(direct_meta.get("confidence", 1.0)),
                notes=f"Direct result of {action.action_type}.",
            )

        # Self-actions do not ripple through society.
        if actor_id == target_id:
            if mutate:
                self._sync_faction_player_dispositions()
                self._recompute_interaction_blocks()
                report["interaction_blocks"] = self.get_interaction_blocks()
                report["summary"] = self.summary()

            return report

        # ==================================================
        # INDIRECT RIPPLE EFFECTS
        # ==================================================
        entity_ids = self.get_entity_ids()

        # In simulation mode, actor/target may not yet exist in the matrix.
        if actor_id not in entity_ids:
            entity_ids.append(actor_id)
            entity_ids = sorted(entity_ids)

        if target_id not in entity_ids:
            entity_ids.append(target_id)
            entity_ids = sorted(entity_ids)

        for observer_id in entity_ids:
            if observer_id == actor_id or observer_id == target_id:
                continue

            influence_score = self._influence_score(
                observer_id=observer_id,
                target_id=target_id,
                entity_ids=entity_ids,
            )

            if abs(influence_score) < 0.0001:
                continue

            rule_multiplier = self._rule_multiplier(
                action=action,
                observer_id=observer_id,
                target_id=target_id,
            )

            delta = (
                magnitude
                * influence_score
                * self.propagation_strength
                * rule_multiplier
            )

            if abs(delta) < 0.0001:
                continue

            old_weight = self.get_relationship(observer_id, actor_id)
            new_weight = self._clamp_weight(old_weight + delta)

            ripple_effect = {
                "source_id": observer_id,
                "target_id": actor_id,
                "influence_score": influence_score,
                "rule_multiplier": rule_multiplier,
                "old_weight": old_weight,
                "delta": delta,
                "new_weight": new_weight,
                "reason": (
                    f"Ripple from {action.action_type} on {target_id} "
                    f"through social path to {observer_id}"
                ),
            }

            report["ripple_effects"].append(ripple_effect)

            if mutate:
                old_meta = self.get_relationship_meta(observer_id, actor_id)
                existing_type = str(old_meta.get("relationship_type", "neutral"))

                if existing_type in ("", "neutral", "identity"):
                    existing_type = "ripple"

                self.set_relationship(
                    source_id=observer_id,
                    target_id=actor_id,
                    weight=new_weight,
                    relationship_type=existing_type,
                    confidence=float(old_meta.get("confidence", 0.8)),
                    notes=f"Ripple from {action.action_type} on {target_id}.",
                )

        if mutate:
            self._sync_faction_player_dispositions()
            self._recompute_interaction_blocks()
            report["interaction_blocks"] = self.get_interaction_blocks()
            report["summary"] = self.summary()

        return report

    def _influence_score(
        self,
        observer_id: str,
        target_id: str,
        entity_ids: List[str],
    ) -> float:
        """
        Calculate how strongly an observer cares about an action against target.

        This uses:
        1. Direct path:
           observer -> target

        2. Indirect path through one intermediate entity:
           observer -> intermediate -> target

        Example:
        NPC Ivan -> Faction B = +0.8
        Faction B -> Faction A = -0.8

        If player helps Faction A,
        Ivan's indirect influence is positive alliance with Faction B
        multiplied by Faction B's hatred of Faction A.

        Ivan therefore dislikes the player's action.
        """
        direct_influence = self.get_relationship(observer_id, target_id)

        indirect_influence = 0.0

        for intermediate_id in entity_ids:
            if intermediate_id == observer_id or intermediate_id == target_id:
                continue

            observer_to_intermediate = self.get_relationship(observer_id, intermediate_id)
            intermediate_to_target = self.get_relationship(intermediate_id, target_id)

            if abs(observer_to_intermediate) < 0.0001:
                continue

            if abs(intermediate_to_target) < 0.0001:
                continue

            indirect_influence += observer_to_intermediate * intermediate_to_target

        influence_score = direct_influence + (indirect_influence * self.indirect_decay)

        return self._clamp_weight(influence_score)

    def _rule_multiplier(
        self,
        action: SocialAction,
        observer_id: str,
        target_id: str,
    ) -> float:
        """
        Apply SocialRule multipliers deterministically.

        Rules can amplify or dampen ripples.
        """
        multiplier = 1.0

        for rule in self._social_rules:
            trigger = str(rule.trigger_action or "*")

            if trigger != "*" and trigger != str(action.action_type):
                continue

            if rule.source_faction_id and str(rule.source_faction_id) != str(observer_id):
                continue

            if rule.target_faction_id and str(rule.target_faction_id) != str(target_id):
                continue

            multiplier *= float(rule.magnitude_multiplier)

        # Keep rules from creating chaotic infinite escalation.
        return max(-5.0, min(5.0, multiplier))

    # ======================================================
    # INTERACTION REFUSAL LOGIC
    # ======================================================

    def _sync_faction_player_dispositions(self) -> None:
        """
        Keep FactionDNA.disposition_toward_player synchronized with the matrix.
        """
        for faction_id in self._faction_ids:
            faction = self._factions.get(faction_id)

            if faction is None:
                continue

            faction.disposition_toward_player = self.get_relationship(
                faction_id,
                self.player_id,
            )

    def _recompute_interaction_blocks(self) -> None:
        """
        Recompute who refuses interaction with whom.

        This is deterministic and derived entirely from the matrix.
        """
        self._interaction_blocks = {
            entity_id: set() for entity_id in self._entities
        }

        entity_ids = self.get_entity_ids()

        for source_id in entity_ids:
            for target_id in entity_ids:
                if source_id == target_id:
                    continue

                if self._should_refuse(source_id, target_id):
                    self._interaction_blocks[source_id].add(target_id)

    def _should_refuse(self, source_id: str, target_id: str) -> bool:
        """
        Determine whether source refuses interaction with target.

        Refusal happens when:
        1. source directly dislikes target enough.
        2. source is allied with a faction that dislikes target enough.
        """
        direct_weight = self.get_relationship(source_id, target_id)

        if direct_weight <= self.refusal_threshold:
            return True

        for faction_id in self.get_faction_ids():
            if faction_id == source_id or faction_id == target_id:
                continue

            faction_to_target = self.get_relationship(faction_id, target_id)
            source_to_faction = self.get_relationship(source_id, faction_id)

            if (
                faction_to_target <= self.refusal_threshold
                and source_to_faction >= self.alliance_threshold
            ):
                return True

        return False

    def can_interact(self, source_id: str, target_id: str) -> bool:
        """
        Return True if interaction is allowed between two entities.

        Interaction is blocked if either entity refuses the other.
        """
        source_id = str(source_id).strip()
        target_id = str(target_id).strip()

        if source_id == target_id:
            return True

        if target_id in self._interaction_blocks.get(source_id, set()):
            return False

        if source_id in self._interaction_blocks.get(target_id, set()):
            return False

        return True

    def get_interaction_blocks(self) -> Dict[str, List[str]]:
        """
        Return all interaction refusals in deterministic sorted form.
        """
        blocks: Dict[str, List[str]] = {}

        for source_id in sorted(self._interaction_blocks.keys()):
            target_ids = sorted(self._interaction_blocks[source_id])

            if target_ids:
                blocks[source_id] = target_ids

        return blocks