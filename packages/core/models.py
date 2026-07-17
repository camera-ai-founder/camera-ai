from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Literal, Union
from enum import Enum
import uuid
import time

# ==========================================================
# 1. PROCEDURAL PRIMITIVES & MATERIALS
# ==========================================================
class PrimitiveType(str, Enum):
    CUBE = "cube"
    SPHERE = "sphere"
    CAPSULE = "capsule"
    CYLINDER = "cylinder"
    CUSTOM_MESH = "custom_mesh"

class MaterialDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    albedo_color: str = Field(default="#FFFFFF")
    roughness: float = Field(default=0.5)
    metallic: float = Field(default=0.0)
    emissive_intensity: float = Field(default=0.0)
    texture_url: Optional[str] = None

class ProceduralPrimitiveDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: PrimitiveType = PrimitiveType.CUBE
    dimensions: List[float] = Field(default=[1.0, 1.0, 1.0])
    material: MaterialDNA = Field(default_factory=MaterialDNA)
    segments: int = Field(default=16)

# ==========================================================
# 2. RAPIER WASM PHYSICS ENGINE
# ==========================================================
class ColliderType(str, Enum):
    CUBOID = "cuboid"
    SPHERE = "sphere"
    CAPSULE = "capsule"
    TRIMESH = "trimesh"

class ColliderDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    shape: ColliderType = ColliderType.CUBOID
    friction: float = Field(default=0.7)
    restitution: float = Field(default=0.1)
    is_sensor: bool = Field(default=False)
    half_extents: List[float] = Field(default=[0.5, 0.5, 0.5])

class RigidBodyDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    body_type: Literal["dynamic", "kinematic", "fixed"] = "dynamic"
    mass: float = Field(default=1.0)
    linear_damping: float = Field(default=0.1)
    angular_damping: float = Field(default=0.1)
    lock_translations: List[bool] = Field(default=[False, False, False])
    lock_rotations: List[bool] = Field(default=[False, False, False])

class PhysicsDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    gravity: List[float] = Field(default=[0.0, -9.81, 0.0])
    timestep: float = Field(default=1.0/60.0)
    max_substeps: int = Field(default=5)

# ==========================================================
# 3 & 11. DRAMA BUDGETS & ONTOLOGICAL GENESIS RENDERER
# ==========================================================
class CullingStrategy(str, Enum):
    FRUSTUM = "frustum"
    OCCLUSION = "occlusion"
    DISTANCE = "distance"

