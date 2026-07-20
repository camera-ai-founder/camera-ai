# packages/core/narrative_engine.py

from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict, deque

try:
    from .models import QuestDNA, NarrativeNode
except ImportError:
    from models import QuestDNA, NarrativeNode


class NarrativeEngine:
    """
    The Procedural Narrative Graph Engine.

    This engine treats story structure as mathematics.

    A quest is not a script.
    A quest is a directed graph of semantic nodes.

    Rules:
    - Story flow has direction.
    - Node A can unlock Node B.
    - Node B can unlock Node C.
    - Node C must never unlock Node A again.
    - If a circular loop exists, the quest is rejected.
    - When a node completes, deterministic World State mutations can fire.
    """

    # ==========================================================
    # DAY 32 STEP 2: DAG VALIDATOR
    # ==========================================================

    def validate_quest_dna(self, quest: QuestDNA) -> Dict[str, Any]:
        """
        Validate that a QuestDNA object is a safe Directed Acyclic Graph.
        """

        errors: List[str] = []
        node_ids: List[str] = []
        node_set: Set[str] = set()

        # --------------------------------------------------
        # 1. A quest must contain at least one narrative node.
        # --------------------------------------------------
        if not quest.nodes:
            errors.append("Quest has no narrative nodes.")
            return self._validation_failure(
                quest=quest,
                errors=errors,
                cycle_path=None
            )

        # --------------------------------------------------
        # 2. Collect node IDs and reject duplicates.
        # --------------------------------------------------
        for node in quest.nodes:
            if node.node_id in node_set:
                errors.append(f"Duplicate node_id detected: '{node.node_id}'.")
            else:
                node_set.add(node.node_id)
                node_ids.append(node.node_id)

        # --------------------------------------------------
        # 3. Validate that every edge references real nodes.
        # --------------------------------------------------
        for edge in quest.edges:
            if edge.from_node not in node_set:
                errors.append(
                    f"Edge references unknown from_node: '{edge.from_node}'."
                )

            if edge.to_node not in node_set:
                errors.append(
                    f"Edge references unknown to_node: '{edge.to_node}'."
                )

            if edge.from_node == edge.to_node:
                errors.append(
                    f"Self-loop detected on node: '{edge.from_node}'."
                )

        # If basic structural validation failed, stop here.
        if errors:
            return self._validation_failure(
                quest=quest,
                errors=errors,
                cycle_path=None
            )

        # --------------------------------------------------
        # 4. Build the directed graph.
        # --------------------------------------------------
        adjacency: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {
            node_id: 0 for node_id in node_ids
        }

        for edge in quest.edges:
            adjacency[edge.from_node].append(edge.to_node)
            indegree[edge.to_node] += 1

        # --------------------------------------------------
        # 5. Kahn's Algorithm for topological sorting.
        #
        # If we can visit every node exactly once,
        # the graph is a valid DAG.
        #
        # If we cannot visit every node,
        # a circular dependency exists.
        # --------------------------------------------------
        queue: deque = deque(
            [
                node_id
                for node_id in node_ids
                if indegree[node_id] == 0
            ]
        )

        topological_order: List[str] = []
        indegree_work: Dict[str, int] = indegree.copy()

        while queue:
            current_node = queue.popleft()
            topological_order.append(current_node)

            for next_node in adjacency[current_node]:
                indegree_work[next_node] -= 1

                if indegree_work[next_node] == 0:
                    queue.append(next_node)

        # --------------------------------------------------
        # 6. If not all nodes were visited, reject the loop.
        # --------------------------------------------------
        if len(topological_order) != len(node_ids):
            cycle_path = self._find_cycle_path(
                adjacency=adjacency,
                node_ids=node_ids
            )

            cycle_text = (
                " -> ".join(cycle_path)
                if cycle_path
                else "unknown circular dependency"
            )

            errors.append(
                f"Circular dependency detected: {cycle_text}"
            )

            return self._validation_failure(
                quest=quest,
                errors=errors,
                cycle_path=cycle_path
            )

        # --------------------------------------------------
        # 7. Success. The quest graph is mathematically safe.
        # --------------------------------------------------
        return {
            "is_valid": True,
            "errors": [],
            "cycle_path": None,
            "topological_order": topological_order,
            "node_count": len(node_ids),
            "edge_count": len(quest.edges),
            "reroll_prompt": None
        }

    def _validation_failure(
        self,
        quest: QuestDNA,
        errors: List[str],
        cycle_path: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Build a deterministic validation failure report.

        This report can be sent back to the Brain so Groq
        can re-roll a corrected QuestDNA.
        """

        reroll_prompt = (
            f"Regenerate QuestDNA '{quest.quest_id}'. "
            "It must be a valid Directed Acyclic Graph. "
            "Remove all circular dependencies. "
            "Only output semantic NarrativeNode objects and NarrativeEdge objects. "
            "Do not output raw dialogue. "
            "Do not output hardcoded scripts."
        )

        if cycle_path:
            reroll_prompt += (
                f" Rejected cycle: {' -> '.join(cycle_path)}."
            )

        return {
            "is_valid": False,
            "errors": errors,
            "cycle_path": cycle_path,
            "topological_order": [],
            "node_count": len(quest.nodes),
            "edge_count": len(quest.edges),
            "reroll_prompt": reroll_prompt
        }

    def _find_cycle_path(
        self,
        adjacency: Dict[str, List[str]],
        node_ids: List[str]
    ) -> List[str]:
        """
        Find one example circular path using DFS coloring.

        Colors:
        - WHITE = unvisited
        - GRAY = currently visiting
        - BLACK = finished

        If we find an edge to a GRAY node, we found a cycle.
        """

        WHITE = 0
        GRAY = 1
        BLACK = 2

        color: Dict[str, int] = {
            node_id: WHITE for node_id in node_ids
        }

        parent: Dict[str, Optional[str]] = {
            node_id: None for node_id in node_ids
        }

        def dfs(node: str) -> Optional[List[str]]:
            color[node] = GRAY

            for neighbor in adjacency.get(node, []):
                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    result = dfs(neighbor)

                    if result:
                        return result

                elif color[neighbor] == GRAY:
                    # A cycle was found.
                    # Reconstruct one readable cycle path.
                    cycle: List[str] = [neighbor, node]
                    current = node

                    while current != neighbor and parent.get(current) is not None:
                        current = parent[current]
                        cycle.append(current)

                    cycle.reverse()
                    return cycle

            color[node] = BLACK
            return None

        for node_id in node_ids:
            if color[node_id] == WHITE:
                cycle = dfs(node_id)

                if cycle:
                    return cycle

        return []

    # ==========================================================
    # DAY 32 STEP 3: STATE-MUTATION RESOLVER
    # ==========================================================

    def get_node(
        self,
        quest: QuestDNA,
        node_id: str
    ) -> Optional[NarrativeNode]:
        """
        Find one NarrativeNode by node_id.
        """

        for node in quest.nodes:
            if node.node_id == node_id:
                return node

        return None

    def get_node_mutations(self, node: NarrativeNode) -> Dict[str, Any]:
        """
        Read deterministic state mutations attached to a node.

        We support both:
        1. A future typed field: node.state_mutations
        2. An extra Pydantic field because NarrativeNode allows extras:
           node.model_extra["state_mutations"]

        This keeps the engine forward-compatible without breaking old DNA.
        """

        mutations = getattr(node, "state_mutations", None)

        if mutations is None:
            extra = getattr(node, "model_extra", {}) or {}
            mutations = extra.get("state_mutations", {})

        if mutations is None:
            return {}

        if isinstance(mutations, dict):
            return mutations

        return {}

    def evaluate_completion_condition(
        self,
        node: NarrativeNode,
        world_state: Any = None,
        completed_node_ids: Optional[List[str]] = None,
        condition_context: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Determine if a node's completion_condition is satisfied.

        This is deterministic.
        No vibes.
        No hidden script logic.

        Supported condition examples:

        Always true:
        {
            "type": "always"
        }

        World State flag:
        {
            "type": "world_state_flag",
            "key": "ruins_discovered",
            "value": true
        }

        World State equals:
        {
            "type": "world_state_equals",
            "key": "heat_level",
            "value": 2
        }

        Node completed:
        {
            "type": "node_completed",
            "node_id": "node_enter_ruins"
        }

        AND:
        {
            "type": "and",
            "conditions": [ ... ]
        }

        OR:
        {
            "type": "or",
            "conditions": [ ... ]
        }
        """

        if force:
            return {
                "condition_met": True,
                "errors": []
            }

        condition = node.completion_condition or {}

        if not condition:
            return {
                "condition_met": True,
                "errors": []
            }

        return self._evaluate_condition(
            condition=condition,
            world_state=world_state,
            completed_node_ids=completed_node_ids or [],
            context=condition_context or {}
        )

    def complete_node(
        self,
        quest: QuestDNA,
        node_id: str,
        world_state: Any = None,
        completed_node_ids: Optional[List[str]] = None,
        condition_context: Optional[Dict[str, Any]] = None,
        force: bool = False,
        update_world_state_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Complete one narrative node.

        This does three things:
        1. Validates the quest graph.
        2. Checks whether the node is unlocked and its condition is met.
        3. Applies deterministic state mutations to the Day 11 World State.
        """

        completed_node_ids = list(completed_node_ids or [])
        errors: List[str] = []

        # --------------------------------------------------
        # 1. Validate the quest graph.
        # --------------------------------------------------
        validation = self.validate_quest_dna(quest)

        if not validation["is_valid"]:
            return {
                "success": False,
                "quest_id": quest.quest_id,
                "node_id": node_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "active_node_ids": [],
                "errors": validation["errors"],
                "validation": validation
            }

        # --------------------------------------------------
        # 2. Find the node.
        # --------------------------------------------------
        node = self.get_node(quest, node_id)

        if node is None:
            errors.append(f"Unknown node_id: '{node_id}'.")

            return {
                "success": False,
                "quest_id": quest.quest_id,
                "node_id": node_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "active_node_ids": self.get_active_node_ids(
                    quest=quest,
                    completed_node_ids=completed_node_ids
                ),
                "errors": errors,
                "validation": validation
            }

        # --------------------------------------------------
        # 3. Prevent double completion.
        # --------------------------------------------------
        if node_id in completed_node_ids:
            errors.append(f"Node '{node_id}' is already completed.")

            return {
                "success": False,
                "quest_id": quest.quest_id,
                "node_id": node_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "active_node_ids": self.get_active_node_ids(
                    quest=quest,
                    completed_node_ids=completed_node_ids
                ),
                "errors": errors,
                "validation": validation
            }

        # --------------------------------------------------
        # 4. Check unlock order.
        #
        # Force mode may bypass unlock order for testing.
        # --------------------------------------------------
        if not force:
            if not self.is_node_unlocked(
                quest=quest,
                node_id=node_id,
                completed_node_ids=completed_node_ids
            ):
                errors.append(
                    f"Node '{node_id}' is locked. Complete prerequisite nodes first."
                )

                return {
                    "success": False,
                    "quest_id": quest.quest_id,
                    "node_id": node_id,
                    "completed_node_ids": completed_node_ids,
                    "world_state": world_state,
                    "applied_mutations": {},
                    "mutation_report": {},
                    "active_node_ids": self.get_active_node_ids(
                        quest=quest,
                        completed_node_ids=completed_node_ids
                    ),
                    "errors": errors,
                    "validation": validation
                }

        # --------------------------------------------------
        # 5. Check completion condition.
        #
        # Force mode may bypass condition for testing.
        # --------------------------------------------------
        condition_result = self.evaluate_completion_condition(
            node=node,
            world_state=world_state,
            completed_node_ids=completed_node_ids,
            condition_context=condition_context,
            force=force
        )

        if not condition_result["condition_met"]:
            errors.append(
                f"Completion condition not met for node '{node_id}'."
            )
            errors.extend(condition_result.get("errors", []))

            return {
                "success": False,
                "quest_id": quest.quest_id,
                "node_id": node_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "active_node_ids": self.get_active_node_ids(
                    quest=quest,
                    completed_node_ids=completed_node_ids
                ),
                "errors": errors,
                "validation": validation,
                "condition_result": condition_result
            }

        # --------------------------------------------------
        # 6. Read node-level state mutations.
        # --------------------------------------------------
        mutations = self.get_node_mutations(node)

        # --------------------------------------------------
        # 7. Apply mutations to Day 11 World State.
        # --------------------------------------------------
        updated_world_state, mutation_report = self.apply_state_mutations(
            world_state=world_state,
            mutations=mutations,
            update_world_state_fn=update_world_state_fn
        )

        # --------------------------------------------------
        # 8. Mark node complete.
        # --------------------------------------------------
        completed_node_ids.append(node_id)

        return {
            "success": True,
            "quest_id": quest.quest_id,
            "node_id": node_id,
            "semantic_concept": node.semantic_concept,
            "completed_node_ids": completed_node_ids,
            "world_state": updated_world_state,
            "applied_mutations": mutations,
            "mutation_report": mutation_report,
            "active_node_ids": self.get_active_node_ids(
                quest=quest,
                completed_node_ids=completed_node_ids
            ),
            "errors": [],
            "validation": validation,
            "condition_result": condition_result
        }

    def complete_quest(
        self,
        quest: QuestDNA,
        world_state: Any = None,
        completed_node_ids: Optional[List[str]] = None,
        update_world_state_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Complete the entire quest.

        This is only allowed when every node in the graph is complete.
        Then the quest-level state_mutations are applied.
        """

        completed_node_ids = list(completed_node_ids or [])
        errors: List[str] = []

        validation = self.validate_quest_dna(quest)

        if not validation["is_valid"]:
            return {
                "success": False,
                "quest_id": quest.quest_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "errors": validation["errors"],
                "validation": validation
            }

        completed_set = set(completed_node_ids)
        missing_nodes = [
            node.node_id
            for node in quest.nodes
            if node.node_id not in completed_set
        ]

        if missing_nodes:
            errors.append(
                "Quest cannot be completed. Missing nodes: "
                + ", ".join(missing_nodes)
            )

            return {
                "success": False,
                "quest_id": quest.quest_id,
                "completed_node_ids": completed_node_ids,
                "world_state": world_state,
                "applied_mutations": {},
                "mutation_report": {},
                "errors": errors,
                "validation": validation
            }

        mutations = quest.state_mutations or {}

        updated_world_state, mutation_report = self.apply_state_mutations(
            world_state=world_state,
            mutations=mutations,
            update_world_state_fn=update_world_state_fn
        )

        return {
            "success": True,
            "quest_id": quest.quest_id,
            "completed_node_ids": completed_node_ids,
            "world_state": updated_world_state,
            "applied_mutations": mutations,
            "mutation_report": mutation_report,
            "errors": [],
            "validation": validation
        }

    def apply_state_mutations(
        self,
        world_state: Any,
        mutations: Dict[str, Any],
        update_world_state_fn: Optional[Callable] = None
    ) -> tuple[Any, Dict[str, Any]]:
        """
        Apply deterministic World State mutations.

        Priority:
        1. Use the injected Day 11 update_world_state() function if provided.
        2. Try to auto-discover Day 11 update_world_state().
        3. Fall back to the built-in deterministic mutation resolver.
        """

        errors: List[str] = []

        if mutations is None:
            mutations = {}

        if not mutations:
            return world_state, {
                "engine": "none",
                "applied_mutations": {},
                "errors": []
            }

        if update_world_state_fn is None:
            update_world_state_fn = self._get_default_update_world_state_fn()

        # --------------------------------------------------
        # Try external Day 11 World State updater first.
        # --------------------------------------------------
        if update_world_state_fn is not None:
            try:
                updated_world_state = update_world_state_fn(
                    world_state,
                    mutations
                )

                if updated_world_state is None:
                    updated_world_state = world_state

                return updated_world_state, {
                    "engine": "external_day11",
                    "applied_mutations": mutations,
                    "errors": []
                }

            except TypeError as exc:
                errors.append(f"External update_world_state TypeError: {exc}")

                try:
                    updated_world_state = update_world_state_fn(
                        world_state=world_state,
                        mutations=mutations
                    )

                    if updated_world_state is None:
                        updated_world_state = world_state

                    return updated_world_state, {
                        "engine": "external_day11",
                        "applied_mutations": mutations,
                        "errors": []
                    }

                except Exception as exc:
                    errors.append(
                        f"External update_world_state keyword fallback failed: {exc}"
                    )

            except Exception as exc:
                errors.append(f"External update_world_state failed: {exc}")

        # --------------------------------------------------
        # Built-in deterministic fallback.
        # --------------------------------------------------
        updated_world_state = self._builtin_update_world_state(
            world_state=world_state,
            mutations=mutations
        )

        return updated_world_state, {
            "engine": "builtin_fallback",
            "applied_mutations": mutations,
            "errors": errors
        }

    def _get_default_update_world_state_fn(self) -> Optional[Callable]:
        """
        Try to locate the Day 11 update_world_state function.

        If your Day 11 function lives somewhere else,
        you can always pass it directly:

            engine.complete_node(
                quest=quest,
                node_id="node_1",
                world_state=world_state,
                update_world_state_fn=my_update_world_state
            )
        """

        try:
            from .world_state_engine import update_world_state
            return update_world_state
        except ImportError:
            pass

        try:
            from .state_engine import update_world_state
            return update_world_state
        except ImportError:
            pass

        try:
            from .brain import update_world_state
            return update_world_state
        except ImportError:
            pass

        try:
            from world_state_engine import update_world_state
            return update_world_state
        except ImportError:
            pass

        try:
            from state_engine import update_world_state
            return update_world_state
        except ImportError:
            pass

        try:
            from brain import update_world_state
            return update_world_state
        except ImportError:
            pass

        return None

    def _builtin_update_world_state(
        self,
        world_state: Any,
        mutations: Dict[str, Any]
    ) -> Any:
        """
        A safe deterministic fallback for applying mutations.

        Supported mutation forms:

        Direct top-level mutations:
        {
            "heat_level": 2,
            "time_of_day": "18:00"
        }

        Nested under world_state:
        {
            "world_state": {
                "heat_level": 2
            }
        }

        Nested under set:
        {
            "set": {
                "heat_level": 2
            }
        }

        Math operators:
        {
            "heat_level": {"$add": 1}
            "heat_level": {"$sub": 1}
            "heat_level": {"$multiply": 2}
            "heat_level": {"$set": 5}
        }
        """

        if world_state is None:
            updated_world_state: Any = {}
        elif isinstance(world_state, dict):
            updated_world_state = dict(world_state)
        else:
            updated_world_state = world_state

        payload = mutations

        if isinstance(mutations, dict):
            if "world_state" in mutations and isinstance(mutations["world_state"], dict):
                payload = mutations["world_state"]
            elif "set" in mutations and isinstance(mutations["set"], dict):
                payload = mutations["set"]

        if not isinstance(payload, dict):
            return updated_world_state

        for key, value in payload.items():
            current_value = self._get_context_value(
                key=key,
                world_state=updated_world_state,
                context={}
            )

            new_value = self._resolve_mutation_value(
                current_value=current_value,
                mutation_value=value
            )

            if isinstance(updated_world_state, dict):
                self._set_dict_value(
                    target=updated_world_state,
                    key=key,
                    value=new_value
                )
            else:
                # For Pydantic objects or normal Python objects,
                # we apply top-level attributes deterministically.
                setattr(updated_world_state, key, new_value)

        return updated_world_state

    def _resolve_mutation_value(
        self,
        current_value: Any,
        mutation_value: Any
    ) -> Any:
        """
        Resolve simple deterministic math operators.
        """

        if not isinstance(mutation_value, dict):
            return mutation_value

        if "$set" in mutation_value:
            return mutation_value["$set"]

        if "$add" in mutation_value:
            base = 0 if current_value is None else current_value
            return base + mutation_value["$add"]

        if "$sub" in mutation_value:
            base = 0 if current_value is None else current_value
            return base - mutation_value["$sub"]

        if "$multiply" in mutation_value:
            base = 0 if current_value is None else current_value
            return base * mutation_value["$multiply"]

        return mutation_value

    def _set_dict_value(
        self,
        target: Dict[str, Any],
        key: str,
        value: Any
    ) -> None:
        """
        Set a value inside a dictionary.
        Supports dotted keys like:

        "player.health"
        """

        parts = key.split(".")
        current = target

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}

            current = current[part]

        current[parts[-1]] = value

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        world_state: Any,
        completed_node_ids: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively evaluate a completion condition.
        """

        errors: List[str] = []

        if not isinstance(condition, dict):
            return {
                "condition_met": False,
                "errors": ["Completion condition must be a JSON object."]
            }

        condition_type = condition.get("type", "always")

        # --------------------------------------------------
        # ALWAYS / NEVER
        # --------------------------------------------------
        if condition_type in ["always", "true"]:
            return {
                "condition_met": True,
                "errors": []
            }

        if condition_type in ["never", "false"]:
            return {
                "condition_met": False,
                "errors": []
            }

        # --------------------------------------------------
        # NODE COMPLETED
        # --------------------------------------------------
        if condition_type == "node_completed":
            target_node_id = condition.get("node_id")

            if not target_node_id:
                return {
                    "condition_met": False,
                    "errors": ["node_completed condition requires 'node_id'."]
                }

            return {
                "condition_met": target_node_id in completed_node_ids,
                "errors": []
            }

        # --------------------------------------------------
        # WORLD STATE FLAG / EQUALS
        # --------------------------------------------------
        if condition_type in [
            "world_state_flag",
            "world_state_equals",
            "equals"
        ]:
            key = condition.get("key")
            expected_value = condition.get("value", True)

            if not key:
                return {
                    "condition_met": False,
                    "errors": ["world_state condition requires 'key'."]
                }

            actual_value = self._get_context_value(
                key=key,
                world_state=world_state,
                context=context
            )

            return {
                "condition_met": actual_value == expected_value,
                "errors": []
            }

        # --------------------------------------------------
        # NUMERIC COMPARISONS
        # --------------------------------------------------
        if condition_type in [
            "greater_than",
            "less_than",
            "greater_than_or_equal",
            "less_than_or_equal"
        ]:
            key = condition.get("key")
            expected_value = condition.get("value")

            if not key:
                return {
                    "condition_met": False,
                    "errors": [f"{condition_type} condition requires 'key'."]
                }

            if expected_value is None:
                return {
                    "condition_met": False,
                    "errors": [f"{condition_type} condition requires 'value'."]
                }

            actual_value = self._get_context_value(
                key=key,
                world_state=world_state,
                context=context
            )

            try:
                actual_number = float(actual_value)
                expected_number = float(expected_value)
            except Exception as exc:
                return {
                    "condition_met": False,
                    "errors": [f"Numeric comparison failed: {exc}"]
                }

            if condition_type == "greater_than":
                met = actual_number > expected_number
            elif condition_type == "less_than":
                met = actual_number < expected_number
            elif condition_type == "greater_than_or_equal":
                met = actual_number >= expected_number
            else:
                met = actual_number <= expected_number

            return {
                "condition_met": met,
                "errors": []
            }

        # --------------------------------------------------
        # AND
        # --------------------------------------------------
        if condition_type == "and":
            sub_conditions = condition.get("conditions", [])

            if not isinstance(sub_conditions, list):
                return {
                    "condition_met": False,
                    "errors": ["AND condition requires a list called 'conditions'."]
                }

            all_met = True

            for sub_condition in sub_conditions:
                result = self._evaluate_condition(
                    condition=sub_condition,
                    world_state=world_state,
                    completed_node_ids=completed_node_ids,
                    context=context
                )

                if not result["condition_met"]:
                    all_met = False

                errors.extend(result.get("errors", []))

            return {
                "condition_met": all_met,
                "errors": errors
            }

        # --------------------------------------------------
        # OR
        # --------------------------------------------------
        if condition_type == "or":
            sub_conditions = condition.get("conditions", [])

            if not isinstance(sub_conditions, list):
                return {
                    "condition_met": False,
                    "errors": ["OR condition requires a list called 'conditions'."]
                }

            any_met = False

            for sub_condition in sub_conditions:
                result = self._evaluate_condition(
                    condition=sub_condition,
                    world_state=world_state,
                    completed_node_ids=completed_node_ids,
                    context=context
                )

                if result["condition_met"]:
                    any_met = True

                errors.extend(result.get("errors", []))

            return {
                "condition_met": any_met,
                "errors": errors
            }

        # --------------------------------------------------
        # UNKNOWN CONDITION
        # --------------------------------------------------
        errors.append(f"Unknown completion condition type: '{condition_type}'.")

        return {
            "condition_met": False,
            "errors": errors
        }

    def _get_context_value(
        self,
        key: str,
        world_state: Any,
        context: Dict[str, Any]
    ) -> Any:
        """
        Read a value from condition_context first, then World State.

        Supports dotted keys:

        "player.health"
        "heat_level"
        "time_of_day"
        """

        if not key:
            return None

        # --------------------------------------------------
        # 1. Try direct context.
        # --------------------------------------------------
        if context and key in context:
            return context[key]

        # --------------------------------------------------
        # 2. Try nested context.
        # --------------------------------------------------
        context_value = self._get_nested_value(
            source=context,
            key=key
        )

        if context_value is not None:
            return context_value

        # --------------------------------------------------
        # 3. Try World State.
        # --------------------------------------------------
        return self._get_nested_value(
            source=world_state,
            key=key
        )

    def _get_nested_value(
        self,
        source: Any,
        key: str
    ) -> Any:
        """
        Safely read dotted keys from dicts or objects.
        """

        if source is None:
            return None

        parts = key.split(".")
        current = source

        for part in parts:
            if current is None:
                return None

            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)

        return current

    # ==========================================================
    # GRAPH HELPERS
    # ==========================================================

    def get_active_node_ids(
        self,
        quest: QuestDNA,
        completed_node_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Return all nodes that are unlocked and not yet completed.
        """

        completed = set(completed_node_ids or [])
        active: List[str] = []

        validation = self.validate_quest_dna(quest)

        if not validation["is_valid"]:
            return []

        for node in quest.nodes:
            if node.node_id in completed:
                continue

            if self.is_node_unlocked(
                quest=quest,
                node_id=node.node_id,
                completed_node_ids=list(completed)
            ):
                active.append(node.node_id)

        return active

    def is_node_unlocked(
        self,
        quest: QuestDNA,
        node_id: str,
        completed_node_ids: Optional[List[str]] = None
    ) -> bool:
        """
        A node is unlocked when every incoming edge's from_node is complete.
        """

        completed = set(completed_node_ids or [])

        node_exists = any(
            node.node_id == node_id
            for node in quest.nodes
        )

        if not node_exists:
            return False

        for edge in quest.edges:
            if edge.to_node == node_id:
                if edge.from_node not in completed:
                    return False

        return True


# ==========================================================
# PUBLIC CONVENIENCE FUNCTIONS
# ==========================================================

def validate_quest_dna(quest: QuestDNA) -> Dict[str, Any]:
    """
    Validate QuestDNA without manually creating an engine instance.
    """

    engine = NarrativeEngine()
    return engine.validate_quest_dna(quest)


def complete_quest_node(
    quest: QuestDNA,
    node_id: str,
    world_state: Any = None,
    completed_node_ids: Optional[List[str]] = None,
    condition_context: Optional[Dict[str, Any]] = None,
    force: bool = False,
    update_world_state_fn: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Complete one quest node without manually creating an engine instance.
    """

    engine = NarrativeEngine()
    return engine.complete_node(
        quest=quest,
        node_id=node_id,
        world_state=world_state,
        completed_node_ids=completed_node_ids,
        condition_context=condition_context,
        force=force,
        update_world_state_fn=update_world_state_fn
    )