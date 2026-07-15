# packages/core/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal, Tuple
from datetime import datetime

# ==========================================
# DAY 22 MODELS: THE SECURITY DNA (Zero-Trust Vault)
# ==========================================
class SecurityDNA(BaseModel):
    """The mathematical vault rules to prevent memory overload and injection attacks."""
    max_payload_size: int = Field(
        1048576, 
        description="Max payload size in bytes (1MB default to prevent memory attacks)"
    )
    allowed_keys: List[str] = Field(
        default_factory=list, 
        description="Explicitly allowed keys for strict parsing"
    )
    restricted_characters: List[str] = Field(
        default_factory=lambda: ["<", ">", ";", "--", "/*", "*/"], 
        description="Forbidden SQL/XSS injection characters"
    )

# ==========================================
# OUR BASIC BUILDING BLOCKS
# ==========================================
class OntologicalNode(BaseModel):
    id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)

class Edge(BaseModel):
    source: str = Field(..., max_length=50)
    target: str = Field(..., max_length=50)
    relationship: str = Field(..., max_length=50)

class Graph(BaseModel):
    nodes: List[OntologicalNode] = []
    edges: List[Edge] = []

# THE WORLD STATE (Our Memory Folder!)
class WorldState(BaseModel):
    """The persistent memory of our game world."""
    heat_level: int = Field(default=0, description="The current heat/wanted level")
    time_of_day: str = Field(default="12:00", max_length=10, description="In-game time")
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
    impact_type: str = Field("default", max_length=50) # e.g., "heavy_smash", "light_bounce"
    ragdoll_decay: float = 0.5   
    impact_vector: Optional[ImpactVector] = None

# ==========================================
# DAY 13 MODELS: THE TWO-TIER LOGIC
# ==========================================

class MuscleParameters(BaseModel):
    """TIER 1: Fast, real-time physics parameters."""
    speed: float = Field(default=5.0, description="Movement speed of the entity.")
    gravity: float = Field(default=9.8, description="Gravity strength.")
    dodge_chance: float = Field(default=0.1, description="Probability to dodge attacks (0.0 to 1.0).")
    jump_force: float = Field(default=10.0, description="How high the entity jumps.")

class BrainDirective(BaseModel):
    """TIER 2: Slow, narrative-level commands."""
    action_type: str = Field(..., max_length=50, description="The high-level action.")
    target: Optional[str] = Field(default=None, max_length=50, description="What the action applies to.")
    intensity: int = Field(default=50, description="How strong the action is, from 1 to 100.")

class DramaBudget(BaseModel):
    """Mathematical guardrails to prevent the AI from crashing the browser."""
    max_entities: int = Field(default=10, ge=1, le=50, description="Absolute max entities.")
    max_tension: int = Field(default=50, ge=0, le=100, description="Tension level 0-100.")
    max_projectiles: int = Field(default=5, ge=0, le=20, description="Max active projectiles.")

class TwoTierOutput(BaseModel):
    """The master output schema for Groq."""
    muscle_params: MuscleParameters = Field(description="Settings for the fast physics engine.")
    brain_directives: List[BrainDirective] = Field(default_factory=list)
    drama_budget: DramaBudget = Field(default_factory=DramaBudget)

# ==========================================
# DAY 14 MODELS: APP DNA & DESIGN TOKENS
# ==========================================

class DesignTokens(BaseModel):
    """The visual and motion DNA of the generated UI."""
    accent_primary: str = Field(..., max_length=20, description="Hex code for the primary brand color.")
    spacing_unit: int = Field(..., description="Base padding/margin multiplier in pixels.")
    motion_entrance: str = Field(..., max_length=50, description="Framer Motion entrance animation type.")

class AppComponent(BaseModel):
    """A single pre-audited component required for the app."""
    component_name: str = Field(..., max_length=50, description="The exact name of the component.")
    props: Dict[str, Any] = Field(default_factory=dict)

class AppDNA(BaseModel):
    """The structural DNA of the requested application."""
    entity_name: str = Field(..., max_length=100, description="The name of the core entity.")
    required_components: List[AppComponent] = Field(...)
    
    # DAY 22 ADDITION: The Security DNA strand
    security: SecurityDNA = Field(
        default_factory=SecurityDNA, 
        description="The Zero-Trust security rules for this app."
    )

