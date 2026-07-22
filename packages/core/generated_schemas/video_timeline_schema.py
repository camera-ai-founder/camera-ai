from pydantic import BaseModel
from typing import List, Dict, Any

class VideoTimelineDNA(BaseModel):
    clips: List[str] = []
    transitions: List[str] = []
    duration: float = 0.0
    transition_duration: float = 0.0