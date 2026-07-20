"""
packages/core/accessibility_engine.py

Day 31: The Accessibility Hole — Cognitive & Motor Adaptation Engine.

This engine reads player struggle signals and converts them into
deterministic AccessibilityDNA adaptations.

We NEVER hardcode accessibility settings.
We read DNA, telemetry, and mastery signals.
We calculate mathematical comfort adaptations.
We emit AdaptationEvents as deterministic proof that reality changed.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from .models import (
        AccessibilityDNA,
        AdaptationEvent,
        TelemetryDNA,
        PerformanceReport,
    )
except ImportError:
    from packages.core.models import (
        AccessibilityDNA,
        AdaptationEvent,
        TelemetryDNA,
        PerformanceReport,
    )


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _safe_number(value: Any, default: float = 0.0) -> float:
    """
    Safely convert almost anything into a float.
    If conversion fails, return the default.
    """
    if value is None:
        return default

    try:
        return float(value)
    except Exception:
        return default


def _first_present(*values: Any) -> Any:
    """
    Return the first value that is not None.
    This allows multiple possible DNA field names without crashing.
    """
    for value in values:
        if value is not None:
            return value
    return None


def _get_field(source: Any, key: str, default: Any = None) -> Any:
    """
    Safely read a field from a dict, Pydantic model, or object.

    This is important because our DNA may evolve.
    Older JSON may not contain newer fields.
    The engine must remain gentle and resilient.
    """
    if source is None:
        return default

    # Dict-like source
    if isinstance(source, dict):
        return source.get(key, default)

    # Normal object / Pydantic field
    value = getattr(source, key, None)
    if value is not None:
        return value

    # Pydantic v2 extra fields
    model_extra = getattr(source, "model_extra", None)
    if isinstance(model_extra, dict):
        return model_extra.get(key, default)

    return default


def _coerce_accessibility(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]]
) -> AccessibilityDNA:
    """
    Convert incoming accessibility data into a clean AccessibilityDNA object.

    Accepts:
    - None
    - dict
    - AccessibilityDNA
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
# ACCESSIBILITY ENGINE
# ==========================================================

