from typing import List, Dict, Optional, Any, Tuple, Union

try:
    from .models import (
        InputDNA,
        AccessibilityDNA,
        AdaptationEvent,
    )
except ImportError:
    from packages.core.models import (
        InputDNA,
        AccessibilityDNA,
        AdaptationEvent,
    )


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _safe_number(value: Any, default: float = 0.0) -> float:
    """
    Safely convert almost anything into a float.
    """
    if value is None:
        return default

    try:
        return float(value)
    except Exception:
        return default


def _get_field(source: Any, key: str, default: Any = None) -> Any:
    """
    Safely read a field from a dict, Pydantic model, or object.
    """
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    value = getattr(source, key, None)
    if value is not None:
        return value

    model_extra = getattr(source, "model_extra", None)
    if isinstance(model_extra, dict):
        return model_extra.get(key, default)

    return default


def _coerce_accessibility(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]]
) -> AccessibilityDNA:
    """
    Convert incoming accessibility data into a clean AccessibilityDNA object.
    """
    if accessibility is None:
        return AccessibilityDNA()

    if isinstance(accessibility, AccessibilityDNA):
        if hasattr(accessibility, "model_copy"):
            return accessibility.model_copy(deep=True)
        if hasattr(accessibility, "copy"):
            return accessibility.copy(deep=True)
        return AccessibilityDNA(**accessibility.model_dump())

    if isinstance(accessibility, dict):
        return AccessibilityDNA(**accessibility)

    return AccessibilityDNA()


# ==========================================================
# DETERMINISTIC TIMING VAULT
# ==========================================================
# These are fallback base timing seeds.
# They are NOT hardcoded gameplay law.
# They can be overwritten by JSON DNA, OGF_STATE, or the Brain.
#
# If InputDNA provides base_window_ms, that value wins.
# ==========================================================

FALLBACK_BASE_ACTION_WINDOWS_MS: Dict[str, int] = {
    "dodge": 200,
    "parry": 150,
    "confirm": 300,
    "interact": 250,
    "jump": 200,
}


# ==========================================================
# MOTOR ASSIST MULTIPLIERS
# ==========================================================
# These are mathematical comfort multipliers.
# They do not touch raw input code.
# They only reshape the timing windows declared by DNA.
# ==========================================================

MOTOR_ASSIST_MULTIPLIERS: Dict[str, float] = {
    "standard": 1.0,
    "generous_timing": 2.5,
    "max_assist": 3.5,
}


# ==========================================================
# DETERMINISTIC INPUT ENGINE
# ==========================================================

