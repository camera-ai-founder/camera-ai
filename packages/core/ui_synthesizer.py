import time
import logging
import copy
from typing import Any, Dict, Optional, Tuple, List, Union

from pydantic import BaseModel

try:
    from .models import (
        DesignTokens,
        AppDNA,
        BottleneckType,
        LocaleDNA,
        AccessibilityDNA,
        AdaptationEvent,
    )
except ImportError:
    from packages.core.models import (
        DesignTokens,
        AppDNA,
        BottleneckType,
        LocaleDNA,
        AccessibilityDNA,
        AdaptationEvent,
    )

try:
    from .templates import TEMPLATE_VAULT
except ImportError:
    from packages.core.templates import TEMPLATE_VAULT

try:
    from .accessibility_synthesizer import default_accessibility_synthesizer
except ImportError:
    try:
        from packages.core.accessibility_synthesizer import default_accessibility_synthesizer
    except ImportError:
        default_accessibility_synthesizer = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UISynthesizer")


# ==========================================================
# DAY 31: SAFE ACCESSIBILITY HELPERS
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


def _coerce_accessibility(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]]
) -> Optional[AccessibilityDNA]:
    """
    Convert incoming accessibility data into a clean AccessibilityDNA object.
    """
    if accessibility is None:
        return None

    if isinstance(accessibility, AccessibilityDNA):
        return accessibility

    try:
        return AccessibilityDNA(**accessibility)
    except Exception:
        return AccessibilityDNA()


def _normalize_hex(color: Any) -> Optional[str]:
    """
    Normalize a color string into #RRGGBB format.
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


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert #RRGGBB into (red, green, blue).
    """
    clean = _normalize_hex(hex_color)

    if clean is None:
        return (0, 0, 0)

    clean = clean[1:]

    red = int(clean[0:2], 16)
    green = int(clean[2:4], 16)
    blue = int(clean[4:6], 16)

    return (red, green, blue)


def _rgb_to_hex(red: int, green: int, blue: int) -> str:
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


