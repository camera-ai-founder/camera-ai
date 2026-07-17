from typing import List, Dict, Optional
from .models import InputDNA 

class DeterministicInputEngine:
    """
    The Universal Translator & Traffic Cop for our game inputs.
    It reads the InputDNA, builds a map, and routes hardware to actions 
    based on the current Context (gameplay, ui, or cinematic).
    """
    
    def __init__(self):
        self.input_map: Dict[str, str] = {}
        # We start in gameplay mode by default
        self.current_context: str = "gameplay" 

    def build_map_from_dna(self, input_dna_list: List[InputDNA]):
        """
        Step A: Read the DNA and build our fast lookup list.
        """
        self.input_map = {} 
        
        for dna in input_dna_list:
            # Create a unique key: e.g., "Spacebar_gameplay" or "Spacebar_cinematic"
            unique_key = f"{dna.hardware_trigger}_{dna.active_context}"
            self.input_map[unique_key] = dna.action_name

    def set_context(self, new_context: str):
        """
        Step B: The Traffic Cop switches modes.
        When the camera enters a cutscene (from Day 15 Camera DNA), 
        the game calls this to switch to "cinematic" mode.
        """
        self.current_context = new_context

    def get_action(self, hardware_pressed: str) -> Optional[str]:
        """
        Step C: The game just asks 'What does Spacebar do right now?'
        The engine automatically uses the active context to find the perfect action.
        """
        # We use the current context to find the exact right key
        unique_key = f"{hardware_pressed}_{self.current_context}"
        return self.input_map.get(unique_key)
    
    def get_full_map(self) -> Dict[str, str]:
        """
        Step D: The backend calls this to send the entire map to the browser frontend.
        This is how the JavaScript file gets its rules without hardcoding anything.
        """
        return self.input_map.copy()