# packages/core/evolution_engine.py

import os
import json
from datetime import datetime
from packages.core.models import (
    EvolutionDNA, SystemBlueprint, 
    GuardrailCheckEnum, RegistrationStatusEnum
)
from typing import Dict, Any

# ==========================================================
# DAY 38: SELF-EVOLVING ARCHITECTURE (PILLAR 25)
# THE GUARDRAIL VALIDATOR, GENERATORS, & REGISTRAR
# ==========================================================

# 1. Existing engine names to prevent conflicts (Pillars 1-24)
EXISTING_ENGINE_NAMES = [
    "ui_synthesizer", "backend_compiler", "deployment_engine", "netcode_engine",
    "security_engine", "telemetry_engine", "input_engine", "modding_engine",
    "localization_engine", "economy_engine", "tutorial_engine", "chrono_engine",
    "accessibility_engine", "narrative_engine", "social_engine", "ecology_engine",
    "flow_engine", "content_weaver", "fidelity_engine", "universal_compiler",
    "evolution_engine" 
]

# 2. Existing templates to prevent overwriting pre-audited vaults
EXISTING_TEMPLATE_NAMES = [
    "base_html", "react_component", "svelte_component", "vanilla_js",
    "tailwind_css", "basic_route", "supabase_schema", "base_ui_shell"
]

# 3. Allowed safe types (NO RAW CODE ALLOWED)
ALLOWED_SCHEMA_TYPES = ["str", "int", "float", "bool", "list", "dict", "enum"]

# 4. Hardware Budget Guardrails (Protecting the i3 laptop)
HARDWARE_HIERARCHY = {
    "free": 0,
    "light": 1,
    "moderate": 2,
    "heavy": 3
}

CURRENT_HARDWARE_TIER = "potato" 
TIER_LIMITS = {
    "potato": 1,   
    "mid": 2,
    "high": 3,
    "ultra": 3,
    "cloud": 3
}

def validate_blueprint(dna: EvolutionDNA) -> Dict[str, Any]:
    """
    The Bouncer. Checks the EvolutionDNA against 5 strict guardrails.
    """
    failures = []

    # GUARDRAIL 1: SCHEMA CHECK
    for field in dna.new_schema_fields:
        if field.field_type not in ALLOWED_SCHEMA_TYPES:
            failures.append(f"SCHEMA CHECK FAILED: Invalid type '{field.field_type}' for '{field.field_name}'.")

    # GUARDRAIL 2: COMPILER CHECK
    if dna.new_compiler_type.value not in ["template_stamper", "json_mapper", "math_engine"]:
        failures.append(f"COMPILER CHECK FAILED: '{dna.new_compiler_type.value}' is not allowed.")

    # GUARDRAIL 3: TEMPLATE CHECK
    for template in dna.new_template_names:
        if template in EXISTING_TEMPLATE_NAMES:
            failures.append(f"TEMPLATE CHECK FAILED: '{template}' already exists.")

    # GUARDRAIL 4: NAME CHECK
    if dna.new_system_name in EXISTING_ENGINE_NAMES:
        failures.append(f"NAME CHECK FAILED: '{dna.new_system_name}' conflicts with an existing engine.")

    # GUARDRAIL 5: HARDWARE CHECK (Working Math)
    requested_cost_level = HARDWARE_HIERARCHY.get(dna.hardware_cost.value, 0)
    allowed_limit = TIER_LIMITS.get(CURRENT_HARDWARE_TIER, 1)
    
    if requested_cost_level > allowed_limit:
        failures.append(f"HARDWARE CHECK FAILED: '{dna.hardware_cost.value}' is too heavy for our '{CURRENT_HARDWARE_TIER}' laptop.")

    # --- THE VERDICT ---
    if failures:
        return {
            "status": "rejected",
            "guardrail_check": "failed",
            "failures": failures,
            "system_name": dna.new_system_name
        }
    else:
        blueprint = SystemBlueprint(
            system_name=dna.new_system_name,
            schema_definition={f.field_name: {"type": f.field_type, "default": f.default_value} for f in dna.new_schema_fields},
            compiler_definition={"type": dna.new_compiler_type.value},
            template_definitions=[{"name": t} for t in dna.new_template_names],
            registration_status=RegistrationStatusEnum.PENDING
        )
        
        return {
            "status": "approved",
            "guardrail_check": "passed",
            "blueprint": blueprint
        }

# ==========================================================
# STEP 3: THE SCHEMA GENERATOR (BLUEPRINT → PYDANTIC STRING)
# ==========================================================