class RendererPriorityTier(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"

class CullingRules(BaseModel):
    model_config = ConfigDict(extra="allow")
    strategies: List[CullingStrategy] = Field(default=[CullingStrategy.FRUSTUM, CullingStrategy.DISTANCE])
    max_render_distance: float = Field(default=500.0)
    occlusion_culling_resolution: int = Field(default=256)

class PriorityDualEngineDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    primary_engine: Literal["webgl", "webgpu"] = "webgpu"
    fallback_engine: Literal["webgl", "none"] = "webgl"
    culling_rules: CullingRules = Field(default_factory=CullingRules)
    enable_shadows: bool = Field(default=True)
    shadow_map_resolution: int = 2048
    tier_budgets: dict = Field(default_factory=dict)
    vfx_complexity: str = Field(default="medium") # ADDED FOR DAY 23 HEALING

class DramaBudget(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_entities: int = Field(default=500)
    max_particles: int = Field(default=10000)
    max_lights: int = Field(default=8)
    max_draw_calls: int = Field(default=200)

# ==========================================================
# 4. LITE ECS (ENTITY COMPONENT SYSTEM)
# ==========================================================
class ComponentRegistry(BaseModel):
    model_config = ConfigDict(extra="allow")
    transform: bool = True
    mesh_renderer: bool = True
    rigid_body: bool = False
    network_sync: bool = False
    custom_scripts: List[str] = Field(default_factory=list)

class EntityArchetype(BaseModel):
    model_config = ConfigDict(extra="allow")
    archetype_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    components: ComponentRegistry = Field(default_factory=ComponentRegistry)
    initial_prefab: Optional[str] = None

class LiteECSDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    archetypes: List[EntityArchetype] = Field(default_factory=list)
    chunk_size: int = Field(default=64)
    enable_parallel_systems: bool = Field(default=True)

# ==========================================================
# 5. GLSL BREATHING SHADERS
# ==========================================================
class UniformMapping(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    type: str
    default_value: Union[float, List[float], str]

class ShaderDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    vertex_code: str = Field(default="")
    fragment_code: str = Field(default="")
    uniforms: List[UniformMapping] = Field(default_factory=list)
    breathing_amplitude: float = Field(default=0.05)
    breathing_speed: float = Field(default=1.0)

# ==========================================================
# 6 & 7. META-PROMPT AUTHORING & NARRATIVE CONTEXT PRUNING
# ==========================================================
class TokenBudgets(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_context_tokens: int = Field(default=4000)
    max_prompt_tokens: int = Field(default=1000)
    max_response_tokens: int = Field(default=2000)

class PruningStrategy(str, Enum):
    RECENCY = "recency"
    SEMANTIC_RELEVANCE = "semantic_relevance"
    IMPORTANCE_SCORE = "importance_score"

class NarrativeContextDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    token_budgets: TokenBudgets = Field(default_factory=TokenBudgets)
    pruning_strategy: PruningStrategy = PruningStrategy.SEMANTIC_RELEVANCE
    embedding_model: str = Field(default="text-embedding-3-small")

class MetaPromptDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    system_prompt_template: str = Field(default="You are the Genesis Engine...")
    context_injection_points: List[str] = Field(default=["world_state", "drama_budget"])
    force_json_output: bool = Field(default=True)

# ==========================================================
# 8. TWO-TIER LATENCY LOGIC
# ==========================================================
class LatencyTier(str, Enum):
    LOCAL = "local"
    EDGE = "edge"
    CLOUD = "cloud"

class FallbackRules(BaseModel):
    model_config = ConfigDict(extra="allow")
    primary_tier: LatencyTier = LatencyTier.LOCAL
    fallback_tier: LatencyTier = LatencyTier.CLOUD
    timeout_ms: int = Field(default=500)
    max_retries: int = Field(default=2)

class TwoTierLatencyDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    rules: FallbackRules = Field(default_factory=FallbackRules)
    predictive_prefetch: bool = Field(default=True)

# ==========================================================
# 9 & 10. ONTOLOGICAL UI COMPILER & ATOMIC TOKEN SYNTHESIZER
# ==========================================================
class ThemeScale(BaseModel):
    model_config = ConfigDict(extra="allow")
    spacing: List[int] = Field(default=[0, 4, 8, 16, 32, 64])
    font_sizes: List[int] = Field(default=[12, 14, 16, 20, 24, 32])
    border_radii: List[int] = Field(default=[0, 4, 8, 16])

class AtomicTokenSynthesizer(BaseModel):
    model_config = ConfigDict(extra="allow")
    base_theme: str = Field(default="default")
    scale: ThemeScale = Field(default_factory=ThemeScale)
    generate_css_variables: bool = Field(default=True)

class UIComponentDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    component_type: str
    variant: str = Field(default="primary")
    states: List[str] = Field(default=["default", "hover", "active", "disabled"])

class OntologicalUICompiler(BaseModel):
    model_config = ConfigDict(extra="allow")
    framework: Literal["react", "svelte", "vanilla"] = "react"
    styling_engine: Literal["tailwind", "css_modules", "styled_components"] = "tailwind"
    components: List[UIComponentDNA] = Field(default_factory=list)
    atomic_tokens: AtomicTokenSynthesizer = Field(default_factory=AtomicTokenSynthesizer)

# ==========================================================
# DAY 23: TELEMETRY & SELF-HEALING
# ==========================================================
class BottleneckType(str, Enum):
    RENDER = "render"
    PHYSICS = "physics"
    LOGIC = "logic"
    NETWORK = "network"
    COMPILATION = "compilation"
    NONE = "none"

class TelemetryDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    fps_threshold: float = Field(default=60.0)
    max_memory_mb: int = Field(default=512)
    max_compile_time_ms: int = Field(default=1000)
    self_heal_enabled: bool = Field(default=True)

class PerformanceReport(BaseModel):
    model_config = ConfigDict(extra="allow")
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ms: int = Field(default=0)
    current_fps: float = Field(default=60.0)
    dropped_frames: int = Field(default=0)
    memory_usage_mb: float = Field(default=0.0)
    bottleneck_component: Optional[str] = Field(default="none")

# ==========================================================
# DAY 24: PROCEDURAL DSP SYNTHESIS (THE AUDIO HOLE)
# ==========================================================
class AudioDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    waveform_type: Literal["sine", "square", "sawtooth", "triangle", "noise"] = Field(default="sine", description="The mathematical shape of the sound wave")
    base_frequency: float = Field(default=440.0, description="The base pitch in Hertz (Hz)")
    envelope_attack: float = Field(default=0.05, description="How fast the sound reaches full volume (in seconds)")
    envelope_decay: float = Field(default=0.5, description="How fast the sound fades out (in seconds)")
    filter_type: Literal["lowpass", "highpass", "bandpass", "none"] = Field(default="none", description="Frequencies to cut off to shape the tone")

# ==========================================================
# MASTER APP DNA (THE SINGLE SOURCE OF TRUTH)
# ==========================================================
class OntologicalNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    semantic_tags: List[str] = Field(default_factory=list)
    entity_archetype: Optional[str] = None
    audio: Optional[AudioDNA] = Field(default=None, description="Procedural DNA for mathematically synthesized sound")

class WorldState(BaseModel):
    model_config = ConfigDict(extra="allow")
    nodes: List[OntologicalNode] = Field(default_factory=list)
    global_gravity: List[float] = Field(default=[0.0, -9.81, 0.0])
    heat_level: int = Field(default=0)
    time_of_day: str = Field(default="12:00")

class DesignTokens(BaseModel):
    model_config = ConfigDict(extra="allow")
    primary_color: str = Field(default="#0F172A")
    accent_color: str = Field(default="#38BDF8")
    background_color: str = Field(default="#FFFFFF")
    accent_primary: str = Field(default="#3B82F6")
    spacing_unit: int = Field(default=8)
    motion_entrance: str = Field(default="fade-in-up")

class AppComponent(BaseModel):
    model_config = ConfigDict(extra="allow")
    component_name: str = Field(default="DefaultComponent")
    props: dict = Field(default_factory=dict)

class AppDNA(BaseModel):
    model_config = ConfigDict(extra="allow", title="Master AppDNA Genesis")
    
    app_name: str = Field(default="Genesis Engine v1")
    version: str = Field(default="0.1.0")
    entity_name: str = Field(default="Genesis App")
    
    world_state: WorldState = Field(default_factory=WorldState)
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    
    primitives: List[ProceduralPrimitiveDNA] = Field(default_factory=list)
    physics: PhysicsDNA = Field(default_factory=PhysicsDNA)
    drama_budget: DramaBudget = Field(default_factory=DramaBudget)
    ecs: LiteECSDNA = Field(default_factory=LiteECSDNA)
    shaders: List[ShaderDNA] = Field(default_factory=list)
    narrative_context: NarrativeContextDNA = Field(default_factory=NarrativeContextDNA)
    meta_prompt: MetaPromptDNA = Field(default_factory=MetaPromptDNA)
    latency_logic: TwoTierLatencyDNA = Field(default_factory=TwoTierLatencyDNA)
    ui_compiler: OntologicalUICompiler = Field(default_factory=OntologicalUICompiler)
    renderer: PriorityDualEngineDNA = Field(default_factory=PriorityDualEngineDNA)
    
    required_components: List[AppComponent] = Field(default_factory=list)
    telemetry: TelemetryDNA = Field(default_factory=TelemetryDNA)

# ==========================================================
# DAY 12, 15, 16, 17, 18, 20, 21 & 22 RESTORATION
# (The Final, Unbreakable Missing Links)
# ==========================================================
class ImpactVector(BaseModel):
    model_config = ConfigDict(extra="allow")
    force: float = Field(default=10.0)
    angle: float = Field(default=45.0)
    duration_ms: int = Field(default=500)

class JuiceProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    impact_type: str = Field(default="default")
    ragdoll_decay: float = Field(default=0.5)
    impact_vector: ImpactVector = Field(default_factory=ImpactVector)

class ChangedNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    node_id: str
    new_state: dict = Field(default_factory=dict)

class StateDelta(BaseModel):
    model_config = ConfigDict(extra="allow")
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    changed_nodes: List[ChangedNode] = Field(default_factory=list)
    changed_tokens: dict = Field(default_factory=dict)
    removed_node_ids: List[str] = Field(default_factory=list)

class VisualQuery(BaseModel):
    model_config = ConfigDict(extra="allow")
    search_terms: List[str] = Field(default_factory=list)
    fallback_flag: bool = Field(default=False)
    max_poly_count: int = Field(default=10000)

class SecurityDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_payload_size: int = Field(default=1048576)
    allowed_keys: List[str] = Field(default_factory=list)
    restricted_characters: List[str] = Field(default_factory=list)
    strict_mode: bool = Field(default=True)

# --- DAY 15 ADDITIONS ---
class ParametricGenome(BaseModel):
    model_config = ConfigDict(extra="allow")
    seed: int = Field(default=0)
    rules: List[str] = Field(default_factory=list)
    scale_factor: float = Field(default=1.0)

class CameraAction(BaseModel):
    model_config = ConfigDict(extra="allow")
    movement_type: str = Field(default="static")
    duration_seconds: float = Field(default=0.0)
    intensity: float = Field(default=0.0)

class VFXProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    fog_density: float = Field(default=0.0)
    rain_intensity: float = Field(default=0.0)
    neon_reflection: float = Field(default=0.0)

# --- DAY 16 ADDITIONS ---
class ScatterRule(BaseModel):
    model_config = ConfigDict(extra="allow")
    asset_type: str = Field(default="tree")
    noise_threshold: float = Field(default=0.5)
    density_multiplier: float = Field(default=1.0)

class BiomeDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(default="Default Biome")
    elevation_curve: float = Field(default=0.5)
    moisture_level: float = Field(default=0.5)
    scatter_density: float = Field(default=0.5)
    scatter_rules: List[ScatterRule] = Field(default_factory=list)

# --- DAY 17 ADDITIONS ---
class NavMeshDNA(BaseModel): # ADDED
    model_config = ConfigDict(extra="allow")
    grid_resolution: float = Field(default=1.0)
    agent_radius: float = Field(default=0.5)
    agent_height: float = Field(default=2.0)
    max_slope: float = Field(default=45.0)

class PathingIntent(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_id: str = Field(default="entity_1")
    start_coords: list = Field(default_factory=list)
    target_coords: list = Field(default_factory=list)

# --- DAY 18 ADDITIONS ---
class Route(BaseModel):
    model_config = ConfigDict(extra="allow")
    method: str = Field(default="GET")
    path: str = Field(default="/")

class LogicDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    entity_name: str = Field(default="Entity")
    routes: List[Route] = Field(default_factory=list)
    auth_type: str = Field(default="None")
    database_schema: str = Field(default="")

# --- DAY 20 ADDITIONS ---
class DeployDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    target_environment: str = Field(default="docker")
    port_mappings: dict = Field(default_factory=dict)
    env_variables: dict = Field(default_factory=dict)
    asset_cdn_url: Optional[str] = Field(default=None)

# ==========================================================
# CRITICAL ALIASES FOR BACKWARD COMPATIBILITY
# ==========================================================
# The Telemetry Engine (Step 3) imports 'GenesisRenderer' directly.
# We alias it to our master PriorityDualEngineDNA to prevent import errors.
GenesisRenderer = PriorityDualEngineDNA