"""
packages/core/camera_comfort_engine.py

Day 31: The Accessibility Hole — Camera Comfort Mode.

This is the safe adaptation bridge for the Day 15 Cinematographer.

We NEVER hardcode accessibility settings.
We read AccessibilityDNA.camera_comfort_mode and mathematically reshape
camera motion reality.

Reduced motion preserves cinematic emotion through lighting and color,
not through shakes, lerps, or aggressive FOV movement.
"""

import copy
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

try:
    from .models import (
        AccessibilityDNA,
        AdaptationEvent,
        CameraAction,
    )
except ImportError:
    from packages.core.models import (
        AccessibilityDNA,
        AdaptationEvent,
        CameraAction,
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


def _model_to_dict(data: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model or dict into a plain dict.
    Returns an empty dict for None.
    """
    if data is None:
        return {}

    if isinstance(data, BaseModel):
        if hasattr(data, "model_dump"):
            return copy.deepcopy(data.model_dump())
        return copy.deepcopy(data.dict())

    if isinstance(data, dict):
        return copy.deepcopy(data)

    return {}


def _wrap_like(
    original: Any,
    adapted_dict: Dict[str, Any],
    model_class: Any
) -> Any:
    """
    If the original input was a Pydantic model, return the same model type.
    If the original input was a dict, return a dict.
    """
    if isinstance(original, BaseModel):
        try:
            return model_class(**adapted_dict)
        except Exception:
            return adapted_dict

    return adapted_dict


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
# CAMERA COMFORT PROFILES
# ==========================================================

DEFAULT_BASE_CAMERA_RIG_STATE: Dict[str, Any] = {
    "shake_amplitude": 1.0,
    "sine_wave_shake_enabled": True,
    "fov_change_multiplier": 1.0,
    "interpolation_mode": "smooth_lerp",
    "lerp_duration_seconds": 0.35,
    "snap_to_stable_angles": False,
    "motion_emotion_priority": True,
    "lighting_emotion_priority": False,
    "color_grade_emotion_priority": False,
    "emotion_preservation_channel": "motion",
}


CAMERA_COMFORT_PROFILES: Dict[str, Dict[str, Any]] = {
    "standard": {
        "shake_multiplier": 1.0,
        "sine_wave_shake_enabled": True,
        "fov_change_multiplier": 1.0,
        "interpolation_mode": "smooth_lerp",
        "lerp_duration_seconds": 0.35,
        "snap_to_stable_angles": False,
        "motion_emotion_priority": True,
        "lighting_emotion_priority": False,
        "color_grade_emotion_priority": False,
        "emotion_preservation_channel": "motion",
    },

    "reduced_motion": {
        "shake_multiplier": 0.0,
        "sine_wave_shake_enabled": False,
        "fov_change_multiplier": 0.25,
        "interpolation_mode": "snap",
        "lerp_duration_seconds": 0.0,
        "snap_to_stable_angles": True,
        "motion_emotion_priority": False,
        "lighting_emotion_priority": True,
        "color_grade_emotion_priority": True,
        "emotion_preservation_channel": "lighting_and_color",
    },

    "stable_only": {
        "shake_multiplier": 0.0,
        "sine_wave_shake_enabled": False,
        "fov_change_multiplier": 0.0,
        "interpolation_mode": "snap",
        "lerp_duration_seconds": 0.0,
        "snap_to_stable_angles": True,
        "motion_emotion_priority": False,
        "lighting_emotion_priority": True,
        "color_grade_emotion_priority": True,
        "emotion_preservation_channel": "lighting_and_color",
    },
}


# ==========================================================
# CAMERA COMFORT ENGINE
# ==========================================================

class CameraComfortEngine:
    """
    The Deterministic Camera Comfort Adapter.

    This engine reads AccessibilityDNA.camera_comfort_mode and reshapes
    camera rigs and camera actions without touching raw camera code.
    """

    def get_comfort_profile(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Return the active camera comfort mode and its mathematical profile.
        """
        accessibility_dna = _coerce_accessibility(accessibility)
        mode = accessibility_dna.camera_comfort_mode

        profile = CAMERA_COMFORT_PROFILES.get(
            mode,
            CAMERA_COMFORT_PROFILES["standard"]
        )

        return mode, copy.deepcopy(profile)

    # ------------------------------------------------------
    # CAMERA RIG ADAPTATION
    # ------------------------------------------------------

    def adapt_camera_rig(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        camera_rig_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], List[AdaptationEvent], Dict[str, Any]]:
        """
        Adapt a camera rig state using AccessibilityDNA.

        Returns:
        - adapted camera rig state
        - adaptation events
        - deterministic report
        """
        mode, profile = self.get_comfort_profile(accessibility)

        rig = _model_to_dict(camera_rig_state)

        if not rig:
            rig = copy.deepcopy(DEFAULT_BASE_CAMERA_RIG_STATE)

        # Preserve the original base rig so standard mode can restore it.
        if "base_camera_rig_state" not in rig:
            base_candidate = copy.deepcopy(rig)

            # Clean meta fields out of the preserved base.
            base_candidate.pop("base_camera_rig_state", None)
            base_candidate.pop("camera_comfort_mode", None)
            base_candidate.pop("active_shake_amplitude", None)
            base_candidate.pop("active_fov_change_multiplier", None)

            rig["base_camera_rig_state"] = base_candidate

        base_rig = rig.get("base_camera_rig_state", DEFAULT_BASE_CAMERA_RIG_STATE)

        old_state = copy.deepcopy(rig)

        base_shake_amplitude = _safe_number(
            base_rig.get("shake_amplitude", 1.0),
            1.0
        )

        base_fov_change_multiplier = _safe_number(
            base_rig.get("fov_change_multiplier", 1.0),
            1.0
        )

        base_lerp_duration = _safe_number(
            base_rig.get("lerp_duration_seconds", profile.get("lerp_duration_seconds", 0.35)),
            0.35
        )

        active_shake_amplitude = round(
            base_shake_amplitude * _safe_number(profile.get("shake_multiplier", 1.0), 1.0),
            4
        )

        active_fov_change_multiplier = round(
            base_fov_change_multiplier * _safe_number(profile.get("fov_change_multiplier", 1.0), 1.0),
            4
        )

        rig["camera_comfort_mode"] = mode
        rig["shake_multiplier"] = profile.get("shake_multiplier", 1.0)
        rig["active_shake_amplitude"] = active_shake_amplitude
        rig["sine_wave_shake_enabled"] = bool(
            profile.get("sine_wave_shake_enabled", True)
            and _safe_number(profile.get("shake_multiplier", 1.0), 1.0) > 0.0
        )

        rig["fov_change_multiplier"] = profile.get("fov_change_multiplier", 1.0)
        rig["active_fov_change_multiplier"] = active_fov_change_multiplier

        rig["interpolation_mode"] = profile.get("interpolation_mode", "smooth_lerp")
        rig["snap_to_stable_angles"] = bool(profile.get("snap_to_stable_angles", False))

        if rig["interpolation_mode"] == "snap":
            rig["lerp_duration_seconds"] = 0.0
        else:
            rig["lerp_duration_seconds"] = base_lerp_duration

        rig["motion_emotion_priority"] = bool(profile.get("motion_emotion_priority", True))
        rig["lighting_emotion_priority"] = bool(profile.get("lighting_emotion_priority", False))
        rig["color_grade_emotion_priority"] = bool(profile.get("color_grade_emotion_priority", False))
        rig["emotion_preservation_channel"] = profile.get("emotion_preservation_channel", "motion")

        changes: Dict[str, Dict[str, Any]] = {}

        for key, new_value in rig.items():
            if key == "base_camera_rig_state":
                continue

            old_value = old_state.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value,
                }

        events: List[AdaptationEvent] = []

        if changes:
            events.append(
                AdaptationEvent(
                    trigger_type="camera_comfort_mode",
                    adapted_system="camera_cinematographer"
                )
            )

        report = {
            "camera_comfort_mode": mode,
            "changed_fields": len(changes),
            "changes": changes,
            "math": {
                "active_shake_amplitude": "base_shake_amplitude * shake_multiplier",
                "active_fov_change_multiplier": "base_fov_change_multiplier * fov_change_multiplier",
                "lerp_rule": "if interpolation_mode == snap then lerp_duration_seconds = 0",
            },
            "emotion_preservation_channel": rig["emotion_preservation_channel"],
            "events": len(events),
        }

        return rig, events, report

    # ------------------------------------------------------
    # CAMERA ACTION ADAPTATION
    # ------------------------------------------------------

    def adapt_camera_action(
        self,
        camera_action: Optional[Union[CameraAction, Dict[str, Any]]] = None,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
    ) -> Tuple[Any, List[AdaptationEvent], Dict[str, Any]]:
        """
        Adapt a CameraAction using AccessibilityDNA.

        Returns:
        - adapted CameraAction
        - adaptation events
        - deterministic report
        """
        mode, profile = self.get_comfort_profile(accessibility)

        original_action = camera_action
        action = _model_to_dict(camera_action)

        if not action:
            action = {
                "movement_type": "static",
                "duration_seconds": 0.0,
                "intensity": 0.0,
            }

        # Preserve the original action so standard mode can restore it.
        if "base_camera_action" not in action:
            action["base_camera_action"] = {
                "movement_type": action.get("movement_type", "static"),
                "duration_seconds": action.get("duration_seconds", 0.0),
                "intensity": action.get("intensity", 0.0),
            }

        base_action = action.get("base_camera_action", {})

        old_action = copy.deepcopy(action)

        if mode == "standard":
            action["movement_type"] = base_action.get(
                "movement_type",
                action.get("movement_type", "static")
            )

            action["duration_seconds"] = _safe_number(
                base_action.get(
                    "duration_seconds",
                    action.get("duration_seconds", 0.0)
                ),
                0.0
            )

            action["intensity"] = _safe_number(
                base_action.get(
                    "intensity",
                    action.get("intensity", 0.0)
                ),
                0.0
            )

            action["camera_action_adapted"] = False

        else:
            # Reduced motion and stable_only remove cinematic motion.
            # Emotion is transferred to lighting and color.
            if mode == "reduced_motion":
                action["movement_type"] = "snap"
            else:
                action["movement_type"] = "static"

            action["duration_seconds"] = 0.0
            action["intensity"] = 0.0
            action["camera_action_adapted"] = True

        action["camera_comfort_mode"] = mode
        action["emotion_preservation_channel"] = profile.get(
            "emotion_preservation_channel",
            "motion"
        )

        changes: Dict[str, Dict[str, Any]] = {}

        for key, new_value in action.items():
            if key == "base_camera_action":
                continue

            old_value = old_action.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value,
                }

        events: List[AdaptationEvent] = []

        if changes:
            events.append(
                AdaptationEvent(
                    trigger_type="camera_comfort_mode",
                    adapted_system="camera_cinematographer"
                )
            )

        adapted_action = _wrap_like(
            original_action,
            action,
            CameraAction
        )

        report = {
            "camera_comfort_mode": mode,
            "changed_fields": len(changes),
            "changes": changes,
            "math": {
                "reduced_motion": "movement_type -> snap, intensity -> 0, duration_seconds -> 0",
                "stable_only": "movement_type -> static, intensity -> 0, duration_seconds -> 0",
                "standard": "restore base_camera_action",
            },
            "emotion_preservation_channel": action["emotion_preservation_channel"],
            "events": len(events),
        }

        return adapted_action, events, report

    # ------------------------------------------------------
    # FULL CAMERA COMFORT ADAPTATION
    # ------------------------------------------------------

    def adapt_all(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        camera_rig_state: Optional[Dict[str, Any]] = None,
        camera_actions: Optional[List[Union[CameraAction, Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Adapt the camera rig and all camera actions in one deterministic pass.
        """
        adapted_rig, rig_events, rig_report = self.adapt_camera_rig(
            accessibility=accessibility,
            camera_rig_state=camera_rig_state
        )

        adapted_actions: List[Any] = []
        action_events: List[AdaptationEvent] = []
        action_reports: List[Dict[str, Any]] = []

        if isinstance(camera_actions, list):
            for action in camera_actions:
                adapted_action, events, report = self.adapt_camera_action(
                    camera_action=action,
                    accessibility=accessibility
                )

                adapted_actions.append(adapted_action)
                action_events.extend(events)
                action_reports.append(report)

        all_events = rig_events + action_events

        return {
            "camera_rig": adapted_rig,
            "camera_actions": adapted_actions,
            "events": all_events,
            "report": {
                "rig": rig_report,
                "actions": action_reports,
                "total_events": len(all_events),
            },
        }


# ==========================================================
# MODULE-LEVEL DEFAULT ENGINE
# ==========================================================

default_camera_comfort_engine = CameraComfortEngine()


# ==========================================================
# CONVENIENCE FUNCTIONS
# ==========================================================

def adapt_camera_rig(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    camera_rig_state: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[AdaptationEvent], Dict[str, Any]]:
    """
    Module-level shortcut for camera rig adaptation.
    """
    return default_camera_comfort_engine.adapt_camera_rig(
        accessibility=accessibility,
        camera_rig_state=camera_rig_state
    )


def adapt_camera_action(
    camera_action: Optional[Union[CameraAction, Dict[str, Any]]] = None,
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
) -> Tuple[Any, List[AdaptationEvent], Dict[str, Any]]:
    """
    Module-level shortcut for camera action adaptation.
    """
    return default_camera_comfort_engine.adapt_camera_action(
        camera_action=camera_action,
        accessibility=accessibility
    )


def adapt_all_camera(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    camera_rig_state: Optional[Dict[str, Any]] = None,
    camera_actions: Optional[List[Union[CameraAction, Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Module-level shortcut for full camera adaptation.
    """
    return default_camera_comfort_engine.adapt_all(
        accessibility=accessibility,
        camera_rig_state=camera_rig_state,
        camera_actions=camera_actions
    )