def _relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG relative luminance.
    """
    red, green, blue = rgb

    r = _channel_to_linear(red)
    g = _channel_to_linear(green)
    b = _channel_to_linear(blue)

    return (0.2126 * r) + (0.7152 * g) + (0.0722 * b)


def _contrast_ratio(color_a: str, color_b: str) -> float:
    """
    Calculate the WCAG contrast ratio between two hex colors.
    """
    hex_a = _normalize_hex(color_a)
    hex_b = _normalize_hex(color_b)

    if hex_a is None or hex_b is None:
        return 1.0

    lum_a = _relative_luminance(_hex_to_rgb(hex_a))
    lum_b = _relative_luminance(_hex_to_rgb(hex_b))

    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)

    ratio = (lighter + 0.05) / (darker + 0.05)

    return round(ratio, 3)


def _mix_hex(color_a: str, color_b: str, amount: float) -> str:
    """
    Mix two hex colors.

    amount = 0.0 returns color_a.
    amount = 1.0 returns color_b.
    """
    hex_a = _normalize_hex(color_a)
    hex_b = _normalize_hex(color_b)

    if hex_a is None:
        return hex_b or "#000000"

    if hex_b is None:
        return hex_a

    amount = max(0.0, min(1.0, float(amount)))

    r1, g1, b1 = _hex_to_rgb(hex_a)
    r2, g2, b2 = _hex_to_rgb(hex_b)

    red = r1 * (1.0 - amount) + r2 * amount
    green = g1 * (1.0 - amount) + g2 * amount
    blue = b1 * (1.0 - amount) + b2 * amount

    return _rgb_to_hex(red, green, blue)


def _adjust_color_for_contrast(
    foreground: str,
    background: str,
    target_ratio: float = WCAG_AAA_CONTRAST_RATIO,
    max_steps: int = 100
) -> Tuple[str, bool, float, float]:
    """
    Mathematically shift a foreground color until it reaches the target
    WCAG contrast ratio against the background.
    """
    fg = _normalize_hex(foreground)
    bg = _normalize_hex(background)

    if fg is None:
        return foreground, False, 1.0, 1.0

    if bg is None:
        return fg, False, 1.0, 1.0

    before_ratio = _contrast_ratio(fg, bg)

    if before_ratio >= target_ratio:
        return fg, False, before_ratio, before_ratio

    bg_luminance = _relative_luminance(_hex_to_rgb(bg))

    # If the background is light, darken the foreground toward black.
    # If the background is dark, lighten the foreground toward white.
    target_color = "#000000" if bg_luminance >= 0.5 else "#FFFFFF"

    best_color = fg
    best_ratio = before_ratio

    for step in range(1, max_steps + 1):
        amount = step / float(max_steps)
        candidate = _mix_hex(fg, target_color, amount)
        candidate_ratio = _contrast_ratio(candidate, bg)

        if candidate_ratio > best_ratio:
            best_color = candidate
            best_ratio = candidate_ratio

        if candidate_ratio >= target_ratio:
            return candidate, True, before_ratio, candidate_ratio

    changed = best_color != fg

    return best_color, changed, before_ratio, best_ratio


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
        normalized = _normalize_hex(value)

        if normalized is not None:
            return normalized

    # Fallback: search for any key that looks like a background.
    for key, value in data.items():
        key_lower = str(key).lower()

        if any(hint in key_lower for hint in BACKGROUND_KEY_HINTS):
            normalized = _normalize_hex(value)

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

            normalized = _normalize_hex(value)

            if normalized is None:
                adapted[key] = value
                continue

            key_lower = str(key).lower()

            # Background colors are handled separately.
            if any(hint in key_lower for hint in BACKGROUND_KEY_HINTS):
                adapted[key] = normalized
                continue

            final_color, changed, before_ratio, after_ratio = _adjust_color_for_contrast(
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


def _adapt_design_tokens_accessibility(
    tokens: Optional[Union[DesignTokens, Dict[str, Any]]],
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]]
) -> Tuple[DesignTokens, List[AdaptationEvent], Dict[str, Any]]:
    """
    Adapt DesignTokens using AccessibilityDNA.

    If the Accessibility Synthesizer bridge exists, use it.
    If not, use the built-in local WCAG fallback.
    """
    accessibility_dna = _coerce_accessibility(accessibility)

    if tokens is None:
        tokens = DesignTokens()

    if accessibility_dna is None:
        if isinstance(tokens, DesignTokens):
            return tokens, [], {}

        try:
            return DesignTokens(**tokens), [], {}
        except Exception:
            return DesignTokens(), [], {}

    # Preferred path: use the dedicated Accessibility Synthesizer.
    if default_accessibility_synthesizer is not None:
        try:
            adapted_tokens, _, events, report = default_accessibility_synthesizer.adapt_visual_contrast(
                accessibility=accessibility_dna,
                design_tokens=tokens
            )

            if not isinstance(adapted_tokens, DesignTokens):
                adapted_tokens = DesignTokens(**adapted_tokens)

            return adapted_tokens, events, report

        except Exception as e:
            logger.warning(f"Accessibility Synthesizer bridge failed, falling back to local WCAG math: {e}")

    # Fallback path: local deterministic WCAG adaptation.
    if accessibility_dna.visual_contrast_profile != "high_contrast":
        if isinstance(tokens, DesignTokens):
            return tokens, [], {}

        try:
            return DesignTokens(**tokens), [], {}
        except Exception:
            return DesignTokens(), [], {}

    token_dict = _model_to_dict(tokens)

    if not token_dict:
        token_dict = _model_to_dict(DesignTokens())

    original_background = _find_background_hex(token_dict)
    background_luminance = _relative_luminance(_hex_to_rgb(original_background))

    # For high contrast, push the background to a deterministic extreme:
    # light backgrounds become white, dark backgrounds become black.
    extreme_background = "#FFFFFF" if background_luminance >= 0.5 else "#000000"

    changes: Dict[str, Any] = {}

    if extreme_background != original_background:
        changes["background"] = {
            "old": original_background,
            "new": extreme_background,
            "reason": "background_extreme_for_wcag_aaa",
        }

    token_dict = _adapt_color_structure(
        data=token_dict,
        background_hex=extreme_background,
        target_ratio=WCAG_AAA_CONTRAST_RATIO,
        changes=changes,
        path="design_tokens"
    )

    token_dict = _set_background_hex(token_dict, extreme_background)

    if "text_color" not in token_dict:
        text_color = "#000000" if extreme_background == "#FFFFFF" else "#FFFFFF"
        token_dict["text_color"] = text_color

        changes["design_tokens.text_color"] = {
            "old": None,
            "new": text_color,
            "reason": "added_high_contrast_text_color",
            "contrast_after": _contrast_ratio(text_color, extreme_background),
            "target_ratio": WCAG_AAA_CONTRAST_RATIO,
        }

    events = [
        AdaptationEvent(
            trigger_type="visual_contrast_profile",
            adapted_system="ui_token_synthesizer"
        )
    ]

    report = {
        "visual_contrast_profile": accessibility_dna.visual_contrast_profile,
        "target_contrast_ratio": WCAG_AAA_CONTRAST_RATIO,
        "changed_color_tokens": len(changes),
        "changes": changes,
        "events": len(events),
    }

    try:
        adapted_tokens = DesignTokens(**token_dict)
    except Exception:
        adapted_tokens = DesignTokens()

    return adapted_tokens, events, report


# ==========================================================
# DAY 27: THE FLUIDITY ENGINE
# ==========================================================

def _get_fluid_classes_and_css(locale: LocaleDNA) -> tuple:
    """
    DAY 27: THE FLUIDITY ENGINE.
    Returns Tailwind classes for the main container and a global CSS override 
    for inner elements to prevent layout breaks in long-word languages.
    """
    classes = []
    css_override = ""
    
    if not locale:
        return "", ""

    # 1. Global Text Wrapping Rules (From FluidUIRules)
    if locale.fluid_ui_rules.force_text_wrap:
        classes.append("break-words")
        classes.append("hyphens-auto")
        
    # 2. Container Flexibility
    classes.append("flex-wrap") 
    classes.append("min-w-0") 
    
    # 3. Language-Specific Heuristics (The "Long Word" Defense)
    long_word_languages = ['de', 'ru', 'pl', 'fi', 'nl']
    if locale.target_language in long_word_languages:
        classes.append("whitespace-normal")
        classes.append("text-ellipsis")
        
        # Inject a global CSS override to force ALL text inside the templates to wrap
        css_override = """
  /* DAY 27: FLUIDITY OVERRIDE FOR LONG-WORD LANGUAGES */
  p, span, h1, h2, h3, h4, h5, h6, button, a, div {
    word-break: break-word;
    overflow-wrap: anywhere;
    hyphens: auto;
  }
  .flex-container, .grid, .flex {
    flex-wrap: wrap;
  }
