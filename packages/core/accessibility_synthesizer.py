"""
packages/core/accessibility_synthesizer.py

Day 31: The Accessibility Hole — Visual Contrast & Audio Cue Synthesizer.

This is the safe adaptation bridge between:
- Day 10 Atomic Token Synthesizer / UI Compiler
- Day 24 Procedural DSP Audio Engine
- Day 31 AccessibilityDNA

We NEVER hardcode accessibility settings.
We read AccessibilityDNA and mathematically reshape other DNA.
"""

import copy
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

try:
    from .models import (
        AccessibilityDNA,
        AdaptationEvent,
        DesignTokens,
        AudioDNA,
        AtomicTokenSynthesizer,
    )
except ImportError:
    from packages.core.models import (
        AccessibilityDNA,
        AdaptationEvent,
        DesignTokens,
        AudioDNA,
        AtomicTokenSynthesizer,
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


# ==========================================================
# WCAG COLOR MATH
# ==========================================================

WCAG_AAA_CONTRAST_RATIO: float = 7.0

BACKGROUND_KEY_HINTS = (
    "background",
    "bg",
    "surface",
    "canvas",
    "base",
)

HEX_DIGITS = set("0123456789abcdefABCDEF")


def normalize_hex(color: Any) -> Optional[str]:
    """
    Normalize a color string into #RRGGBB format.
    Returns None if the value is not a valid hex color.
    """
    if not isinstance(color, str):
        return None

    value = color.strip()

    if value.startswith("#"):
        value = value[1:]

    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)

    if len(value) != 6:
        return None

    for ch in value:
        if ch not in HEX_DIGITS:
            return None

    return f"#{value.upper()}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert #RRGGBB into (red, green, blue).
    """
    clean = normalize_hex(hex_color)

    if clean is None:
        return (0, 0, 0)

    clean = clean[1:]

    red = int(clean[0:2], 16)
    green = int(clean[2:4], 16)
    blue = int(clean[4:6], 16)

    return (red, green, blue)


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert RGB values into #RRGGBB.
    """
    red = max(0, min(255, int(round(red))))
    green = max(0, min(255, int(round(green))))
    blue = max(0, min(255, int(round(blue))))

    return f"#{red:02X}{green:02X}{blue:02X}"