class DeterministicInputEngine:
    """
    The Universal Translator & Traffic Cop for our game inputs.

    Day 25:
    It reads the InputDNA, builds a map, and routes hardware to actions
    based on the current Context: gameplay, ui, or cinematic.

    Day 31:
    It also adapts input timing windows using AccessibilityDNA.
    """

    def __init__(
        self,
        base_action_windows_ms: Optional[Dict[str, Union[int, float]]] = None
    ):
        # Day 25 original state.
        self.input_map: Dict[str, str] = {}
        self.current_context: str = "gameplay"

        # Day 31 motor assist state.
        self.base_action_windows_ms: Dict[str, int] = self._normalize_windows(
            base_action_windows_ms or FALLBACK_BASE_ACTION_WINDOWS_MS
        )

        self.input_timing_state: Dict[str, Any] = self._build_timing_state(
            motor_assist_mode="standard",
            base_windows=self.base_action_windows_ms,
            active_windows=self.base_action_windows_ms,
            multiplier=1.0
        )

        self.last_adaptation_events: List[AdaptationEvent] = []

    # ------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------

    def _normalize_windows(
        self,
        windows: Dict[str, Union[int, float]]
    ) -> Dict[str, int]:
        """
        Convert timing windows into clean positive integers.
        """
        normalized: Dict[str, int] = {}

        for action_name, window_ms in windows.items():
            safe_window = max(0.0, _safe_number(window_ms, 0.0))
            normalized[str(action_name)] = int(round(safe_window))

        return normalized

    def _build_timing_state(
        self,
        motor_assist_mode: str,
        base_windows: Dict[str, int],
        active_windows: Dict[str, int],
        multiplier: float
    ) -> Dict[str, Any]:
        """
        Build the single source of truth for input timing.
        """
        return {
            "motor_assist_mode": motor_assist_mode,
            "global_window_multiplier": round(_safe_number(multiplier, 1.0), 4),
            "base_action_windows_ms": dict(base_windows),
            "active_action_windows_ms": dict(active_windows),
            "formula": "active_window_ms = base_window_ms * motor_assist_multiplier",
        }

    # ------------------------------------------------------
    # DAY 25 ORIGINAL BEHAVIOR
    # ------------------------------------------------------

    def build_map_from_dna(
        self,
        input_dna_list: List[Union[InputDNA, Dict[str, Any]]]
    ):
        """
        Step A: Read the DNA and build our fast lookup list.

        Original Day 25 behavior:
        - hardware_trigger + active_context becomes the unique key.
        - The value is the abstract action_name.

        Day 31 addition:
        - If an InputDNA carries base_window_ms, we honor it.
        - If not, we use the deterministic fallback vault.
        """
        self.input_map = {}
        discovered_windows: Dict[str, int] = {}

        if not isinstance(input_dna_list, list):
            input_dna_list = []

        for dna in input_dna_list:
            if not isinstance(dna, InputDNA):
                dna = InputDNA(**dna)

            # Create a unique key: e.g., "Spacebar_gameplay" or "Spacebar_cinematic"
            unique_key = f"{dna.hardware_trigger}_{dna.active_context}"
            self.input_map[unique_key] = dna.action_name

            # Day 31:
            # Read optional timing DNA from the InputDNA if it exists.
            base_window = _get_field(dna, "base_window_ms")

            if base_window is None:
                base_window = _get_field(dna, "timing_window_ms")

            if base_window is not None:
                safe_window = max(0.0, _safe_number(base_window, 0.0))
                discovered_windows[dna.action_name] = int(round(safe_window))

            elif dna.action_name in FALLBACK_BASE_ACTION_WINDOWS_MS:
                discovered_windows[dna.action_name] = FALLBACK_BASE_ACTION_WINDOWS_MS[dna.action_name]

        # Merge timing windows.
        # Existing base windows remain unless DNA explicitly provides newer truth.
        merged_windows = dict(self.base_action_windows_ms)
        merged_windows.update(discovered_windows)

        self.base_action_windows_ms = self._normalize_windows(merged_windows)

        # Preserve the current motor assist mode while rebuilding active windows.
        current_mode = self.input_timing_state.get("motor_assist_mode", "standard")
        current_multiplier = MOTOR_ASSIST_MULTIPLIERS.get(current_mode, 1.0)

        active_windows = {
            action_name: int(round(base_ms * current_multiplier))
            for action_name, base_ms in self.base_action_windows_ms.items()
        }

        self.input_timing_state = self._build_timing_state(
            motor_assist_mode=current_mode,
            base_windows=self.base_action_windows_ms,
            active_windows=active_windows,
            multiplier=current_multiplier
        )

    def set_context(self, new_context: str):
        """
        Step B: The Traffic Cop switches modes.

        When the camera enters a cutscene, the game calls this
        to switch to "cinematic" mode.
        """
        self.current_context = new_context or "gameplay"

    def get_action(self, hardware_pressed: str) -> Optional[str]:
        """
        Step C: The game asks:

        "What does Spacebar do right now?"

        The engine automatically uses the active context
        to find the perfect action.
        """
        unique_key = f"{hardware_pressed}_{self.current_context}"
        return self.input_map.get(unique_key)

    def get_full_map(self) -> Dict[str, str]:
        """
        Step D: The backend calls this to send the entire map
        to the browser frontend.

        This is how the JavaScript file gets its rules
        without hardcoding anything.
        """
        return self.input_map.copy()

    # ------------------------------------------------------
    # DAY 31: MOTOR ASSIST ADAPTATION
    # ------------------------------------------------------

    def get_motor_assist_multiplier(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> float:
        """
        Read motor_assist_mode from AccessibilityDNA and return the multiplier.
        """
        accessibility_dna = _coerce_accessibility(accessibility)
        mode = accessibility_dna.motor_assist_mode

        return MOTOR_ASSIST_MULTIPLIERS.get(mode, 1.0)

    def calculate_active_window_ms(
        self,
        base_window_ms: Union[int, float],
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> int:
        """
        Calculate a single active timing window from a base window.
        """
        multiplier = self.get_motor_assist_multiplier(accessibility)
        safe_base = max(0.0, _safe_number(base_window_ms, 0.0))

        return int(round(safe_base * multiplier))

    def adapt_timing_windows(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        base_action_windows_ms: Optional[Dict[str, Union[int, float]]] = None
    ) -> Tuple[Dict[str, Any], List[AdaptationEvent], Dict[str, Any]]:
        """
        Adapt all input timing windows using AccessibilityDNA.

        Returns:
        - updated input timing state
        - adaptation events
        - deterministic report
        """
        accessibility_dna = _coerce_accessibility(accessibility)

        if base_action_windows_ms is not None:
            self.base_action_windows_ms = self._normalize_windows(base_action_windows_ms)

        old_state = self.input_timing_state
        old_mode = old_state.get("motor_assist_mode", "standard")
        old_active_windows = old_state.get("active_action_windows_ms", {})

        new_mode = accessibility_dna.motor_assist_mode
        multiplier = self.get_motor_assist_multiplier(accessibility_dna)

        new_active_windows: Dict[str, int] = {}
        changes: Dict[str, Dict[str, Any]] = {}

        for action_name, base_window_ms in self.base_action_windows_ms.items():
            active_window_ms = int(round(max(0.0, base_window_ms * multiplier)))
            new_active_windows[action_name] = active_window_ms

            old_window_ms = old_active_windows.get(action_name)

            if old_window_ms != active_window_ms:
                changes[action_name] = {
                    "base_window_ms": base_window_ms,
                    "previous_active_window_ms": old_window_ms,
                    "new_active_window_ms": active_window_ms,
                    "multiplier": multiplier,
                }

        self.input_timing_state = self._build_timing_state(
            motor_assist_mode=new_mode,
            base_windows=self.base_action_windows_ms,
            active_windows=new_active_windows,
            multiplier=multiplier
        )

        events: List[AdaptationEvent] = []

        if changes or old_mode != new_mode:
            events.append(
                AdaptationEvent(
                    trigger_type="motor_assist_mode",
                    adapted_system="input_engine"
                )
            )

        self.last_adaptation_events = events

        report = {
            "previous_motor_assist_mode": old_mode,
            "new_motor_assist_mode": new_mode,
            "multiplier": multiplier,
            "changed_actions": len(changes),
            "changes": changes,
            "input_timing_state": self.export_timing_state(),
        }

        return self.input_timing_state, events, report

    def apply_accessibility(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        base_action_windows_ms: Optional[Dict[str, Union[int, float]]] = None
    ) -> Tuple[Dict[str, Any], List[AdaptationEvent], Dict[str, Any]]:
        """
        Friendly wrapper for adapting input timing from AccessibilityDNA.
        """
        return self.adapt_timing_windows(
            accessibility=accessibility,
            base_action_windows_ms=base_action_windows_ms
        )

    # ------------------------------------------------------
    # TIMING QUERY
    # ------------------------------------------------------

    def get_action_window_ms(
        self,
        action_name: str,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> int:
        """
        Get the active timing window for an action.

        If accessibility is provided, calculate it live.
        If not, use the current input timing state.
        """
        if accessibility is not None:
            base_window_ms = self.base_action_windows_ms.get(action_name, 0)
            return self.calculate_active_window_ms(base_window_ms, accessibility)

        active_windows = self.input_timing_state.get("active_action_windows_ms", {})

        return int(
            active_windows.get(
                action_name,
                self.base_action_windows_ms.get(action_name, 0)
            )
        )

    def is_within_window(
        self,
        elapsed_ms: Union[int, float],
        action_name: str,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> bool:
        """
        Deterministically check whether an action happened inside its timing window.
        """
        elapsed = max(0.0, _safe_number(elapsed_ms, 0.0))
        window_ms = self.get_action_window_ms(action_name, accessibility)

        return elapsed <= window_ms

    # ------------------------------------------------------
    # STATE EXPORT / IMPORT
    # ------------------------------------------------------

    def get_full_timing_map(self) -> Dict[str, Any]:
        """
        Frontend-friendly export of the current timing reality.
        """
        return self.export_timing_state()

    def export_timing_state(self) -> Dict[str, Any]:
        """
        Export the current deterministic input timing state.
        Safe for OGF_STATE.json.
        """
        return {
            "motor_assist_mode": self.input_timing_state.get("motor_assist_mode", "standard"),
            "global_window_multiplier": self.input_timing_state.get("global_window_multiplier", 1.0),
            "base_action_windows_ms": dict(self.base_action_windows_ms),
            "active_action_windows_ms": self.input_timing_state.get("active_action_windows_ms", {}),
            "formula": self.input_timing_state.get(
                "formula",
                "active_window_ms = base_window_ms * motor_assist_multiplier"
            ),
        }

    def import_timing_state(
        self,
        state: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Restore input timing state from OGF_STATE.json or AppDNA.
        """
        if not isinstance(state, dict):
            return self.export_timing_state()

        base_windows = state.get("base_action_windows_ms")
        if isinstance(base_windows, dict):
            self.base_action_windows_ms = self._normalize_windows(base_windows)

        motor_assist_mode = str(state.get("motor_assist_mode", "standard"))

        multiplier = _safe_number(
            state.get(
                "global_window_multiplier",
                MOTOR_ASSIST_MULTIPLIERS.get(motor_assist_mode, 1.0)
            ),
            1.0
        )

        active_windows = state.get("active_action_windows_ms")

        if not isinstance(active_windows, dict):
            active_windows = {
                action_name: int(round(base_ms * multiplier))
                for action_name, base_ms in self.base_action_windows_ms.items()
            }

        self.input_timing_state = self._build_timing_state(
            motor_assist_mode=motor_assist_mode,
            base_windows=self.base_action_windows_ms,
            active_windows=self._normalize_windows(active_windows),
            multiplier=multiplier
        )

        return self.export_timing_state()


# ==========================================================
# COMPATIBILITY ALIASES
# ==========================================================
# Some future systems may refer to the engine as InputEngine.
# Your original name remains the truth.

InputEngine = DeterministicInputEngine


# ==========================================================
# MODULE-LEVEL DEFAULT ENGINE
# ==========================================================
# This allows other systems to import a ready, lightweight engine
# without constructing it repeatedly.

default_input_engine = DeterministicInputEngine()