"""
        
    return " ".join(classes), css_override


# ==========================================================
# DAY 10 / DAY 12 TOKEN SYNTHESIZER
# DAY 31: NOW ACCESSIBILITY-AWARE
# ==========================================================

def synthesize_design_tokens(
    tokens: DesignTokens,
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None
) -> dict:
    """
    Translates the AI's semantic DesignTokens into strict Tailwind CSS 
    and Framer Motion configuration dictionaries.

    Day 31:
    If AccessibilityDNA requests high contrast, the tokens are mathematically
    adapted toward WCAG AAA contrast before synthesis.
    """
    accessible_tokens, accessibility_events, accessibility_report = _adapt_design_tokens_accessibility(
        tokens=tokens,
        accessibility=accessibility
    )

    motion_variants = {
        "fade-in-up": {
            "initial": {"opacity": 0, "y": 20},
            "animate": {"opacity": 1, "y": 0, "transition": {"duration": 0.5}}
        },
        "scale-in": {
            "initial": {"opacity": 0, "scale": 0.9},
            "animate": {"opacity": 1, "scale": 1, "transition": {"duration": 0.4}}
        }
    }
    
    # Fallback safely if the attribute doesn't exist on older DNA
    motion_entrance = getattr(accessible_tokens, 'motion_entrance', 'fade-in-up')
    selected_motion = motion_variants.get(motion_entrance, motion_variants["fade-in-up"])

    # Day 31:
    # Expand the CSS variable system so the UI can render accessible contrast.
    accent_primary = getattr(
        accessible_tokens,
        'accent_primary',
        getattr(accessible_tokens, 'accent_color', '#3B82F6')
    )

    background_color = getattr(accessible_tokens, 'background_color', '#FFFFFF')
    text_color = getattr(accessible_tokens, 'text_color', '#0F172A')
    primary_color = getattr(accessible_tokens, 'primary_color', '#0F172A')
    accent_color = getattr(accessible_tokens, 'accent_color', '#38BDF8')

    synthesized_config = {
        "css_variables": {
            "--color-accent-primary": accent_primary,
            "--color-background": background_color,
            "--color-text": text_color,
            "--color-primary": primary_color,
            "--color-accent": accent_color,
            "--spacing-base": f"{getattr(accessible_tokens, 'spacing_unit', 8)}px"
        },
        "framer_motion": selected_motion,
        "accessibility_events": accessibility_events,
        "accessibility_report": accessibility_report,
    }
    
    return synthesized_config


# ==========================================================
# ONTOLOGICAL UI COMPILER
# ==========================================================

def compile_ui(app_dna: AppDNA, design_config: dict) -> dict:
    """
    The Ontological UI Compiler.
    Stitches the pre-audited templates into one massive React file string,
    while measuring the exact compile time for the Telemetry Black Box.

    Day 31:
    The compiler now reads AppDNA.accessibility and adapts visual tokens
    before stamping the final React output.
    """
    logger.info("🏭 UI Synthesizer: Starting React template stamp...")
    
    # 1. START THE STOPWATCH
    start_time = time.perf_counter()
    
    try:
        # --- DAY 27: EXTRACT LOCALE DNA AND GENERATE FLUIDITY OVERRIDES ---
        locale = getattr(app_dna, 'locale', None)
        fluid_classes, fluid_css_override = _get_fluid_classes_and_css(locale)
        locale_name = getattr(locale, 'target_language', 'en').upper() if locale else 'EN'

        # --- DAY 31: EXTRACT ACCESSIBILITY DNA AND ADAPT DESIGN TOKENS ---
        accessibility = getattr(app_dna, 'accessibility', None)
        accessibility_dna = _coerce_accessibility(accessibility)
        design_tokens = getattr(app_dna, 'design_tokens', DesignTokens())

        accessible_design_config = synthesize_design_tokens(
            tokens=design_tokens,
            accessibility=accessibility_dna
        )

        # Merge the incoming design_config with the accessible design_config.
        # Accessible truth wins for color variables.
        if not isinstance(design_config, dict):
            design_config = {}

        merged_design_config = copy.deepcopy(design_config)
        merged_css_variables = merged_design_config.get("css_variables", {})

        merged_css_variables.update(
            accessible_design_config.get("css_variables", {})
        )

        merged_design_config["css_variables"] = merged_css_variables

        if "framer_motion" not in merged_design_config:
            merged_design_config["framer_motion"] = accessible_design_config.get("framer_motion")

        design_config = merged_design_config

        # --- YOUR ORIGINAL DAY 12 LOGIC (Protected & Enhanced) ---
        react_file = "import React from 'react';\nimport { motion } from 'framer-motion';\n\n"
        
        css_vars = design_config.get("css_variables", {})

        accent = css_vars.get("--color-accent-primary", "#3B82F6")
        spacing = css_vars.get("--spacing-base", "8px")

        # Day 31 accessible color variables.
        background = css_vars.get("--color-background", "#FFFFFF")
        text_color = css_vars.get("--color-text", "#0F172A")
        primary = css_vars.get("--color-primary", "#0F172A")
        accent_color = css_vars.get("--color-accent", accent)
        
        # Note: We use double braces {{ }} here so Python outputs literal { } for CSS
        react_file += f"""
