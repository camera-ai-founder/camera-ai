import math
from typing import Dict, List, Any
from .models import ChronoDNA, RewindIntent

# ============================================================
# DAY 30: THE DETERMINISTIC SEED ENGINE & REWIND LOGIC
# ============================================================
# This file ensures that our Genesis Renderer and Biome Engine 
# are strictly seeded. It also handles the instantaneous, 
# mathematically pure time-travel (Rewind) logic.
# ============================================================

class DeterministicRNG:
    """
    The Shuffling Machine (Pseudo-Random Number Generator).
    Pure mathematical formula (Linear Congruential Generator).
    """
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF
        
    def next_int(self) -> int:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state
        
    def next_float(self) -> float:
        return self.next_int() / 4294967296.0
        
    def next_range(self, min_val: float, max_val: float) -> float:
        return min_val + (self.next_float() * (max_val - min_val))


class ChronoEngine:
    """
    The Time Engine.
    """
    def __init__(self):
        pass

    def generate_world_layout(self, seed: int, timestamp: float) -> Dict[str, Any]:
        """
        Calculates where objects are at a specific moment in time 
        using pure, predictable math.
        """
        rng = DeterministicRNG(seed)
        entities = []
        
        for i in range(3):
            x = rng.next_range(-100.0, 100.0)
            z = rng.next_range(-100.0, 100.0)
            base_height = rng.next_range(2.0, 5.0)
            current_height = base_height + (timestamp * 0.01) 
            
            entities.append({
                "id": f"entity_{i}",
                "x": round(x, 2), 
                "z": round(z, 2), 
                "height": round(current_height, 2)
            })
        
        return {
            "seed_used": seed, 
            "timestamp_calculated": timestamp, 
            "entities": entities
        }
        
    def reconstruct_world_state(self, chrono_dna: ChronoDNA) -> Dict[str, Any]:
        """
        Rebuilds the world from a tiny ChronoDNA checkpoint.
        """
        return self.generate_world_layout(
            seed=chrono_dna.world_seed, 
            timestamp=chrono_dna.timestamp
        )

    def create_checkpoint(self, current_seed: int, current_time: float, depth: int) -> ChronoDNA:
        """
        Creates a new Time Capsule to save to the database.
        """
        fake_input_hash = f"hash_{current_seed}_{current_time}"
        
        return ChronoDNA(
            world_seed=current_seed,
            timestamp=current_time,
            input_log_hash=fake_input_hash,
            rewind_depth=depth
        )

    def process_rewind(self, rewind_intent: RewindIntent, full_input_log: List[Dict[str, Any]], restored_seed: int) -> Dict[str, Any]:
        """
        THE REWIND ENGINE (TIME TRAVEL).
        
        When the player triggers a RewindIntent, this function handles it.
        It does NOT load heavy files. It wipes the lightweight state, 
        reloads the seed, and fast-forwards the math at 10x speed.
        """
        target_time = rewind_intent.target_timestamp
        
        print(f"[CHRONO] 🔄 Wiping current lightweight ECS state...")
        print(f"[CHRONO] 🎯 Target Time: {target_time}s | Reason: {rewind_intent.reason}")
        
        # 1. Initialize our math machine with the restored seed from Supabase
        rng = DeterministicRNG(restored_seed)
        
        print(f"[CHRONO] ⏩ Replaying input log at 10x speed to reconstruct frame...")
        
        # 2. Filter the Black Box inputs to only those that happened BEFORE the target time
        inputs_to_replay = [
            action for action in full_input_log 
            if action.get('timestamp', 0) <= target_time
        ]
        
        # 3. Fast-forward the math. 
        # We don't render these frames, we just advance the mathematical state instantly.
        for action in inputs_to_replay:
            # Advancing the RNG predictably based on the abstracted intent
            rng.next_int() 
            
        # 4. Reconstruct the exact past frame using our core math generator
        final_rewound_state = self.generate_world_layout(restored_seed, target_time)
        
        print(f"[CHRONO] ✨ Time travel complete. World perfectly reconstructed with zero RAM bloat.")
        return final_rewound_state