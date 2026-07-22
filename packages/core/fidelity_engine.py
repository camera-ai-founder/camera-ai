# packages/core/fidelity_engine.py

import logging
import random
from packages.core.models import (
    FidelityDNA, 
    FidelityRoute, 
    RenderPipeline, 
    HardwareTier,
    ShaderProfile
)

# Set up a simple logger for our downgrade and fallback events
logger = logging.getLogger("fidelity_engine")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ==============================================================================
# STEP 2: THE FIDELITY ROUTER (THE TRAFFIC COP)
# ==============================================================================

def resolve_fidelity(dna: FidelityDNA) -> FidelityRoute:
    """
    The Traffic Cop. Checks what the Brain wants against what the hardware can handle.
    Resolves the actual render pipeline.
    """
    max_level_map = {
        HardwareTier.POTATO: 2,
        HardwareTier.MID: 3,
        HardwareTier.HIGH: 4,
        HardwareTier.ULTRA: 5,
        HardwareTier.CLOUD: 5
    }
    
    max_level = max_level_map.get(dna.hardware_tier, 2)
    
    requested_level = dna.fidelity_level
    resolved_level = requested_level
    fallback_level = requested_level
    
    if requested_level > max_level:
        resolved_level = max_level
        fallback_level = max_level
        logger.info(
            f"[FIDELITY DOWNGRADE] Entity '{dna.entity_id}' requested L{requested_level}, "
            f"but {dna.hardware_tier.value} hardware maxes out at L{max_level}. "
            f"Downgrading safely to protect the i3 laptop."
        )
        
    pipeline_map = {
        0: RenderPipeline.PRIMITIVE,
        1: RenderPipeline.SDF,
        2: RenderPipeline.PROCEDURAL_MESH,
        3: RenderPipeline.GAUSSIAN_SPLAT,
        4: RenderPipeline.ASSET_SWARM,
        5: RenderPipeline.AI_GENERATED
    }
    
    render_pipeline = pipeline_map.get(resolved_level, RenderPipeline.PRIMITIVE)
    
    load_estimates = {
        0: 0.5,
        1: 2.0,
        2: 5.0,
        3: 50.0,
        4: 150.0,
        5: 500.0
    }
    estimated_load_ms = load_estimates.get(resolved_level, 5.0)
    
    return FidelityRoute(
        entity_id=dna.entity_id,
        resolved_level=resolved_level,
        render_pipeline=render_pipeline,
        fallback_level=fallback_level,
        estimated_load_ms=estimated_load_ms
    )


# ==============================================================================
# STEP 3: LEVEL 0 RENDERER (PRIMITIVE ASSEMBLY)
# ==============================================================================

