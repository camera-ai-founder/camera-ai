# packages/core/ui_synthesizer.py

from .models import DesignTokens, AppDNA
from .templates import TEMPLATE_VAULT

def synthesize_design_tokens(tokens: DesignTokens) -> dict:
    """
    Translates the AI's semantic DesignTokens into strict Tailwind CSS 
    and Framer Motion configuration dictionaries.
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
    
    selected_motion = motion_variants.get(tokens.motion_entrance, motion_variants["fade-in-up"])

    synthesized_config = {
        "css_variables": {
            "--color-accent-primary": tokens.accent_primary,
            "--spacing-base": f"{tokens.spacing_unit}px"
        },
        "framer_motion": selected_motion
    }
    
    return synthesized_config


def compile_ui(app_dna: AppDNA, design_config: dict) -> str:
    """
    The Ontological UI Compiler.
    It takes the AppDNA (the parts list) and stitches the pre-audited
    templates from our Vault into one massive, flawless React file string.
    """
    
    # 1. Start the file with basic React imports
    react_file = "import React from 'react';\nimport { motion } from 'framer-motion';\n\n"
    
    # 2. Extract CSS variables from our synthesized tokens
    css_vars = design_config.get("css_variables", {})
    accent = css_vars.get("--color-accent-primary", "#3B82F6")
    spacing = css_vars.get("--spacing-base", "8px")
    
    # Create a global style block so the whole app shares the AI's chosen colors
    react_file += f"""
const globalStyles = `
  :root {{
    --color-accent-primary: {accent};
    --spacing-base: {spacing};
  }}
`;
"""

    # 3. Fetch components from the Vault and stitch them in
    rendered_components = []
    for comp in app_dna.required_components:
        # If the component exists in our secure vault, we use it.
        if comp.component_name in TEMPLATE_VAULT:
            react_file += f"\n// --- {comp.component_name} Component ---\n"
            react_file += TEMPLATE_VAULT[comp.component_name]
            rendered_components.append(comp.component_name)
        else:
            # Failsafe: If the AI hallucinates a component name not in our vault, we safely skip it.
            print(f"Warning: {comp.component_name} not found in Vault. Skipping safely.")
            
    # 4. Build the final Main App layout that holds everything together
    # We join the names to create tags like <NavBar /> and <DataGrid />
    component_tags = "".join([f"<{name} />" for name in rendered_components])
    
    react_file += f"""
// --- Main {app_dna.entity_name} App ---
const App = () => {{
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <style>{{globalStyles}}</style>
      <h1 className="text-4xl font-bold mb-8" style={{ color: 'var(--color-accent-primary)' }}>
        {app_dna.entity_name}
      </h1>
      <div className="space-y-8">
        {component_tags}
      </div>
    </div>
  );
}};

export default App;
"""
    
    return react_file