def generate_schema(blueprint: SystemBlueprint) -> str:
    """
    Generates a Pydantic model definition AS A STRING.
    It does NOT execute the code. It saves it to a separate file for human review.
    """
    class_name = "".join(word.capitalize() for word in blueprint.system_name.split("_")) + "DNA"
    
    lines = [f"class {class_name}(BaseModel):"]
    
    TYPE_MAPPING = {
        "str": ("str", '""'),
        "int": ("int", "0"),
        "float": ("float", "0.0"),
        "bool": ("bool", "False"),
        "list": ("List[str]", "[]"),
        "dict": ("Dict[str, Any]", "{}"),
        "enum": ("str", '""')
    }
    
    for field_name, field_info in blueprint.schema_definition.items():
        field_type = field_info.get("type", "str")
        py_type, safe_default = TYPE_MAPPING.get(field_type, ("str", '""'))
        
        custom_default = field_info.get("default")
        if custom_default and str(custom_default).strip() not in ["", "None", "null"]:
            final_default = str(custom_default)
        else:
            final_default = safe_default
            
        lines.append(f"    {field_name}: {py_type} = {final_default}")
        
    schema_string = "\n".join(lines)
    
    dir_path = "packages/core/generated_schemas"
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"{blueprint.system_name}_schema.py")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("from pydantic import BaseModel\n")
        f.write("from typing import List, Dict, Any\n\n")
        f.write(schema_string)
        
    return schema_string

# ==========================================================
# STEP 4: THE COMPILER GENERATOR (BLUEPRINT → DETERMINISTIC COMPILER)
# ==========================================================

def generate_compiler(blueprint: SystemBlueprint) -> str:
    """
    Generates a deterministic compiler AS A STRING based on the compiler_type.
    Saves it to generated_compilers/ for human review. NO raw AI code is executed.
    """
    compiler_type = blueprint.compiler_definition.get("type", "template_stamper")
    system_name = blueprint.system_name
    
    compiler_code = ""
    
    if compiler_type == "template_stamper":
        compiler_code = f'''def compile_{system_name}(data: dict) -> str:
    """
    Deterministic Template Stamper for {system_name}.
    Reads JSON, injects variables into a pre-audited template string.
    """
    template = "Generated {system_name} output: " + ", ".join([f"{{k}}={{v}}" for k, v in data.items()])
    try:
        return template.format(**data)
    except KeyError:
        return "Error: Missing required template variables."
'''
    elif compiler_type == "json_mapper":
        mappings = ", ".join([f'"{k}": data.get("{k}", {repr(v.get("default", ""))})' for k, v in blueprint.schema_definition.items()])
        compiler_code = f'''def compile_{system_name}(data: dict) -> dict:
    """
    Deterministic JSON Mapper for {system_name}.
    Maps input JSON fields directly to output JSON fields.
    """
    return {{
        {mappings}
    }}
'''
    elif compiler_type == "math_engine":
        compiler_code = f'''def compile_{system_name}(data: dict) -> float:
    """
    Deterministic Math Engine for {system_name}.
    Applies a safe mathematical formula to the input parameters.
    """
    total = 0.0
    for key, value in data.items():
        if isinstance(value, (int, float)):
            total += float(value)
    return total
'''
    else:
        compiler_code = f'''def compile_{system_name}(data: dict):
    return "Error: Invalid compiler type."
'''

    dir_path = "packages/core/generated_compilers"
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"{system_name}_compiler.py")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(compiler_code)
        
    return compiler_code

# ==========================================================
# STEP 5: THE SYSTEM REGISTRAR (MAKING IT LIVE)
# ==========================================================

REGISTRY_PATH = "packages/core/system_registry.json"

def register_system(blueprint: SystemBlueprint) -> Dict[str, Any]:
    """
    Registers the validated blueprint into the system registry.
    The Universal Compiler reads this file to route to new systems dynamically.
    NO existing engine files are modified. Additive only.
    """
    # 1. Load existing registry or start fresh
    registry = {}
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except json.JSONDecodeError:
            registry = {} # Fallback to empty if corrupted

    # 2. Define paths for the generated files
    schema_path = f"packages/core/generated_schemas/{blueprint.system_name}_schema.py"
    compiler_path = f"packages/core/generated_compilers/{blueprint.system_name}_compiler.py"

    # 3. Create the registry entry
    registry_entry = {
        "system_name": blueprint.system_name,
        "schema_file_path": schema_path,
        "compiler_file_path": compiler_path,
        "template_names": [t.get("name", "") for t in blueprint.template_definitions],
        "status": "registered",
        "version": blueprint.version,
        "created_at": blueprint.created_at.isoformat()
    }

    # 4. Update registry and save
    registry[blueprint.system_name] = registry_entry
    
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)

    # 5. Mark blueprint as registered
    blueprint.registration_status = RegistrationStatusEnum.REGISTERED

    return {
        "status": "live",
        "message": f"System '{blueprint.system_name}' is now LIVE and registered.",
        "blueprint": blueprint
    }