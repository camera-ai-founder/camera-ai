"""
==========================================================
DAY 29: THE TUTORIAL ENGINE (THE SILENT OBSERVER)
==========================================================
This engine watches the World State and the player's recent
inputs. It NEVER interrupts the player with text boxes.
Instead, it flags which TutorialDNA concepts need a subtle
visual hint, and which have been mastered and should be
permanently suppressed.

It is the invisible mentor. Pure, reactive, mathematical.
"""

import time
from typing import List, Dict, Optional, Any
from packages.core.models import TutorialDNA, MasteryEvent


class TutorialEngine:
    """
    The Silent Observer.
    Evaluates TutorialDNA rules against the live World State
    and the player's recent input history from the Day 25 Input Engine.
    """

    def __init__(self):
        # A dictionary tracking the last time each input action was performed.
        # Example: {"dash_button": 1721400000.5, "jump_button": 1721400002.1}
        self.input_history: Dict[str, float] = {}

        # A set of concept_ids the player has already mastered.
        # Once a concept is here, its hint is permanently suppressed.
        self.mastered_concepts: set = set()

        # The list of active hints that the frontend should render right now.
        self.active_hints: List[Dict[str, Any]] = []

    # ----------------------------------------------------------
    # 1. RECORD PLAYER INPUTS (Connected to Day 25 Input Engine)
    # ----------------------------------------------------------
    def record_input(self, action_name: str) -> None:
        """
        Called every time the player presses a mapped button.
        The Day 25 Input Engine should call this automatically.
        
        Example: record_input("dash_button")
        """
        self.input_history[action_name] = time.time()

    # ----------------------------------------------------------
    # 2. MARK A CONCEPT AS MASTERED
    # ----------------------------------------------------------
    def mark_mastered(self, concept_id: str) -> MasteryEvent:
        """
        Called when the player successfully performs the required
        input while the hint is active. This permanently suppresses
        the hint for this concept. The player is now a natural.
        """
        self.mastered_concepts.add(concept_id)
        event = MasteryEvent(concept_id=concept_id)
        return event

    # ----------------------------------------------------------
    # 3. THE SIMPLE CONDITION EVALUATOR (Safe, No eval())
    # ----------------------------------------------------------
    def _evaluate_single_condition(
        self, condition: str, world_state_vars: Dict[str, Any]
    ) -> bool:
        """
        Safely evaluates a single condition string like:
            "player_health < 30"
            "enemy_distance < 5"
        
        We DO NOT use Python's eval(). That is the Old Paradigm
        and it is dangerous. We parse it manually, step by step.
        """
        # Supported operators, checked in order of length
        operators = ["<=", ">=", "==", "!=", "<", ">"]

        for op in operators:
            if op in condition:
                # Split the condition into left side and right side
                parts = condition.split(op)
                if len(parts) != 2:
                    return False

                variable_name = parts[0].strip()
                try:
                    threshold = float(parts[1].strip())
                except ValueError:
                    return False

                # Look up the variable in the world state
                current_value = world_state_vars.get(variable_name)
                if current_value is None:
                    return False

                current_value = float(current_value)

                # Perform the comparison safely
                if op == "<":
                    return current_value < threshold
                elif op == ">":
                    return current_value > threshold
                elif op == "<=":
                    return current_value <= threshold
                elif op == ">=":
                    return current_value >= threshold
                elif op == "==":
                    return current_value == threshold
                elif op == "!=":
                    return current_value != threshold

        return False

    def _evaluate_trigger(
        self, trigger_condition: str, world_state_vars: Dict[str, Any]
    ) -> bool:
        """
        Handles compound conditions joined by 'AND'.
        Example: "player_health < 30 AND enemy_distance < 5"
        """
        # Split by AND (case-insensitive)
        sub_conditions = [c.strip() for c in trigger_condition.upper().split(" AND ")]
        
        # Re-split from the original to preserve variable names
        original_parts = [c.strip() for c in trigger_condition.split(" AND ")]
        if len(original_parts) != len(sub_conditions):
            original_parts = [trigger_condition]

        for part in original_parts:
            if not self._evaluate_single_condition(part, world_state_vars):
                return False

        return True

    # ----------------------------------------------------------
    # 4. THE MAIN EVALUATION LOOP (The Silent Observer)
    # ----------------------------------------------------------
    def evaluate_tutorials(
        self,
        tutorial_dna_list: List[TutorialDNA],
        world_state_vars: Dict[str, Any],
        time_window_seconds: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        The heartbeat of the Tutorial Engine.
        Call this every frame or every game tick.

        It checks each TutorialDNA rule:
          1. Is the concept already mastered? If yes, skip it forever.
          2. Is the trigger condition true? (e.g., health is low)
          3. Has the player NOT performed the required input recently?
        
        If all three are true, the hint is flagged as "needs_hint".

        Args:
            tutorial_dna_list: The list of TutorialDNA from AppDNA.tutorials
            world_state_vars: A flat dict of current game variables.
                              Example: {"player_health": 25, "enemy_distance": 3.2}
            time_window_seconds: How far back to check for inputs (default 5 sec)

        Returns:
            A list of active hint dictionaries for the frontend to render.
        """
        self.active_hints = []
        current_time = time.time()

        for tutorial in tutorial_dna_list:
            # RULE 1: If mastered, permanently suppress. The player knows this.
            if tutorial.concept_id in self.mastered_concepts:
                continue

            # RULE 2: Check if the world state triggers this hint
            if not self._evaluate_trigger(tutorial.trigger_condition, world_state_vars):
                continue

            # RULE 3: Check if the player has NOT performed the required input
            #         within the time window (e.g., last 5 seconds)
            last_input_time = self.input_history.get(tutorial.input_requirement, 0.0)
            time_since_input = current_time - last_input_time

            if time_since_input <= time_window_seconds:
                # The player recently performed the action. No hint needed.
                continue

            # ALL CONDITIONS MET: The player is struggling. Flag the hint.
            self.active_hints.append({
                "concept_id": tutorial.concept_id,
                "hint_visual_type": tutorial.hint_visual_type,
                "input_requirement": tutorial.input_requirement,
                "urgency": min(1.0, time_since_input / 10.0),  # Grows stronger over time
            })

        return self.active_hints

    # ----------------------------------------------------------
    # 5. AUTO-MASTERY CHECK (The Reward Loop)
    # ----------------------------------------------------------
    def check_and_reward_mastery(
        self,
        tutorial_dna_list: List[TutorialDNA],
        world_state_vars: Dict[str, Any],
    ) -> List[MasteryEvent]:
        """
        Called after the player performs an input.
        If the trigger condition is NO LONGER true (e.g., health
        recovered because they dodged), we reward mastery.
        """
        new_mastery_events = []

        for tutorial in tutorial_dna_list:
            if tutorial.concept_id in self.mastered_concepts:
                continue

            # If the trigger is no longer active, the player solved the problem
            if not self._evaluate_trigger(tutorial.trigger_condition, world_state_vars):
                # Check if they recently performed the required input
                last_input_time = self.input_history.get(tutorial.input_requirement, 0.0)
                if (time.time() - last_input_time) <= 5.0:
                    event = self.mark_mastered(tutorial.concept_id)
                    new_mastery_events.append(event)

        return new_mastery_events