# ==========================================
# DAY 15 MODELS: THE GENESIS RENDERER (PILLAR 11)
# ==========================================

class ParametricGenome(BaseModel):
    """Priority 1: The mathematical DNA to grow 3D objects using pure math."""
    seed: int = Field(...)
    rules: List[str] = Field(default_factory=list)
    scale_factor: float = Field(1.0)

class VisualQuery(BaseModel):
    """Priority 2: The search parameters for our CC0 Asset Swarm fallback."""
    search_terms: List[str] = Field(...)
    fallback_flag: bool = Field(False)
    max_poly_count: int = Field(10000)

class CameraAction(BaseModel):
    """Priority 4: The AI Cinematographer's deterministic camera movements."""
    movement_type: Literal["static", "shaky_cam", "orbit", "dolly_zoom", "tracking"] = Field("static")
    duration_seconds: float = Field(3.0)
    intensity: float = Field(1.0)

class VFXProfile(BaseModel):
    """Priority 5: Mathematical parameters for cinematic post-processing effects."""
    fog_density: float = Field(0.0)
    rain_intensity: float = Field(0.0)
    neon_reflection: float = Field(0.0)

# ==========================================
# DAY 16 MODELS: INFINITE BIOMES & SCATTER MATH
# ==========================================

class ScatterRule(BaseModel):
    """Deterministic rules for placing Genesis assets."""
    asset_type: str = Field(..., max_length=100)
    noise_threshold: float = Field(...)
    density_multiplier: float = Field(default=1.0)

class BiomeDNA(BaseModel):
    """The mathematical recipe for an ecosystem."""
    name: str = Field(..., max_length=50)
    elevation_curve: float = Field(...)
    moisture_level: float = Field(...)
    scatter_density: float = Field(...)
    scatter_rules: List[ScatterRule] = Field(default_factory=list)

# ==========================================
# DAY 17 MODELS: THE NAVIGATION HOLE 
# ==========================================

class NavMeshDNA(BaseModel):
    """The mathematical blueprint for our walkable terrain grid."""
    grid_resolution: float = Field(default=1.0)
    walkable_threshold: float = Field(default=0.5)

class PathingIntent(BaseModel):
    """The AI's simple declaration of WHERE it wants to go."""
    entity_id: str = Field(..., max_length=50)
    start_coords: Tuple[float, float] = Field(...)
    target_coords: Tuple[float, float] = Field(...)

# ==========================================
# DAY 18 MODELS: THE BACKEND DNA COMPILER
# ==========================================

class Route(BaseModel):
    """Defines a single API endpoint."""
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(...)
    path: str = Field(..., max_length=200)

class LogicDNA(BaseModel):
    """The DNA for our backend architecture."""
    entity_name: str = Field(..., max_length=100)
    routes: List[Route] = Field(...)
    auth_type: Literal["JWT", "OAuth", "API_Key", "Public", "None"] = Field(...)
    database_schema: str = Field(..., max_length=2000)

# ==========================================
# DAY 20 MODELS: THE DEPLOYMENT DNA
# ==========================================

class DeployDNA(BaseModel):
    """The Deployment DNA."""
    target_environment: str = Field(..., max_length=50)
    port_mappings: Dict[int, int] = Field(default_factory=dict)
    env_variables: Dict[str, str] = Field(default_factory=dict)
    asset_cdn_url: Optional[str] = Field(None, max_length=500)

# ==========================================
# DAY 21 MODELS: THE MULTIPLAYER HOLE 
# ==========================================

class NetworkDNA(BaseModel):
    """The rulebook for how this specific world communicates."""
    sync_rate_hz: float = Field(default=10.0)
    authoritative_source: str = Field(default="server", max_length=50)
    max_delta_size_kb: int = Field(default=50)

class StateDelta(BaseModel):
    """The exact mathematical difference between two world states."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changed_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    changed_tokens: Dict[str, Any] = Field(default_factory=dict)
    removed_node_ids: List[str] = Field(default_factory=list)