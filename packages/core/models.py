# packages/core/models.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Literal, Union, Any, Tuple
from enum import Enum
import uuid
import time
from datetime import datetime, timezone

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
    vfx_complexity: str = Field(default="medium")

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
# DAY 25: THE INPUT DNA (DETERMINISTIC ACTION MAPPING)
# ==========================================================
class InputDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    action_name: str = Field(..., description="The abstract intent, e.g., 'jump', 'dash', 'interact'. NOT hardcoded logic.")
    hardware_trigger: str = Field(..., description="The physical button or axis, e.g., 'Spacebar', 'Gamepad_A', 'Mouse_Left'.")
    modifier_key: Optional[str] = Field(None, description="Optional modifier like 'Shift', 'Ctrl', or None.")
    active_context: str = Field("gameplay", description="The context where this is valid: 'gameplay', 'ui', or 'cinematic'.")

# ==========================================================
# DAY 27: THE LOCALIZATION HOLE (SEMANTIC & FLUID)
# ==========================================================
class FluidUIRules(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_word_length_tolerance: int = Field(default=20, description="Max characters before forced wrapping or scaling")
    force_text_wrap: bool = Field(default=True)
    flex_direction_fallback: str = Field(default="column", description="If row fails, stack vertically")
    scale_font_down_if_overflow: bool = Field(default=True)

class LocaleDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    target_language: str = Field(default="en", description="e.g., 'en', 'es', 'ja', 'de'")
    fluid_ui_rules: FluidUIRules = Field(default_factory=FluidUIRules)
    audio_cadence_shift: float = Field(default=0.0, description="0.0 is normal. Positive speeds up rhythm, negative slows it down.")
    text_direction: str = Field(default="ltr", description="'ltr' (Left-to-Right) or 'rtl' (Right-to-Left like Arabic)")

class SemanticToken(BaseModel):
    model_config = ConfigDict(extra="allow")
    concept_id: str = Field(..., description="e.g., 'greeting_hostile', 'combat_warn_fire'")
    intensity: float = Field(default=1.0, description="0.0 to 1.0. Modifies how strongly the concept is expressed.")
    context_vars: Dict[str, Any] = Field(default_factory=dict, description="For injecting variables like {'player_name': 'Sarah'}")

# ==========================================================
# DAY 29: THE TUTORIAL HOLE (DYNAMIC ONBOARDING)
# ==========================================================
class TutorialDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    concept_id: str = Field(..., description="Unique ID for the concept, e.g., 'dodge_mechanic'")
    trigger_condition: str = Field(..., description="The World State condition that triggers the hint, e.g., 'player_health < 30 AND enemy_distance < 5'")
    input_requirement: str = Field(..., description="The input the player must perform to succeed, e.g., 'dash_button'")
    hint_visual_type: Literal["glowing_vector", "pulsing_input_icon", "subtle_particle_trail"] = Field(..., description="The mathematical visual cue to guide the player's eye.")

class MasteryEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    concept_id: str = Field(..., description="The ID of the concept the player just mastered.")
    success_timestamp: datetime = Field(default_factory=datetime.utcnow, description="The exact time the player succeeded.")

# ==========================================================
# DAY 31: THE ACCESSIBILITY HOLE (EMPATHETIC ADAPTATION)
# ==========================================================
class AccessibilityDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    cognitive_load_level: Literal["minimal", "balanced", "supported", "max_support"] = Field(default="balanced", description="How much mental load the experience should place on the player.")
    motor_assist_mode: Literal["standard", "generous_timing", "max_assist"] = Field(default="standard", description="How generous input timing windows should be for motor comfort.")
    visual_contrast_profile: Literal["standard", "high_contrast"] = Field(default="standard", description="The visual contrast reality the UI Token Synthesizer should compile.")
    audio_cue_amplification: Literal["off", "low", "medium", "high"] = Field(default="off", description="How strongly critical audio cues should be amplified.")
    camera_comfort_mode: Literal["standard", "reduced_motion", "stable_only"] = Field(default="standard", description="How the camera should move to prevent motion sickness while preserving emotional intent.")

class AdaptationEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    trigger_type: str = Field(..., description="Why the adaptation happened.")
    adapted_system: str = Field(..., description="The system that changed.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The exact time the adaptation occurred.")

# ==========================================================
# DAY 32: THE QUEST HOLE (PROCEDURAL NARRATIVE GRAPHS)
# ==========================================================
class NarrativeNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    node_id: str = Field(..., description="Unique ID for this story node.")
    semantic_concept: str = Field(..., description="The semantic meaning of this story beat.")
    completion_condition: Dict[str, Any] = Field(default_factory=dict, description="Deterministic condition that must be satisfied to complete this node.")

class NarrativeEdge(BaseModel):
    model_config = ConfigDict(extra="allow")
    from_node: str = Field(..., description="The source node ID.")
    to_node: str = Field(..., description="The target node ID.")

class QuestDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    quest_id: str = Field(..., description="Unique ID for this quest.")
    nodes: List[NarrativeNode] = Field(default_factory=list, description="All narrative nodes inside this quest graph.")
    edges: List[NarrativeEdge] = Field(default_factory=list, description="Directed edges between nodes.")
    prerequisites: List[str] = Field(default_factory=list, description="Quest-level prerequisites.")
    state_mutations: Dict[str, Any] = Field(default_factory=dict, description="Deterministic World State mutations.")

# ==========================================================
# DAY 33: THE SOCIAL HOLE (DETERMINISTIC SOCIAL MATRICES)
# ==========================================================
class FactionDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    faction_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this faction.")
    name: str = Field(..., description="The name of the faction.")
    description: str = Field(default="", description="A short semantic description of the faction.")
    values: List[str] = Field(default_factory=list, description="What the faction believes in.")
    goals: List[str] = Field(default_factory=list, description="What the faction wants.")
    disposition_toward_player: float = Field(default=0.0, description="-1.0 means hostile, 0.0 means neutral, +1.0 means allied.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra deterministic faction memory.")

class RelationshipTensor(BaseModel):
    model_config = ConfigDict(extra="allow")
    source_id: str = Field(..., description="The entity or faction where this relationship starts.")
    target_id: str = Field(..., description="The entity or faction where this relationship points.")
    weight: float = Field(default=0.0, description="The mathematical disposition from source to target.")
    relationship_type: str = Field(default="neutral", description="Examples: alliance, rivalry, debt, trade, religious_tension.")
    confidence: float = Field(default=1.0, description="How stable or certain this relationship is.")
    notes: str = Field(default="", description="Optional semantic note for the Brain.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra deterministic relationship memory.")

class SocialRule(BaseModel):
    model_config = ConfigDict(extra="allow")
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this social rule.")
    trigger_action: str = Field(default="*", description="The SocialAction type this rule responds to.")
    source_faction_id: Optional[str] = Field(default=None, description="Optional faction this rule specifically applies to.")
    target_faction_id: Optional[str] = Field(default=None, description="Optional target faction this rule specifically applies to.")
    effect_type: str = Field(default="disposition_change", description="The type of mathematical effect.")
    magnitude_multiplier: float = Field(default=1.0, description="How strongly this rule amplifies or dampens the ripple.")
    description: str = Field(default="", description="Human-readable explanation for the Brain and Founder.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra deterministic rule memory.")

class SocialDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    factions: List[FactionDNA] = Field(default_factory=list, description="All factions inside this society.")
    relationship_tensors: List[RelationshipTensor] = Field(default_factory=list, description="Weighted relationships between factions, NPCs, and the player.")
    social_rules: List[SocialRule] = Field(default_factory=list, description="Deterministic rules that govern how actions ripple through society.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra deterministic society memory.")

class SocialAction(BaseModel):
    model_config = ConfigDict(extra="allow")
    actor_id: str = Field(..., description="The ID of the actor performing the action.")
    target_id: str = Field(..., description="The ID of the faction, NPC, or group being affected.")
    action_type: str = Field(..., description="The semantic action, e.g., help, steal, betray, donate, insult.")
    magnitude: float = Field(default=0.1, description="How strong the action is.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Extra context for the Social Engine.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The exact time the social action occurred.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra deterministic action memory.")

# ==========================================================
# DAY 34: THE LIVING WORLD TRINITY (ECOLOGY & FLOW STATE)
# PLACED HERE (ABOVE AppDNA) SO PYTHON KNOWS THEM BEFORE AppDNA USES THEM.
# ==========================================================
class PacingDirective(str, Enum):
    INCREASE_TENSION = "increase_tension"
    REDUCE_DIFFICULTY = "reduce_difficulty"
    MAINTAIN_FLOW = "maintain_flow"
    QUIET_MOMENT = "quiet_moment"

class EcologyDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    species_list: List[str] = Field(default_factory=list, description="All species or ecological actors in this biome.")
    predator_prey_links: List[Tuple[str, str]] = Field(default_factory=list, description="Predator-prey relationships. Each tuple is (predator, prey).")
    hunger_rates: Dict[str, float] = Field(default_factory=dict, description="How quickly each species experiences hunger pressure.")
    reproduction_cycles: Dict[str, int] = Field(default_factory=dict, description="How many ticks between reproduction opportunities.")
    territory_ranges: Dict[str, float] = Field(default_factory=dict, description="Territory radius or range needed by each species.")
    carrying_capacity: Dict[str, int] = Field(default_factory=dict, description="Maximum sustainable population for each species.")

class FlowDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    flow_score: float = Field(default=50.0, ge=0.0, le=100.0, description="Current flow quality from 0 to 100.")
    challenge_level: float = Field(default=0.5, ge=0.0, le=1.0, description="Current challenge pressure from 0 to 1.")
    skill_level: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated player skill from 0 to 1.")
    pacing_directive: PacingDirective = Field(default=PacingDirective.MAINTAIN_FLOW, description="The Brain's next emotional pacing command.")
    tension_curve: List[float] = Field(default_factory=list, description="Recent tension history for pacing analysis.")
    session_start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp when the current session began.")
    failure_count: int = Field(default=0, ge=0, description="Number of recent failures or deaths.")
    hesitation_ms: float = Field(default=0.0, ge=0.0, description="Average input hesitation in milliseconds.")

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

    locale: LocaleDNA = Field(default_factory=LocaleDNA)
    tutorials: List[TutorialDNA] = Field(default_factory=list)

    accessibility: AccessibilityDNA = Field(default_factory=AccessibilityDNA)
    quests: List[QuestDNA] = Field(default_factory=list)
    social: SocialDNA = Field(default_factory=SocialDNA)

    ecology: EcologyDNA = Field(default_factory=EcologyDNA)
    flow: FlowDNA = Field(default_factory=FlowDNA)

# ==========================================================
# DAY 12, 15, 16, 17, 18, 20, 21 & 22 RESTORATION
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

class NavMeshDNA(BaseModel):
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

class DeployDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    target_environment: str = Field(default="docker")
    port_mappings: dict = Field(default_factory=dict)
    env_variables: dict = Field(default_factory=dict)
    asset_cdn_url: Optional[str] = Field(default=None)

# ==========================================================
# CRITICAL ALIASES FOR BACKWARD COMPATIBILITY
# ==========================================================
GenesisRenderer = PriorityDualEngineDNA

# ==========================================================
# DAY 26: THE MODDING HOLE (SAFE INJECTION)
# ==========================================================
class ModMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)
    description: str = ""

class ModDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    mod_name: str
    author_id: str
    injected_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_tokens: List[str] = Field(default_factory=list)
    metadata: ModMetadata = Field(default_factory=ModMetadata)

# ==========================================================
# DAY 28: THE ECONOMY HOLE (MATH BALANCING)
# ==========================================================
class EconomyDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    resource_name: str = Field(..., description="Name of the resource, e.g., 'Gold', 'Wood'")
    faucet_type: Literal["active_quest", "passive_income", "loot_drop"] = Field(..., description="How the resource enters the economy (the source)")
    sink_type: Literal["vendor_purchase", "crafting_cost", "tax"] = Field(..., description="How the resource leaves the economy (the drain)")
    target_velocity: float = Field(..., description="Expected transactions per hour to keep the player engaged")
    inflation_cap: float = Field(..., description="Maximum allowed accumulation rate per hour to mathematically prevent exploits")

class EconomicEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    actor_id: str = Field(..., description="The ID of the player or entity causing the event")
    amount: float = Field(..., description="Positive for faucets (earned), negative for sinks (spent)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The exact time the event occurred")

# ==========================================================
# DAY 30: THE CHRONO DNA — DETERMINISTIC SEED CHECKPOINTING
# ==========================================================
class ChronoDNA(BaseModel):
    model_config = ConfigDict(extra="allow")
    world_seed: int = Field(..., description="The master mathematical seed that generated the entire world.")
    timestamp: float = Field(..., description="The exact moment in game-time (in seconds) when this checkpoint was created.")
    input_log_hash: str = Field(..., description="A tiny fingerprint (hash) of every abstracted player action.")
    rewind_depth: int = Field(default=0, description="How many checkpoints back from 'now' this one sits.")