def _channel_to_linear(channel: int) -> float:
    """
    Convert an 8-bit sRGB channel into linear RGB space.
    """
    c = max(0.0, min(255.0, float(channel))) / 255.0

    if c <= 0.03928:
        return c / 12.92

    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG relative luminance.
    """
    red, green, blue = rgb

    r = _channel_to_linear(red)
    g = _channel_to_linear(green)
    b = _channel_to_linear(blue)

    return (0.2126 * r) + (0.7152 * g) + (0.0722 * b)


def contrast_ratio(color_a: str, color_b: str) -> float:
    """
    Calculate the WCAG contrast ratio between two hex colors.
    """
    hex_a = normalize_hex(color_a)
    hex_b = normalize_hex(color_b)

    if hex_a is None or hex_b is None:
        return 1.0

    lum_a = relative_luminance(hex_to_rgb(hex_a))
    lum_b = relative_luminance(hex_to_rgb(hex_b))

    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)

    ratio = (lighter + 0.05) / (darker + 0.05)

    return round(ratio, 3)


def mix_hex(color_a: str, color_b: str, amount: float) -> str:
    """
    Mix two hex colors.

    amount = 0.0 returns color_a.
    amount = 1.0 returns color_b.
    """
    hex_a = normalize_hex(color_a)
    hex_b = normalize_hex(color_b)

    if hex_a is None:
        return hex_b or "#000000"

    if hex_b is None:
        return hex_a

    amount = max(0.0, min(1.0, float(amount)))

    r1, g1, b1 = hex_to_rgb(hex_a)
    r2, g2, b2 = hex_to_rgb(hex_b)

    red = r1 * (1.0 - amount) + r2 * amount
    green = g1 * (1.0 - amount) + g2 * amount
    blue = b1 * (1.0 - amount) + b2 * amount

    return rgb_to_hex(red, green, blue)


def adjust_color_for_contrast(
    foreground: str,
    background: str,
    target_ratio: float = WCAG_AAA_CONTRAST_RATIO,
    max_steps: int = 100
) -> Tuple[str, bool, float, float]:
    """
    Mathematically shift a foreground color until it reaches the target
    WCAG contrast ratio against the background.

    Returns:
    - final foreground hex
    - whether it changed
    - contrast before
    - contrast after
    """
    fg = normalize_hex(foreground)
    bg = normalize_hex(background)

    if fg is None:
        return foreground, False, 1.0, 1.0

    if bg is None:
        return fg, False, 1.0, 1.0

    before_ratio = contrast_ratio(fg, bg)

    if before_ratio >= target_ratio:
        return fg, False, before_ratio, before_ratio

    bg_luminance = relative_luminance(hex_to_rgb(bg))

    # If the background is light, darken the foreground toward black.
    # If the background is dark, lighten the foreground toward white.
    target_color = "#000000" if bg_luminance >= 0.5 else "#FFFFFF"

    best_color = fg
    best_ratio = before_ratio

    for step in range(1, max_steps + 1):
        amount = step / float(max_steps)
        candidate = mix_hex(fg, target_color, amount)
        candidate_ratio = contrast_ratio(candidate, bg)

        if candidate_ratio > best_ratio:
            best_color = candidate
            best_ratio = candidate_ratio

        if candidate_ratio >= target_ratio:
            return candidate, True, before_ratio, candidate_ratio

    changed = best_color != fg

    return best_color, changed, before_ratio, best_ratio


# ==========================================================
# COLOR STRUCTURE ADAPTATION
# ==========================================================

def _find_background_hex(data: Dict[str, Any]) -> str:
    """
    Find the most likely background color inside a token dictionary.
    """
    if not isinstance(data, dict):
        return "#FFFFFF"

    preferred_keys = (
        "background_color",
        "backgroundColor",
        "background",
        "surface_color",
        "surfaceColor",
        "canvas_color",
        "canvasColor",
        "base_color",
        "baseColor",
        "bg_color",
        "bgColor",
    )

    for key in preferred_keys:
        value = data.get(key)
        normalized = normalize_hex(value)

        if normalized is not None:
            return normalized

    # Fallback: search for any key that looks like a background.
    for key, value in data.items():
        key_lower = str(key).lower()

        if any(hint in key_lower for hint in BACKGROUND_KEY_HINTS):
            normalized = normalize_hex(value)

            if normalized is not None:
                return normalized

    return "#FFFFFF"


def _set_background_hex(data: Dict[str, Any], background_hex: str) -> Dict[str, Any]:
    """
    Set known background keys to the final background hex.
    """
    if not isinstance(data, dict):
        return data

    known_keys = (
        "background_color",
        "backgroundColor",
        "background",
        "surface_color",
        "surfaceColor",
        "canvas_color",
        "canvasColor",
        "bg_color",
        "bgColor",
    )

    for key in known_keys:
        if key in data:
            data[key] = background_hex

    if not any(key in data for key in known_keys):
        data["background_color"] = background_hex

    return data


def _adapt_color_structure(
    data: Any,
    background_hex: str,
    target_ratio: float,
    changes: Dict[str, Any],
    path: str = ""
) -> Any:
    """
    Recursively walk a token structure and adapt hex colors for contrast.
    """
    if isinstance(data, dict):
        adapted: Dict[str, Any] = {}

        for key, value in data.items():
            current_path = f"{path}.{key}" if path else str(key)

            if isinstance(value, dict) or isinstance(value, list):
                adapted[key] = _adapt_color_structure(
                    value,
                    background_hex,
                    target_ratio,
                    changes,
                    current_path
                )
                continue

            normalized = normalize_hex(value)

            if normalized is None:
                adapted[key] = value
                continue

            key_lower = str(key).lower()

            # Background colors are handled separately.
            if any(hint in key_lower for hint in BACKGROUND_KEY_HINTS):
                adapted[key] = normalized
                continue

            final_color, changed, before_ratio, after_ratio = adjust_color_for_contrast(
                foreground=normalized,
                background=background_hex,
                target_ratio=target_ratio
            )

            adapted[key] = final_color

            if changed:
                changes[current_path] = {
                    "old": value,
                    "new": final_color,
                    "contrast_before": before_ratio,
                    "contrast_after": after_ratio,
                    "target_ratio": target_ratio,
                }

        return adapted

    if isinstance(data, list):
        adapted_list: List[Any] = []

        for index, item in enumerate(data):
            item_path = f"{path}[{index}]"
            adapted_list.append(
                _adapt_color_structure(
                    item,
                    background_hex,
                    target_ratio,
                    changes,
                    item_path
                )
            )

        return adapted_list

    return data


# ==========================================================
# ACCESSIBILITY SYNTHESIZER
# ==========================================================

class AccessibilitySynthesizer:
    """
    The Visual Contrast & Audio Cue Adaptation Bridge.

    This engine reads AccessibilityDNA and reshapes:
    - DesignTokens
    - AtomicTokenSynthesizer data
    - AudioDNA

    It never writes raw CSS.
    It never writes raw audio code.
    It only produces adapted DNA and deterministic reports.
    """

    WCAG_AAA_CONTRAST_RATIO = WCAG_AAA_CONTRAST_RATIO

    AUDIO_AMPLIFICATION_DB: Dict[str, float] = {
        "off": 0.0,
        "low": 3.0,
        "medium": 6.0,
        "high": 10.0,
    }

    CRITICAL_FREQUENCY_BAND_HZ: List[int] = [1000, 4000]

    # ------------------------------------------------------
    # VISUAL CONTRAST ADAPTATION
    # ------------------------------------------------------

    def adapt_visual_contrast(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        design_tokens: Optional[Union[DesignTokens, Dict[str, Any]]] = None,
        atomic_tokens: Optional[Union[AtomicTokenSynthesizer, Dict[str, Any]]] = None
    ) -> Tuple[Any, Any, List[AdaptationEvent], Dict[str, Any]]:
        """
        Adapt visual tokens for WCAG AAA contrast when required.

        Returns:
        - adapted design tokens
        - adapted atomic tokens
        - adaptation events
        - deterministic report
        """
        accessibility_dna = _coerce_accessibility(accessibility)

        original_design_tokens = design_tokens
        original_atomic_tokens = atomic_tokens

        design_dict = _model_to_dict(design_tokens)
        atomic_dict = _model_to_dict(atomic_tokens)

        events: List[AdaptationEvent] = []
        changes: Dict[str, Any] = {}

        if accessibility_dna.visual_contrast_profile == "high_contrast":
            if not design_dict:
                design_dict = {
                    "background_color": "#FFFFFF",
                    "primary_color": "#000000",
                    "accent_color": "#0B57D0",
                    "accent_primary": "#0B57D0",
                }

            original_background = _find_background_hex(design_dict)
            background_luminance = relative_luminance(hex_to_rgb(original_background))

            # For high contrast, push the background to a deterministic extreme:
            # light backgrounds become white, dark backgrounds become black.
            extreme_background = "#FFFFFF" if background_luminance >= 0.5 else "#000000"

            if extreme_background != original_background:
                changes["background"] = {
                    "old": original_background,
                    "new": extreme_background,
                    "reason": "background_extreme_for_wcag_aaa",
                }

            design_dict = _adapt_color_structure(
                data=design_dict,
                background_hex=extreme_background,
                target_ratio=self.WCAG_AAA_CONTRAST_RATIO,
                changes=changes,
                path="design_tokens"
            )

            design_dict = _set_background_hex(design_dict, extreme_background)

            # Guarantee a readable text token.
            if "text_color" not in design_dict:
                text_color = "#000000" if extreme_background == "#FFFFFF" else "#FFFFFF"
                design_dict["text_color"] = text_color

                changes["design_tokens.text_color"] = {
                    "old": None,
                    "new": text_color,
                    "reason": "added_high_contrast_text_color",
                    "contrast_after": contrast_ratio(text_color, extreme_background),
                    "target_ratio": self.WCAG_AAA_CONTRAST_RATIO,
                }

            # Adapt atomic token colors if present.
            if atomic_dict:
                atomic_dict = _adapt_color_structure(
                    data=atomic_dict,
                    background_hex=extreme_background,
                    target_ratio=self.WCAG_AAA_CONTRAST_RATIO,
                    changes=changes,
                    path="atomic_tokens"
                )

            events.append(
                AdaptationEvent(
                    trigger_type="visual_contrast_profile",
                    adapted_system="ui_token_synthesizer"
                )
            )

        adapted_design_tokens = _wrap_like(
            original_design_tokens,
            design_dict,
            DesignTokens
        )

        adapted_atomic_tokens = _wrap_like(
            original_atomic_tokens,
            atomic_dict,
            AtomicTokenSynthesizer
        )

        report = {
            "visual_contrast_profile": accessibility_dna.visual_contrast_profile,
            "target_contrast_ratio": self.WCAG_AAA_CONTRAST_RATIO,
            "changed_color_tokens": len(changes),
            "changes": changes,
            "events": len(events),
        }

        return adapted_design_tokens, adapted_atomic_tokens, events, report

    # ------------------------------------------------------
    # AUDIO CUE ADAPTATION
    # ------------------------------------------------------

    def adapt_audio_cues(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        audio_dna: Optional[Union[AudioDNA, Dict[str, Any]]] = None
    ) -> Tuple[Any, List[AdaptationEvent], Dict[str, Any]]:
        """
        Adapt AudioDNA critical cue amplification using AccessibilityDNA.

        Returns:
        - adapted AudioDNA
        - adaptation events
        - deterministic report
        """
        accessibility_dna = _coerce_accessibility(accessibility)

        original_audio_dna = audio_dna
        audio_dict = _model_to_dict(audio_dna)

        mode = accessibility_dna.audio_cue_amplification
        boost_db = self.AUDIO_AMPLIFICATION_DB.get(mode, 0.0)

        old_mode = audio_dict.get("accessibility_audio_mode")
        old_boost_db = _safe_number(
            audio_dict.get(
                "critical_frequency_boost_db",
                audio_dict.get("danger_cue_amplification_db", 0.0)
            ),
            0.0
        )

        changed = False

        if audio_dict.get("accessibility_audio_mode") != mode:
            audio_dict["accessibility_audio_mode"] = mode
            changed = True

        if _safe_number(audio_dict.get("critical_frequency_boost_db"), None) != boost_db:
            audio_dict["critical_frequency_boost_db"] = boost_db
            changed = True

        if _safe_number(audio_dict.get("danger_cue_amplification_db"), None) != boost_db:
            audio_dict["danger_cue_amplification_db"] = boost_db
            changed = True

        if audio_dict.get("critical_frequency_band_hz") != self.CRITICAL_FREQUENCY_BAND_HZ:
            audio_dict["critical_frequency_band_hz"] = list(self.CRITICAL_FREQUENCY_BAND_HZ)
            changed = True

        # Critical danger cues should never be silent when amplification is requested.
        if mode != "off":
            if "filter_type" not in audio_dict or audio_dict.get("filter_type") == "none":
                audio_dict["critical_cue_filter_hint"] = "presence_boost"
            else:
                audio_dict["critical_cue_filter_hint"] = audio_dict.get("filter_type")

        events: List[AdaptationEvent] = []

        if changed or old_mode != mode:
            events.append(
                AdaptationEvent(
                    trigger_type="audio_cue_amplification",
                    adapted_system="dsp_audio_engine"
                )
            )

        adapted_audio_dna = _wrap_like(
            original_audio_dna,
            audio_dict,
            AudioDNA
        )

        report = {
            "audio_cue_amplification": mode,
            "previous_boost_db": old_boost_db,
            "new_boost_db": boost_db,
            "critical_frequency_band_hz": list(self.CRITICAL_FREQUENCY_BAND_HZ),
            "formula": "critical_cue_volume_db = base_cue_volume_db + accessibility_boost_db",
            "changed": changed,
            "events": len(events),
        }

        return adapted_audio_dna, events, report

    # ------------------------------------------------------
    # FULL ADAPTATION
    # ------------------------------------------------------

    def adapt_all(
        self,
        accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
        design_tokens: Optional[Union[DesignTokens, Dict[str, Any]]] = None,
        atomic_tokens: Optional[Union[AtomicTokenSynthesizer, Dict[str, Any]]] = None,
        audio_dna: Optional[Union[AudioDNA, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Adapt both visual tokens and audio DNA in one deterministic pass.
        """
        (
            adapted_design_tokens,
            adapted_atomic_tokens,
            visual_events,
            visual_report
        ) = self.adapt_visual_contrast(
            accessibility=accessibility,
            design_tokens=design_tokens,
            atomic_tokens=atomic_tokens
        )

        (
            adapted_audio_dna,
            audio_events,
            audio_report
        ) = self.adapt_audio_cues(
            accessibility=accessibility,
            audio_dna=audio_dna
        )

        all_events = visual_events + audio_events

        return {
            "design_tokens": adapted_design_tokens,
            "atomic_tokens": adapted_atomic_tokens,
            "audio_dna": adapted_audio_dna,
            "events": all_events,
            "report": {
                "visual": visual_report,
                "audio": audio_report,
                "total_events": len(all_events),
            },
        }


