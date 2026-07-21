# packages/core/ecology_engine.py

from typing import Dict, List, Tuple
from pydantic import BaseModel, Field

# We import the DNA schemas we built in Step 1 (Day 34) and Day 16
from .models import EcologyDNA, BiomeDNA


class EcologyEvent(BaseModel):
    """
    A record of a major ecological shift.
    The Brain will read these events to narrate the world.
    """
    event_type: str = Field(..., description="e.g., 'extinction', 'overpopulation', 'starvation'")
    species: str = Field(..., description="The species affected.")
    message: str = Field(..., description="Human-readable summary for the narrative engine.")


class CascadeEvent(BaseModel):
    """
    A domino-effect event triggered by an extinction or depletion.
    """
    event_type: str = Field(..., description="e.g., 'prey_boom', 'predator_starvation', 'biome_collapse'")
    target_species: str = Field(..., description="The species or environment affected.")
    mathematical_effect: dict = Field(default_factory=dict, description="The exact math the engine applies next.")
    message: str = Field(..., description="Human-readable summary for the narrative engine.")


def simulate_tick(
    current_populations: Dict[str, int], 
    dna: EcologyDNA
) -> Tuple[Dict[str, int], List[EcologyEvent]]:
    """
    Simulates one tick of the ecosystem using simplified Lotka-Volterra equations.
    """
    dt = 0.1 
    
    PREDATION_RATE = 0.001
    CONVERSION_RATE = 0.5
    
    new_populations = current_populations.copy()
    deltas: Dict[str, float] = {species: 0.0 for species in current_populations.keys()}
    
    # 1. Calculate growth for all species based on reproduction and hunger
    for species in current_populations.keys():
        pop = current_populations.get(species, 0)
        if pop <= 0:
            continue
            
        repro_cycle = dna.reproduction_cycles.get(species, 10)
        birth_rate = 1.0 / max(1, repro_cycle)
        hunger_rate = dna.hunger_rates.get(species, 0.1) * 0.05 
        death_rate = hunger_rate 
        
        deltas[species] += (birth_rate * pop - death_rate * pop) * dt

    # 2. Calculate predator-prey interactions
    for predator, prey in dna.predator_prey_links:
        pred_pop = current_populations.get(predator, 0)
        prey_pop = current_populations.get(prey, 0)
        
        if pred_pop <= 0 or prey_pop <= 0:
            continue
            
        prey_loss = PREDATION_RATE * prey_pop * pred_pop
        pred_gain = CONVERSION_RATE * PREDATION_RATE * prey_pop * pred_pop
        
        deltas[prey] -= prey_loss * dt
        deltas[predator] += pred_gain * dt

    # 3. Apply deltas, clamp to carrying capacity, and check for extinctions
    events: List[EcologyEvent] = []
    
    for species, delta in deltas.items():
        old_pop = current_populations.get(species, 0)
        raw_new_pop = old_pop + delta
        capacity = dna.carrying_capacity.get(species, 10000)
        clamped_new_pop = max(0, min(capacity, int(raw_new_pop)))
        
        new_populations[species] = clamped_new_pop
        
        if old_pop > 0 and clamped_new_pop == 0:
            events.append(EcologyEvent(
                event_type="extinction",
                species=species,
                message=f"The {species} population has collapsed to zero and gone extinct."
            ))
        elif clamped_new_pop >= capacity and old_pop < capacity:
            events.append(EcologyEvent(
                event_type="carrying_capacity_reached",
                species=species,
                message=f"The {species} population has reached the absolute limit the land can support."
            ))

    return new_populations, events


def resolve_cascade(
    current_populations: Dict[str, int],
    dna: EcologyDNA,
    current_biome: BiomeDNA
) -> Tuple[Dict[str, int], BiomeDNA, List[CascadeEvent]]:
    """
    Resolves the domino effects (trophic cascades) when a species goes extinct
    or a base resource is severely depleted.
    """
    events: List[CascadeEvent] = []
    new_pops = current_populations.copy()
    
    # Clone the biome DNA so we don't mutate the original object directly
    # (Pydantic V2 safe cloning)
    new_biome = current_biome.model_copy(deep=True)

    # 1. Predator goes extinct -> Prey population growth doubles (Prey Boom)
    for predator, prey in dna.predator_prey_links:
        if current_populations.get(predator, 0) == 0 and current_populations.get(prey, 0) > 0:
            events.append(CascadeEvent(
                event_type="prey_boom",
                target_species=prey,
                mathematical_effect={"growth_multiplier": 2.0, "duration_ticks": 10},
                message=f"With {predator} extinct, the {prey} population faces no predation pressure and will grow twice as fast."
            ))

    # 2. Prey goes extinct -> Predator Starvation (30% drop per tick)
    for predator, prey in dna.predator_prey_links:
        if current_populations.get(prey, 0) == 0 and current_populations.get(predator, 0) > 0:
            pred_pop = new_pops[predator]
            starved_pop = int(pred_pop * 0.7) # 30% drop
            new_pops[predator] = starved_pop
            
            events.append(CascadeEvent(
                event_type="predator_starvation",
                target_species=predator,
                mathematical_effect={"population_drop_percent": 30},
                message=f"Without {prey} to hunt, the {predator} are starving. Their population dropped by 30%."
            ))

    # 3. Vegetation drops below 20% -> Biome Collapse
    # We assume "vegetation" is the base prey in the ecosystem.
    veg_pop = current_populations.get("vegetation", 0)
    veg_capacity = dna.carrying_capacity.get("vegetation", 100)
    
    if veg_capacity > 0 and veg_pop < (0.20 * veg_capacity):
        # Mutate the Day 16 BiomeDNA to reflect a barren state
        new_biome.scatter_density = 0.0
        new_biome.moisture_level = 0.1
        if "Barren" not in new_biome.name:
            new_biome.name = f"{current_biome.name} (Barren)"
            
        events.append(CascadeEvent(
            event_type="biome_collapse",
            target_species="vegetation",
            mathematical_effect={"new_biome_state": "barren", "scatter_density": 0.0},
            message="Vegetation has dropped below 20% of carrying capacity. The biome is collapsing into a barren wasteland."
        ))

    return new_pops, new_biome, events