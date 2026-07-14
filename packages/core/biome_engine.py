import random
from typing import List, Dict, Any

class BiomeEngine:
    def __init__(self, seed: int):
        """Initialize the engine with a deterministic math seed."""
        self.seed = seed

    def _smoothstep(self, t: float) -> float:
        """A math trick to turn jagged random static into smooth, rolling curves."""
        return t * t * (3.0 - 2.0 * t)

    def generate_map(self, width: int, height: int, scale: float, seed_offset: int = 0) -> List[List[float]]:
        """
        Generates a 2D grid of Perlin-like noise values (0.0 to 1.0).
        """
        random.seed(self.seed + seed_offset)
        base_grid = [[random.random() for _ in range(width + 2)] for _ in range(height + 2)]
        
        noise_grid = []
        for y in range(height):
            row = []
            for x in range(width):
                x_frac = (x / scale)
                y_frac = (y / scale)
                x0 = int(x_frac)
                x1 = x0 + 1
                y0 = int(y_frac)
                y1 = y0 + 1
                
                sx = self._smoothstep(x_frac - x0)
                sy = self._smoothstep(y_frac - y0)
                
                n0 = base_grid[y0][x0] * (1 - sx) + base_grid[y0][x1] * sx
                n1 = base_grid[y1][x0] * (1 - sx) + base_grid[y1][x1] * sx
                
                final_value = n0 * (1 - sy) + n1 * sy
                row.append(final_value)
            noise_grid.append(row)
            
        return noise_grid

    def get_biome_maps(self, width: int = 50, height: int = 50, scale: float = 10.0) -> dict:
        """Generates both the heightmap and moisture map for a biome."""
        heightmap = self.generate_map(width, height, scale, seed_offset=0)
        moisture_map = self.generate_map(width, height, scale, seed_offset=9999) 
        return {
            "elevation": heightmap,
            "moisture": moisture_map
        }

    def calculate_scatter_coordinates(self, biome_dna: Any, width: int = 50, height: int = 50, unit_size: float = 2.0) -> List[Dict[str, Any]]:
        """
        Reads the biome DNA and noise maps to output precise X, Y, Z coordinates for assets.
        """
        # 1. Generate the math maps
        maps = self.get_biome_maps(width, height)
        elevation_map = maps["elevation"]
        moisture_map = maps["moisture"]
        
        spawn_list = []
        
        # We use a specific seed offset for the scatter dice-roll to keep it deterministic
        random.seed(self.seed + 4242) 
        
        # 2. Iterate through every rule defined in the Biome DNA
        for rule in biome_dna.scatter_rules:
            # 3. Iterate through every grid point (X and Z in 3D space)
            for z_idx in range(height):
                for x_idx in range(width):
                    # Get the environmental value (Using Moisture for this logic)
                    moisture_val = moisture_map[z_idx][x_idx]
                    
                    # Check if this spot meets the rule's threshold
                    if moisture_val >= rule.noise_threshold:
                        # 4. Density Roll: Should we actually spawn something here?
                        # We combine the global biome density with the specific rule's density
                        spawn_chance = biome_dna.scatter_density * rule.density_multiplier
                        
                        # Clamp to 1.0 (100% chance) just in case
                        spawn_chance = min(1.0, spawn_chance)
                        
                        if random.random() < spawn_chance:
                            # 5. Calculate final World Coordinates
                            # X and Z are grid positions * unit_size (spacing)
                            world_x = x_idx * unit_size
                            world_z = z_idx * unit_size
                            
                            # Y is the elevation map value * a height multiplier (e.g., 10 units high max)
                            world_y = elevation_map[z_idx][x_idx] * 10.0 
                            
                            spawn_list.append({
                                "asset_type": rule.asset_type,
                                "x": round(world_x, 2),
                                "y": round(world_y, 2),
                                "z": round(world_z, 2)
                            })
                            
        return spawn_list