class RewindIntent(BaseModel):
    model_config = ConfigDict(extra="allow")
    target_timestamp: float = Field(..., description="The exact game-time (in seconds) the player wants to rewind to.")
    reason: str = Field(default="manual", description="Why the rewind was triggered (e.g., 'manual', 'player_death').")

    # ==============================================================================
# DAY 35: INFINITE CONTENT WEAVER (PILLAR 22) - APPEND ONLY
# ==============================================================================

class TriggerSource(str, Enum):
    """Where did the spark for this moment come from?"""
    ECOLOGY = "ecology"
    SOCIAL = "social"
    NARRATIVE = "narrative"
    FLOW = "flow"
    ECONOMY = "economy"
    RANDOM = "random"

class EmotionalArc(str, Enum):
    """The shape of the player's emotion during this moment."""
    RISING = "rising"     # Tension building (chase, mystery)
    FALLING = "falling"   # Tension releasing (aftermath)
    PEAK = "peak"         # Climax (boss fight, revelation)
    VALLEY = "valley"     # Calm (rest, reflection)
    TWIST = "twist"       # Surprise (betrayal, sudden discovery)

class ContentWeaverDNA(BaseModel):
    """
    The DNA of a Moment. This is the 'Conductor's Baton'.
    It doesn't play the music; it tells the musicians (engines) when to play.
    """
    moment_id: str
    trigger_source: TriggerSource
    intensity: float = Field(ge=0.0, le=1.0) # 0.0 is whisper, 1.0 is scream
    affected_systems: List[str] # e.g., ["cinematographer", "audio", "ecology"]
    duration_ticks: int
    emotional_arc: EmotionalArc

