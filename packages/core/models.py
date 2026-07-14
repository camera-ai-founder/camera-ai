from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal

# Our basic building blocks for the Ontological Brain
class OntologicalNode(BaseModel):
    id: str
    name: str
    type: str

class Edge(BaseModel):
    source: str
    target: str
    relationship: str

class Graph(BaseModel):
    nodes: List[OntologicalNode] = []
    edges: List[Edge] = []

# THE WORLD STATE (Our Memory Folder!)
class WorldState(BaseModel):
    """The persistent memory of our game world."""
    heat_level: int = Field(default=0, description="The current heat/wanted level")
    time_of_day: str = Field(default="12:00", description="In-game time")
    extra_attributes: Dict[str, Any] = Field(default_factory=dict, description="Flexible storage for any other world events")

# ==========================================
# DAY 12 MODELS: THE JUICE ENGINE
# ==========================================

class ImpactVector(BaseModel):
    """The mathematical DNA of a physical push."""
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    force: float = 0.0

class JuiceProfile(BaseModel):
    """The visual flavor and decay rate of an impact."""
    impact_type: str = "default" # e.g., "heavy_smash", "light_bounce", "glass_shatter"
    ragdoll_decay: float = 0.5   # How fast the wobble fades out (0.0 to 1.0)
    impact_vector: Optional[ImpactVector] = None

# ==========================================
# DAY 13 MODELS: THE TWO-TIER LOGIC
# ==========================================

class MuscleParameters(BaseModel):
    """
    TIER 1: Fast, real-time physics parameters. 
    The AI just sets these numbers, and JavaScript handles the actual movement.
    """
    speed: float = Field(default=5.0, description="Movement speed of the entity.")
    gravity: float = Field(default=9.8, description="Gravity strength.")
    dodge_chance: float = Field(default=0.1, description="Probability to dodge attacks (0.0 to 1.0).")
    jump_force: float = Field(default=10.0, description="How high the entity jumps.")

class BrainDirective(BaseModel):
    """
    TIER 2: Slow, narrative-level commands. 
    The AI uses this to tell the game to do big, story-driven things.
    """
    action_type: str = Field(description="The high-level action, e.g., 'spawn_enemy', 'change_weather'.")
    target: Optional[str] = Field(default=None, description="What the action applies to, e.g., 'player', 'forest'.")
    intensity: int = Field(default=50, description="How strong the action is, from 1 to 100.")

# ==========================================
# DAY 13 STEP 4: THE DRAMA BUDGET GUARDRAILS
# ==========================================

class DramaBudget(BaseModel):
    """
    Mathematical guardrails to prevent the AI from crashing the browser 
    with infinite spawns or excessive chaos.
    """
    max_entities: int = Field(
        default=10, 
        ge=1, le=50,
        description="Absolute maximum number of new entities allowed to spawn this turn."
    )
    max_tension: int = Field(
        default=50, 
        ge=0, le=100, 
        description="Tension level from 0 (calm) to 100 (pure chaos)."
    )
    max_projectiles: int = Field(
        default=5, 
        ge=0, le=20, 
        description="Maximum number of active projectiles allowed on screen."
    )

class TwoTierOutput(BaseModel):
    """
    The master output schema. We will force Groq to always return this exact JSON structure.
    """
    muscle_params: MuscleParameters = Field(description="Settings for the fast physics engine.")
    brain_directives: List[BrainDirective] = Field(
        default_factory=list, 
        description="A list of high-level narrative commands for the game engine to process."
    )
    drama_budget: DramaBudget = Field(
        default_factory=DramaBudget,
        description="Strict limits on how much chaos the AI is allowed to generate."
    )

# ==========================================
# DAY 14 MODELS: APP DNA & DESIGN TOKENS
# ==========================================

class DesignTokens(BaseModel):
    """The visual and motion DNA of the generated UI. The AI must fill this out."""
    accent_primary: str = Field(..., description="Hex code for the primary brand color, e.g., '#3B82F6'")
    spacing_unit: int = Field(..., description="Base padding/margin multiplier in pixels, usually 4 or 8")
    motion_entrance: str = Field(..., description="Framer Motion entrance animation type, e.g., 'fade-in-up' or 'scale-in'")

