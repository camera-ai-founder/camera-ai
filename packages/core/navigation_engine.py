import math
import heapq
from typing import List, Dict, Tuple
from packages.core.models import NavMeshDNA

# We define our world limits here as a constant. 
# (-50, -50) is the bottom-left corner, (50, 50) is the top-right corner of our map.
WORLD_BOUNDS = (-50.0, -50.0, 50.0, 50.0)

class Voxelizer:
    """
    Converts our Biome/Scatter math into a deterministic, lightweight 2D grid.
    True = Walkable (grass/road)
    False = Blocked (Genesis building/obstacle)
    """
    
    def __init__(self, nav_dna: NavMeshDNA):
        self.dna = nav_dna
        self.min_x, self.min_z, self.max_x, self.max_z = WORLD_BOUNDS
        self.resolution = self.dna.grid_resolution
        
        # Calculate grid dimensions based on our world size and resolution
        self.grid_width = int((self.max_x - self.min_x) / self.resolution)
        self.grid_height = int((self.max_z - self.min_z) / self.resolution)

    def generate_grid(self, placed_assets: List[Dict]) -> List[List[bool]]:
        """
        Creates the 2D boolean grid.
        :param placed_assets: List of dictionaries from our Scatter Engine, 
                              e.g., [{'x': 10.5, 'z': -5.2, 'radius': 2.0}, ...]
        """
        # Initialize grid with True (assume everything is walkable by default)
        grid = [[True for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Block out cells where Genesis assets (buildings, trees) are placed
        for asset in placed_assets:
            ax = asset.get('x', 0.0)
            az = asset.get('z', 0.0)
            radius = asset.get('radius', 1.0) # The footprint of the building
            
            # Convert world coordinates to grid indices
            # We add a small buffer to the radius to ensure entities don't clip into walls
            safe_radius = radius + self.resolution 
            
            # Determine the bounding box in grid indices
            start_col = int((ax - safe_radius - self.min_x) / self.resolution)
            end_col = int((ax + safe_radius - self.min_x) / self.resolution)
            start_row = int((az - safe_radius - self.min_z) / self.resolution)
            end_row = int((az + safe_radius - self.min_z) / self.resolution)
            
            # Mark cells as False (blocked)
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    # Boundary checks to prevent index out of bounds errors
                    if 0 <= r < self.grid_height and 0 <= c < self.grid_width:
                        grid[r][c] = False
                        
        return grid

    def world_to_grid(self, x: float, z: float) -> Tuple[int, int]:
        """Converts a 3D world coordinate to a 2D grid index."""
        col = int((x - self.min_x) / self.resolution)
        row = int((z - self.min_z) / self.resolution)
        
        # Clamp to grid boundaries to prevent crashes if an entity wanders off the map
        col = max(0, min(col, self.grid_width - 1))
        row = max(0, min(row, self.grid_height - 1))
        return row, col

    def grid_to_world(self, row: int, col: int) -> Tuple[float, float]:
        """Converts a 2D grid index back to a 3D world coordinate (center of the cell)."""
        x = (col * self.resolution) + self.min_x + (self.resolution / 2)
        z = (row * self.resolution) + self.min_z + (self.resolution / 2)
        return x, z


class AStarPathfinder:
    """
    Pure-math A* (A-Star) algorithm.
    It reads the 2D boolean grid and calculates the shortest walkable path.
    """
    def __init__(self, grid: List[List[bool]], voxelizer: Voxelizer):
        self.grid = grid
        self.voxelizer = voxelizer
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance: simple math to guess how far we are from the goal."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Look at the 4 adjacent squares (Up, Down, Left, Right)."""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        neighbors = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.rows and 0 <= c < self.cols:
                if self.grid[r][c]: # Only walkable cells (True)
                    neighbors.append((r, c))
        return neighbors

    def find_path(self, start_world: Tuple[float, float], target_world: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Calculates the path from start to target.
        Returns a list of (x, z) world coordinates.
        """
        # Convert world coords to grid coords
        start_grid = self.voxelizer.world_to_grid(start_world[0], start_world[1])
        target_grid = self.voxelizer.world_to_grid(target_world[0], target_world[1])

        # Priority queue for A* (stores: priority, counter, grid_node)
        open_set = []
        heapq.heappush(open_set, (0, 0, start_grid))
        counter = 1 # Tie-breaker for heapq

        came_from = {}
        
        # Cost to reach each node
        g_score = {start_grid: 0}
        # Estimated total cost
        f_score = {start_grid: self._heuristic(start_grid, target_grid)}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            # If we reached the target, reconstruct the path!
            if current == target_grid:
                path_grid = []
                while current in came_from:
                    path_grid.append(current)
                    current = came_from[current]
                path_grid.append(start_grid)
                path_grid.reverse()

                # Convert grid path back to world coordinates
                path_world = [self.voxelizer.grid_to_world(r, c) for r, c in path_grid]
                return path_world

            for neighbor in self._get_neighbors(current[0], current[1]):
                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, target_grid)
                    
                    # Push to priority queue
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                    counter += 1

        # If we exhaust the queue and never hit the target, return empty list (no path)
        return []