const globalStyles = `
  :root {{
    --color-accent-primary: {accent};
    --color-background: {background};
    --color-text: {text_color};
    --color-primary: {primary};
    --color-accent: {accent_color};
    --spacing-base: {spacing};
  }}
  {fluid_css_override}
`;
"""
        rendered_components = []

        # Safely get required_components, defaulting to empty list if missing
        required_components = getattr(app_dna, 'required_components', [])
        
        for comp in required_components:
            comp_name = getattr(comp, 'component_name', 'Unknown')
            if comp_name in TEMPLATE_VAULT:
                react_file += f"\n// --- {comp_name} Component ---\n"
                react_file += TEMPLATE_VAULT[comp_name]
                rendered_components.append(comp_name)
            else:
                logger.warning(f"Warning: {comp_name} not found in Vault. Skipping safely.")
                
        component_tags = "".join([f"<{name} />" for name in rendered_components])
        entity_name = getattr(app_dna, 'entity_name', 'GenesisApp')
        
        # DAY 27 FIX: Properly escaping braces for Python f-strings vs React JSX
        # DAY 31: Added accessible background and text color variables.
        react_file += f"""
// --- Main {entity_name} App ---
const App = () => {{
  return (
    <div
      className="min-h-screen bg-gray-50 p-8 {fluid_classes}"
      style={{{{ backgroundColor: 'var(--color-background)', color: 'var(--color-text)' }}}}
    >
      <style>{{globalStyles}}</style>
      <h1 className="text-4xl font-bold mb-8" style={{{{ color: 'var(--color-accent-primary)' }}}}>
        {entity_name} <span className="text-sm font-normal opacity-50">({locale_name})</span>
      </h1>
      <div className="space-y-8 flex flex-col">
        {component_tags}
      </div>
    </div>
  );
}};