class AppComponent(BaseModel):
    """A single pre-audited component required for the app."""
    component_name: str = Field(..., description="The exact name of the component from our Template Vault, e.g., 'NavBar' or 'DataGrid'")
    props: Dict[str, Any] = Field(default_factory=dict, description="Specific properties to pass to the component.")

class AppDNA(BaseModel):
    """The structural DNA of the requested application."""
    entity_name: str = Field(..., description="The name of the core entity this app manages, e.g., 'User Dashboard'")
    required_components: List[AppComponent] = Field(..., description="Ordered list of components needed to render this app.")

# ==========================================
# DAY 15 MODELS: THE GENESIS RENDERER (PILLAR 11)
# ==========================================

class ParametricGenome(BaseModel):
    """Priority 1: The mathematical DNA to grow 3D objects using pure math."""
    seed: int = Field(..., description="A deterministic math seed (0-9999) to grow the exact same shape every time.")
    rules: List[str] = Field(default_factory=list, description="L-System rules or CSG operations to grow the topology.")
    scale_factor: float = Field(1.0, description="Global scale multiplier for the generated math object.")

class VisualQuery(BaseModel):
    """Priority 2: The search parameters for our CC0 Asset Swarm fallback."""
    search_terms: List[str] = Field(..., description="Keywords to search the CC0 asset API (e.g., ['gothic', 'gargoyle']).")
    fallback_flag: bool = Field(False, description="True if parametric math is insufficient and we MUST download a 3D model.")
    max_poly_count: int = Field(10000, description="Hard limit for downloaded assets to protect the browser RAM.")

class CameraAction(BaseModel):
    """Priority 4: The AI Cinematographer's deterministic camera movements."""
    movement_type: Literal["static", "shaky_cam", "orbit", "dolly_zoom", "tracking"] = Field("static")
    duration_seconds: float = Field(3.0, description="How long the camera movement lasts.")
    intensity: float = Field(1.0, description="Strength of the camera effect (e.g., how violent the shaky_cam is).")

class VFXProfile(BaseModel):
    """Priority 5: Mathematical parameters for cinematic post-processing effects."""
    fog_density: float = Field(0.0, description="Volumetric fog thickness (0.0 to 1.0).")
    rain_intensity: float = Field(0.0, description="Screen-space rain amount (0.0 to 1.0).")
    neon_reflection: float = Field(0.0, description="Wet street neon bounce intensity (0.0 to 1.0).")

# ==========================================
# DAY 16 MODELS: INFINITE BIOMES & SCATTER MATH
# ==========================================

class ScatterRule(BaseModel):
    """Deterministic rules for placing Genesis assets based on environmental math."""
    asset_type: str = Field(..., description="The specific Genesis asset to spawn (e.g., 'parametric_pine_tree', 'neon_shack').")
    noise_threshold: float = Field(..., description="The minimum noise value (0.0 to 1.0) required to trigger this spawn.")
    density_multiplier: float = Field(default=1.0, description="How heavily this asset populates when the threshold is met.")

class BiomeDNA(BaseModel):
    """The mathematical recipe for an ecosystem, preventing random object hallucinations."""
    name: str = Field(..., description="The thematic name of the biome (e.g., 'Toxic Wasteland', 'High-Tech Forest').")
    elevation_curve: float = Field(..., description="The base height of the terrain (0.0 is a deep trench, 1.0 is a mountain peak).")
    moisture_level: float = Field(..., description="How wet the biome is (0.0 is dry/desert, 1.0 is dense/rainforest).")
    scatter_density: float = Field(..., description="The overall tightness of the object packing (0.0 is sparse, 1.0 is highly dense).")
    scatter_rules: List[ScatterRule] = Field(default_factory=list, description="The logical rules for placing Genesis assets based on the environment's math.")