class AccessibilityEngine:
    """
    The Deterministic Cognitive & Motor Adaptation Engine.

    This engine does not render UI.
    This engine does not compile backend.
    This engine does not touch raw code.

    It reads signals.
    It calculates comfort.
    It reshapes AccessibilityDNA.
    """

    # Cognitive load scoring weights.
    # Total possible = 100.
    FRAME_DROP_WEIGHT = 35.0
    INPUT_HESITATION_WEIGHT = 35.0
    TUTORIAL_FAILURE_WEIGHT = 30.0

    # The point at which these signals are considered "maximum struggle".
    FRAME_DROP_CEILING = 30.0
    INPUT_HESITATION_CEILING_MS = 1200.0
    TUTORIAL_FAILURE_CEILING = 5.0

    # If cognitive load crosses this threshold, we trigger an AdaptationEvent.
    DEFAULT_COGNITIVE_LOAD_THRESHOLD = 70.0

    # Support ranking.
    # Higher means more supportive.
    COGNITIVE_LOAD_RANK = {
        "minimal": 0,
        "balanced": 1,
        "supported": 2,
        "max_support": 3,
    }

    def __init__(
        self,
        cognitive_load_threshold: float = DEFAULT_COGNITIVE_LOAD_THRESHOLD
    ):
        self.cognitive_load_threshold = _safe_number(
            cognitive_load_threshold,
            self.DEFAULT_COGNITIVE_LOAD_THRESHOLD
        )

    # ------------------------------------------------------
    # SIGNAL EXTRACTION
    # ------------------------------------------------------

    def extract_frame_drops(
        self,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
        explicit_frame_drops: Optional[float] = None
    ) -> float:
        """
        Extract frame drop pressure from telemetry or performance reports.
        """
        frame_drops = _first_present(
            explicit_frame_drops,
            _get_field(telemetry, "frame_drops"),
            _get_field(telemetry, "dropped_frames"),
            _get_field(performance_report, "dropped_frames"),
            _get_field(performance_report, "frame_drops"),
            0.0
        )

        frame_drops = max(0.0, _safe_number(frame_drops, 0.0))

        # If we do not have explicit frame drops, but we can see FPS pain,
        # mathematically estimate frame pressure.
        current_fps = _safe_number(
            _first_present(
                _get_field(performance_report, "current_fps"),
                _get_field(telemetry, "current_fps"),
                _get_field(telemetry, "average_fps"),
                60.0
            ),
            60.0
        )

        fps_threshold = _safe_number(
            _first_present(
                _get_field(telemetry, "fps_threshold"),
                _get_field(performance_report, "fps_threshold"),
                60.0
            ),
            60.0
        )

        if current_fps < fps_threshold:
            fps_deficit = max(0.0, fps_threshold - current_fps)

            # A gentle deterministic estimation:
            # Every 1 FPS below threshold adds estimated frame pressure.
            estimated_frame_pressure = fps_deficit * 1.5
            frame_drops = max(frame_drops, estimated_frame_pressure)

        return frame_drops

    def extract_input_hesitation_ms(
        self,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
        explicit_input_hesitation_ms: Optional[float] = None
    ) -> float:
        """
        Extract input hesitation in milliseconds.

        Input hesitation means the player wanted to act, but delayed.
        This can indicate cognitive overload or motor discomfort.
        """
        hesitation = _first_present(
            explicit_input_hesitation_ms,
            _get_field(telemetry, "input_hesitation_ms"),
            _get_field(telemetry, "input_hesitation"),
            _get_field(performance_report, "input_hesitation_ms"),
            _get_field(performance_report, "input_hesitation"),
            0.0
        )

        return max(0.0, _safe_number(hesitation, 0.0))

    def extract_failed_tutorial_attempts(
        self,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        explicit_failed_tutorial_attempts: Optional[float] = None
    ) -> float:
        """
        Extract failed tutorial attempts.

        Repeated tutorial failure is a strong signal that the experience
        is asking too much of the player right now.
        """
        failures = _first_present(
            explicit_failed_tutorial_attempts,
            _get_field(telemetry, "failed_tutorial_attempts"),
            _get_field(telemetry, "tutorial_failures"),
            _get_field(telemetry, "failed_tutorials"),
            _get_field(telemetry, "tutorial_failed_attempts"),
            0.0
        )

        return max(0.0, _safe_number(failures, 0.0))

    # ------------------------------------------------------
    # COGNITIVE LOAD CALCULATION
    # ------------------------------------------------------

    def calculate_cognitive_load_score(
        self,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
        explicit_frame_drops: Optional[float] = None,
        explicit_input_hesitation_ms: Optional[float] = None,
        explicit_failed_tutorial_attempts: Optional[float] = None
    ) -> float:
        """
        Calculate a cognitive_load_score from 0 to 100.

        0   = calm, comfortable, flowing
        100 = overloaded, struggling, needs maximum support

        The math is deterministic and transparent.
        """
        frame_drops = self.extract_frame_drops(
            telemetry=telemetry,
            performance_report=performance_report,
            explicit_frame_drops=explicit_frame_drops
        )

        input_hesitation_ms = self.extract_input_hesitation_ms(
            telemetry=telemetry,
            performance_report=performance_report,
            explicit_input_hesitation_ms=explicit_input_hesitation_ms
        )

        failed_tutorial_attempts = self.extract_failed_tutorial_attempts(
            telemetry=telemetry,
            explicit_failed_tutorial_attempts=explicit_failed_tutorial_attempts
        )

        # Normalize each signal into a 0.0 to 1.0 pressure value.
        frame_pressure = min(
            frame_drops / self.FRAME_DROP_CEILING,
            1.0
        )

        hesitation_pressure = min(
            input_hesitation_ms / self.INPUT_HESITATION_CEILING_MS,
            1.0
        )

        failure_pressure = min(
            failed_tutorial_attempts / self.TUTORIAL_FAILURE_CEILING,
            1.0
        )

        # Apply weights.
        frame_score = frame_pressure * self.FRAME_DROP_WEIGHT
        hesitation_score = hesitation_pressure * self.INPUT_HESITATION_WEIGHT
        failure_score = failure_pressure * self.TUTORIAL_FAILURE_WEIGHT

        total_score = frame_score + hesitation_score + failure_score

        # Clamp to 0-100 and round for clean deterministic reporting.
        total_score = max(0.0, min(100.0, total_score))
        return round(total_score, 2)

    # ------------------------------------------------------
    # RECOMMENDATION
    # ------------------------------------------------------

    def recommend_cognitive_load_level(self, cognitive_load_score: float) -> str:
        """
        Convert a numeric cognitive load score into an AccessibilityDNA level.

        This is pure math.
        No hardcoded UI.
        No hardcoded tutorial behavior.
        """
        score = _safe_number(cognitive_load_score, 0.0)

        if score >= 80.0:
            return "max_support"

        if score >= 60.0:
            return "supported"

        if score >= 35.0:
            return "balanced"

        return "minimal"

    # ------------------------------------------------------
    # ADAPTATION
    # ------------------------------------------------------

    def adapt_accessibility(
        self,
        current_accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        cognitive_load_score: Optional[float] = None,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
        explicit_frame_drops: Optional[float] = None,
        explicit_input_hesitation_ms: Optional[float] = None,
        explicit_failed_tutorial_attempts: Optional[float] = None
    ) -> Tuple[AccessibilityDNA, List[AdaptationEvent], Dict[str, Any]]:
        """
        Evaluate cognitive load and adapt AccessibilityDNA if needed.

        Returns:
        - updated AccessibilityDNA
        - list of AdaptationEvents
        - deterministic report explaining the math
        """
        accessibility = _coerce_accessibility(current_accessibility)

        if cognitive_load_score is None:
            cognitive_load_score = self.calculate_cognitive_load_score(
                telemetry=telemetry,
                performance_report=performance_report,
                explicit_frame_drops=explicit_frame_drops,
                explicit_input_hesitation_ms=explicit_input_hesitation_ms,
                explicit_failed_tutorial_attempts=explicit_failed_tutorial_attempts
            )

        cognitive_load_score = round(
            max(0.0, min(100.0, _safe_number(cognitive_load_score, 0.0))),
            2
        )

        old_level = accessibility.cognitive_load_level
        recommended_level = self.recommend_cognitive_load_level(cognitive_load_score)

        old_rank = self.COGNITIVE_LOAD_RANK.get(old_level, 1)
        recommended_rank = self.COGNITIVE_LOAD_RANK.get(recommended_level, 1)

        changed = False
        new_level = old_level

        # For safety and peace, automatic evaluation increases support.
        # It does not abruptly remove support unless explicitly told later.
        if recommended_rank > old_rank:
            accessibility.cognitive_load_level = recommended_level
            new_level = recommended_level
            changed = True

        triggered = cognitive_load_score >= self.cognitive_load_threshold

        events: List[AdaptationEvent] = []

        if triggered or changed:
            trigger_type = (
                "cognitive_load_threshold"
                if triggered
                else "cognitive_load_elevation"
            )

            events.append(
                AdaptationEvent(
                    trigger_type=trigger_type,
                    adapted_system="accessibility_engine"
                )
            )

        report = {
            "cognitive_load_score": cognitive_load_score,
            "threshold": self.cognitive_load_threshold,
            "triggered": triggered,
            "previous_cognitive_load_level": old_level,
            "recommended_cognitive_load_level": recommended_level,
            "new_cognitive_load_level": new_level,
            "changed": changed,
            "adaptation_events": len(events),
            "math": {
                "frame_drop_ceiling": self.FRAME_DROP_CEILING,
                "input_hesitation_ceiling_ms": self.INPUT_HESITATION_CEILING_MS,
                "tutorial_failure_ceiling": self.TUTORIAL_FAILURE_CEILING,
                "frame_drop_weight": self.FRAME_DROP_WEIGHT,
                "input_hesitation_weight": self.INPUT_HESITATION_WEIGHT,
                "tutorial_failure_weight": self.TUTORIAL_FAILURE_WEIGHT,
            }
        }

        return accessibility, events, report

    # ------------------------------------------------------
    # CONVENIENCE WRAPPER
    # ------------------------------------------------------

    def evaluate_and_adapt(
        self,
        current_accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
        performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
        explicit_frame_drops: Optional[float] = None,
        explicit_input_hesitation_ms: Optional[float] = None,
        explicit_failed_tutorial_attempts: Optional[float] = None
    ) -> Tuple[AccessibilityDNA, List[AdaptationEvent], Dict[str, Any]]:
        """
        Friendly wrapper for the full evaluate-and-adapt flow.
        """
        return self.adapt_accessibility(
            current_accessibility=current_accessibility,
            cognitive_load_score=None,
            telemetry=telemetry,
            performance_report=performance_report,
            explicit_frame_drops=explicit_frame_drops,
            explicit_input_hesitation_ms=explicit_input_hesitation_ms,
            explicit_failed_tutorial_attempts=explicit_failed_tutorial_attempts
        )


# ==========================================================
# MODULE-LEVEL DEFAULT ENGINE
# ==========================================================
# This allows other systems to import a ready, lightweight engine
# without constructing it repeatedly.

default_accessibility_engine = AccessibilityEngine()