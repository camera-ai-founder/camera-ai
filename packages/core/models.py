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