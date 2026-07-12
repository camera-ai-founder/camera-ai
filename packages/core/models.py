from pydantic import BaseModel, Field
from typing import Dict, Any, List

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