def render_l0_primitive(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """
    Generates a Three.js JSON descriptor using pure primitives (L0).
    Outputs instant, lightweight math that the existing renderer understands.
    """
    shape_map = {
        "character": [
            {"type": "box", "role": "body"},
            {"type": "sphere", "role": "head"}
        ],
        "tree": [
            {"type": "cylinder", "role": "trunk"},
            {"type": "sphere", "role": "leaves"}
        ],
        "building": [
            {"type": "box", "role": "base"},
            {"type": "box", "role": "roof"}
        ],
        "vehicle": [
            {"type": "box", "role": "body"},
            {"type": "cylinder", "role": "wheel_fl"},
            {"type": "cylinder", "role": "wheel_fr"},
            {"type": "cylinder", "role": "wheel_bl"},
            {"type": "cylinder", "role": "wheel_br"}
        ]
    }
    
    shapes = shape_map.get(entity_type.lower(), [{"type": "box", "role": "default"}])
    
    material_map = {
        ShaderProfile.TOON: "MeshToonMaterial",
        ShaderProfile.PBR: "MeshStandardMaterial",
        ShaderProfile.UNLIT: "MeshBasicMaterial",
        ShaderProfile.CUSTOM: "ShaderMaterial"
    }
    material_type = material_map.get(dna.shader_profile, "MeshStandardMaterial")
    
    three_js_descriptor = {
        "entity_id": entity_id,
        "fidelity_level": 0,
        "pipeline": "primitive",
        "children": []
    }
    
    for shape in shapes:
        color = dna.color_palette.get(shape["role"], "#FFFFFF")
        
        child_mesh = {
            "geometry": shape["type"],
            "material": {
                "type": material_type,
                "color": color
            },
            "role": shape["role"]
        }
        three_js_descriptor["children"].append(child_mesh)
        
    return three_js_descriptor


# ==============================================================================
# STEP 4: LEVEL 1 RENDERER (SDF - SIGNED DISTANCE FIELDS)
# ==============================================================================

def render_l1_sdf(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """
    Generates a JSON descriptor for a Signed Distance Field shader (L1).
    SDFs describe shapes using pure math equations instead of polygons.
    """
    sdf_map = {
        "character": {
            "primitives": [
                {"sdf_type": "capsule", "role": "body"},
                {"sdf_type": "sphere", "role": "head"}
            ],
            "blend_mode": "union"
        },
        "tree": {
            "primitives": [
                {"sdf_type": "cylinder", "role": "trunk"},
                {"sdf_type": "sphere", "role": "canopy"}
            ],
            "blend_mode": "union"
        },
        "building": {
            "primitives": [
                {"sdf_type": "box", "role": "structure"},
                {"sdf_type": "box", "role": "windows", "operation": "subtract"}
            ],
            "blend_mode": "subtract"
        },
        "rock": {
            "primitives": [
                {"sdf_type": "sphere", "role": "base"},
                {"sdf_type": "sphere", "role": "detail"}
            ],
            "blend_mode": "union"
        }
    }
    
    sdf_config = sdf_map.get(entity_type.lower(), {
        "primitives": [{"sdf_type": "sphere", "role": "default"}],
        "blend_mode": "union"
    })
    
    primary_color = dna.color_palette.get("primary", "#888888")
    
    sdf_descriptor = {
        "entity_id": entity_id,
        "fidelity_level": 1,
        "pipeline": "sdf",
        "shader_template": "sdf_raymarch_template", 
        "blend_mode": sdf_config["blend_mode"],
        "primitives": [],
        "global_color": primary_color,
        "style_tags": dna.style_tags
    }
    
    for prim in sdf_config["primitives"]:
        color = dna.color_palette.get(prim["role"], primary_color)
        sdf_prim = {
            "sdf_type": prim["sdf_type"],
            "role": prim["role"],
            "color": color,
            "operation": prim.get("operation", "union")
        }
        sdf_descriptor["primitives"].append(sdf_prim)
    
    return sdf_descriptor


# ==============================================================================
# STEP 4: LEVEL 2 RENDERER (PROCEDURAL MESH - L-SYSTEMS)
# ==============================================================================

def render_l2_procedural(entity_id: str, entity_type: str, dna: FidelityDNA, seed: int = None) -> dict:
    """
    Generates a JSON descriptor for procedural mesh generation (L2).
    Uses L-System grammars to 'grow' complex shapes from simple rules.
    """
    if seed is None:
        seed = hash(entity_id) % 100000
    
    grammar_map = {
        "tree": {
            "axiom": "F",
            "rules": {"F": "FF+[+F-F-F]-[-F+F+F]"},
            "iterations": 4,
            "angle": 25.0,
            "length": 10.0,
            "description": "Classic fractal tree with branching"
        },
        "bush": {
            "axiom": "X",
            "rules": {"X": "F[+X][-X]FX", "F": "FF"},
            "iterations": 5,
            "angle": 30.0,
            "length": 5.0,
            "description": "Dense bushy vegetation"
        },
        "building": {
            "axiom": "B",
            "rules": {"B": "B[+W][-W]B", "W": "WW"},
            "iterations": 3,
            "angle": 90.0,
            "length": 15.0,
            "description": "CSG-style stacked building blocks"
        },
        "character": {
            "axiom": "T",
            "rules": {"T": "T[+A][-A]T", "A": "AF"},
            "iterations": 2,
            "angle": 45.0,
            "length": 8.0,
            "description": "Abstract procedural humanoid silhouette"
        }
    }
    
    grammar_config = grammar_map.get(entity_type.lower(), {
        "axiom": "F",
        "rules": {"F": "F+F-F"},
        "iterations": 3,
        "angle": 60.0,
        "length": 10.0,
        "description": "Default procedural shape"
    })
    
    primary_color = dna.color_palette.get("primary", "#44AA44")
    
    procedural_descriptor = {
        "entity_id": entity_id,
        "fidelity_level": 2,
        "pipeline": "procedural_mesh",
        "method": "lsystem",
        "grammar": {
            "axiom": grammar_config["axiom"],
            "rules": grammar_config["rules"],
            "iterations": grammar_config["iterations"],
            "angle": grammar_config["angle"],
            "length": grammar_config["length"]
        },
        "seed": seed,
        "color_palette": dna.color_palette if dna.color_palette else {"primary": primary_color},
        "style_tags": dna.style_tags,
        "description": grammar_config["description"],
        "compatible_renderer": "parametric_breeder" 
    }
    
    return procedural_descriptor


# ==============================================================================
# STEP 5: LEVEL 3-5 HOOKS (FUTURE PIPELINES & GRACEFUL FALLBACK)
# ==============================================================================

def render_l3_hook(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """Stub for Phase 6 (Gaussian Splatting)."""
    return {
        "entity_id": entity_id, "fidelity_level": 3, "pipeline": "gaussian_splat",
        "status": "not_yet_implemented", "fallback": "l2_procedural",
        "planned_phase": "Phase 6 (Days 1826-2190)"
    }

def render_l4_hook(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """Stub for Phase 6 (Asset Swarm)."""
    return {
        "entity_id": entity_id, "fidelity_level": 4, "pipeline": "asset_swarm",
        "status": "not_yet_implemented", "fallback": "l2_procedural",
        "planned_phase": "Phase 6 (Days 1826-2190)"
    }

def render_l5_hook(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """Stub for Phase 6 (AI-Generated)."""
    return {
        "entity_id": entity_id, "fidelity_level": 5, "pipeline": "ai_generated",
        "status": "not_yet_implemented", "fallback": "l2_procedural",
        "planned_phase": "Phase 6 (Days 1826-2190)"
    }


# ==============================================================================
# THE MASTER DISPATCHER (TIES IT ALL TOGETHER)
# ==============================================================================

def render_entity(entity_id: str, entity_type: str, dna: FidelityDNA) -> dict:
    """
    The Master Dispatcher. Routes the entity to the correct renderer.
    If L3-L5 are requested, it catches the 'not_yet_implemented' stub
    and automatically falls back to L2 (Procedural Mesh) so the render never breaks.
    """
    # First, the Traffic Cop resolves the route
    route = resolve_fidelity(dna)
    
    # Then, we dispatch to the correct pipeline
    if route.render_pipeline == RenderPipeline.PRIMITIVE:
        return render_l0_primitive(entity_id, entity_type, dna)
        
    elif route.render_pipeline == RenderPipeline.SDF:
        return render_l1_sdf(entity_id, entity_type, dna)
        
    elif route.render_pipeline == RenderPipeline.PROCEDURAL_MESH:
        return render_l2_procedural(entity_id, entity_type, dna)
        
    elif route.render_pipeline == RenderPipeline.GAUSSIAN_SPLAT:
        hook_result = render_l3_hook(entity_id, entity_type, dna)
        logger.info(f"[GRACEFUL FALLBACK] L3 not built yet. Falling back to L2 for {entity_id}.")
        return render_l2_procedural(entity_id, entity_type, dna)
        
    elif route.render_pipeline == RenderPipeline.ASSET_SWARM:
        hook_result = render_l4_hook(entity_id, entity_type, dna)
        logger.info(f"[GRACEFUL FALLBACK] L4 not built yet. Falling back to L2 for {entity_id}.")
        return render_l2_procedural(entity_id, entity_type, dna)
        
    elif route.render_pipeline == RenderPipeline.AI_GENERATED:
        hook_result = render_l5_hook(entity_id, entity_type, dna)
        logger.info(f"[GRACEFUL FALLBACK] L5 not built yet. Falling back to L2 for {entity_id}.")
        return render_l2_procedural(entity_id, entity_type, dna)
        
    # Ultimate safety net: if something goes completely wrong, draw a box.
    return render_l0_primitive(entity_id, entity_type, dna)