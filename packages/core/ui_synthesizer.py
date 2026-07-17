import time
import logging
from .models import DesignTokens, AppDNA, BottleneckType, LocaleDNA
from .templates import TEMPLATE_VAULT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UISynthesizer")

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

def synthesize_design_tokens(tokens: DesignTokens) -> dict:
    """
    Translates the AI's semantic DesignTokens into strict Tailwind CSS 
    and Framer Motion configuration dictionaries. (Unchanged from Day 12)
    """
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
    motion_entrance = getattr(tokens, 'motion_entrance', 'fade-in-up')
    selected_motion = motion_variants.get(motion_entrance, motion_variants["fade-in-up"])

    synthesized_config = {
        "css_variables": {
            "--color-accent-primary": getattr(tokens, 'accent_primary', '#3B82F6'),
            "--spacing-base": f"{getattr(tokens, 'spacing_unit', 8)}px"
        },
        "framer_motion": selected_motion
    }
    
    return synthesized_config


def compile_ui(app_dna: AppDNA, design_config: dict) -> dict:
    """
    The Ontological UI Compiler.
    Stitches the pre-audited templates into one massive React file string,
    while measuring the exact compile time for the Telemetry Black Box.
    """
    logger.info("🏭 UI Synthesizer: Starting React template stamp...")
    
    # 1. START THE STOPWATCH
    start_time = time.perf_counter()
    
    try:
        # --- DAY 27: EXTRACT LOCALE DNA AND GENERATE FLUIDITY OVERRIDES ---
        locale = getattr(app_dna, 'locale', None)
        fluid_classes, fluid_css_override = _get_fluid_classes_and_css(locale)
        locale_name = getattr(locale, 'target_language', 'en').upper() if locale else 'EN'

        # --- YOUR ORIGINAL DAY 12 LOGIC (Protected & Enhanced) ---
        react_file = "import React from 'react';\nimport { motion } from 'framer-motion';\n\n"
        
        css_vars = design_config.get("css_variables", {})
        accent = css_vars.get("--color-accent-primary", "#3B82F6")
        spacing = css_vars.get("--spacing-base", "8px")
        
        # Note: We use double braces {{ }} here so Python outputs literal { } for CSS
        react_file += f"""
const globalStyles = `
  :root {{
    --color-accent-primary: {accent};
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
        # 1. {fluid_classes} injects the Python string directly into the HTML class attribute.
        # 2. {{globalStyles}} tells Python to output literal {globalStyles} for React.
        # 3. {{{{ color: ... }}}} tells Python to output literal {{ color: ... }} for React inline styles.
        react_file += f"""
// --- Main {entity_name} App ---
const App = () => {{
  return (
    <div className="min-h-screen bg-gray-50 p-8 {fluid_classes}">
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

        # 4. RETURN THE COMPILATION REPORT (Code + Metrics)
        return {
            "success": True,
            "code": react_file,
            "compile_time_ms": round(compile_time_ms, 2),
            "bottleneck_component": bottleneck
        }

    except Exception as e:
        logger.error(f"❌ UI Synthesis failed: {e}")
        return {
            "success": False,
            "code": "",
            "compile_time_ms": 0.0,
            "bottleneck_component": BottleneckType.COMPILATION
        }