class AAAMoment(BaseModel):
    """
    The fully orchestrated event.
    Contains specific directives for every engine involved.
    """
    moment_id: str
    timestamp: datetime
    trigger_source: str
    
    # Directives are JSON strings to keep the schema flexible for different engines
    cinematographer_directive: str 
    audio_directive: str
    ecology_directive: str
    social_directive: str
    narrative_directive: str
    economy_directive: str
    tutorial_directive: Optional[str] = None
    
    resolved: bool = False

    # ==============================================================================
# DAY 36: THE FIDELITY LADDER GROUNDWORK (PILLAR 23) - APPEND ONLY
# ==============================================================================

class ShaderProfile(str, Enum):
    TOON = "toon"
    PBR = "pbr"
    UNLIT = "unlit"
    CUSTOM = "custom"

class HardwareTier(str, Enum):
    POTATO = "potato"   # i3 laptops, strict $0 cloud
    MID = "mid"
    HIGH = "high"
    ULTRA = "ultra"
    CLOUD = "cloud"

class RenderPipeline(str, Enum):
    PRIMITIVE = "primitive"         # L0
    SDF = "sdf"                     # L1
    PROCEDURAL_MESH = "procedural_mesh" # L2
    GAUSSIAN_SPLAT = "gaussian_splat"   # L3
    ASSET_SWARM = "asset_swarm"         # L4
    AI_GENERATED = "ai_generated"       # L5

class FidelityDNA(BaseModel):
    """The DESIRED fidelity requested by the Brain."""
    model_config = ConfigDict(extra="allow")
    
    entity_id: str = Field(..., description="Unique ID of the entity requesting render.")
    fidelity_level: int = Field(..., ge=0, le=5, description="Desired visual fidelity level (0 to 5).")
    style_tags: List[str] = Field(default_factory=list, description="e.g., ['cyberpunk', 'organic', 'brutalist']")
    color_palette: Dict[str, str] = Field(default_factory=dict, description="Mapping of semantic role to hex color.")
    shader_profile: ShaderProfile = Field(default=ShaderProfile.PBR, description="Material style.")
    lod_bias: float = Field(default=0.5, ge=0.0, le=1.0, description="Level of detail bias (0.0 to 1.0).")
    hardware_tier: HardwareTier = Field(default=HardwareTier.POTATO, description="Target hardware capability.")

class FidelityRoute(BaseModel):
    """The ACTUAL fidelity resolved by the Fidelity Engine after hardware checks."""
    model_config = ConfigDict(extra="allow")
    
    entity_id: str = Field(..., description="The entity this route applies to.")
    resolved_level: int = Field(..., ge=0, le=5, description="The ACTUAL level the engine will render.")
    render_pipeline: RenderPipeline = Field(..., description="The exact rendering pipeline to use.")
    fallback_level: int = Field(..., ge=0, le=5, description="The level we fell back to if requested level was too high.")
    estimated_load_ms: float = Field(default=0.0, description="Estimated time to render/compile this level in ms.")