export default App;
"""
        # --- END OF YOUR ORIGINAL LOGIC ---

        # 2. STOP THE STOPWATCH
        end_time = time.perf_counter()
        compile_time_ms = (end_time - start_time) * 1000
        
        # 3. EVALUATE AGAINST TELEMETRY DNA
        bottleneck = BottleneckType.NONE

        # Safely get the telemetry limit, defaulting to 1000ms if not present
        telemetry_dna = getattr(app_dna, 'telemetry', None)
        max_time = getattr(telemetry_dna, 'max_compile_time_ms', 1000)
        
        if compile_time_ms > max_time:
            logger.warning(f"⚠️ UI Compiler took {compile_time_ms:.2f}ms! Exceeds limit of {max_time}ms.")
            bottleneck = BottleneckType.COMPILATION
        else:
            logger.info(f"✅ UI Compiler finished in {compile_time_ms:.2f}ms. Healthy.")

        accessibility_visual_profile = (
            accessibility_dna.visual_contrast_profile
            if accessibility_dna is not None
            else "standard"
        )

        # 4. RETURN THE COMPILATION REPORT (Code + Metrics)
        return {
            "success": True,
            "code": react_file,
            "compile_time_ms": round(compile_time_ms, 2),
            "bottleneck_component": bottleneck,
            "accessibility_visual_profile": accessibility_visual_profile,
            "accessibility_events": len(accessible_design_config.get("accessibility_events", [])),
            "accessibility_report": accessible_design_config.get("accessibility_report", {}),
        }

    except Exception as e:
        logger.error(f"❌ UI Synthesis failed: {e}")
        return {
            "success": False,
            "code": "",
            "compile_time_ms": 0.0,
            "bottleneck_component": BottleneckType.COMPILATION
        }