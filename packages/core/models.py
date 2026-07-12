from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

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