# ==========================================================
# MODULE-LEVEL DEFAULT SYNTHESIZER
# ==========================================================

default_accessibility_synthesizer = AccessibilitySynthesizer()


# ==========================================================
# CONVENIENCE FUNCTIONS
# ==========================================================

def adapt_visual_contrast(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    design_tokens: Optional[Union[DesignTokens, Dict[str, Any]]] = None,
    atomic_tokens: Optional[Union[AtomicTokenSynthesizer, Dict[str, Any]]] = None
) -> Tuple[Any, Any, List[AdaptationEvent], Dict[str, Any]]:
    """
    Module-level shortcut for visual contrast adaptation.
    """
    return default_accessibility_synthesizer.adapt_visual_contrast(
        accessibility=accessibility,
        design_tokens=design_tokens,
        atomic_tokens=atomic_tokens
    )


def adapt_audio_cues(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    audio_dna: Optional[Union[AudioDNA, Dict[str, Any]]] = None
) -> Tuple[Any, List[AdaptationEvent], Dict[str, Any]]:
    """
    Module-level shortcut for audio cue adaptation.
    """
    return default_accessibility_synthesizer.adapt_audio_cues(
        accessibility=accessibility,
        audio_dna=audio_dna
    )


def adapt_all(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    design_tokens: Optional[Union[DesignTokens, Dict[str, Any]]] = None,
    atomic_tokens: Optional[Union[AtomicTokenSynthesizer, Dict[str, Any]]] = None,
    audio_dna: Optional[Union[AudioDNA, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Module-level shortcut for full visual + audio adaptation.
    """
    return default_accessibility_synthesizer.adapt_all(
        accessibility=accessibility,
        design_tokens=design_tokens,
        atomic_tokens=atomic_tokens,
        audio_dna=audio_dna
    )