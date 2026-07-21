# ==============================================================================
# DAY 35: INFINITE CONTENT WEAVER (PILLAR 22) - THE CONDUCTOR
# This file orchestrates the AAA Moments. It reads state, writes DNA.
# ==============================================================================

import uuid
import random
import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Import our Schemas and Enums
from packages.core.models import (
    ContentWeaverDNA, 
    AAAMoment,
    TriggerSource, 
    EmotionalArc, 
    FlowDNA, 
    PacingDirective
)

class ContentWeaver:
    """
    The Conductor. It does not play the music (execute logic).
    It reads the mood of the world and writes the sheet music (Directives).
    """
    
    def generate_moment(
        self,
        flow_state: FlowDNA,
        ecology_state: Dict[str, Any],
        social_state: Dict[str, Any],
        narrative_state: Dict[str, Any],
        economy_state: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> ContentWeaverDNA:
        """
        Reads the Flow State's pacing directive and generates the DNA for the next AAA Moment.
        """
        pacing = flow_state.pacing_directive
        
        # Defaults
        trigger = TriggerSource.RANDOM
        intensity = 0.5
        arc = EmotionalArc.PEAK
        
        # WORKING MATH: The Logic of the Conductor
        if pacing == PacingDirective.INCREASE_TENSION:
            trigger = random.choice([TriggerSource.ECOLOGY, TriggerSource.SOCIAL, TriggerSource.NARRATIVE])
            intensity = 0.8
            arc = EmotionalArc.RISING
            
        elif pacing == PacingDirective.REDUCE_DIFFICULTY:
            trigger = random.choice([TriggerSource.ECOLOGY, TriggerSource.SOCIAL]) 
            intensity = 0.3
            arc = EmotionalArc.VALLEY
            
        elif pacing == PacingDirective.MAINTAIN_FLOW:
            trigger = random.choice([TriggerSource.ECOLOGY, TriggerSource.NARRATIVE, TriggerSource.ECONOMY])
            intensity = 0.5
            arc = EmotionalArc.PEAK
            
        elif pacing == PacingDirective.QUIET_MOMENT:
            trigger = random.choice([TriggerSource.ECOLOGY, TriggerSource.SOCIAL])
            intensity = 0.1
            arc = EmotionalArc.VALLEY

        # Who needs to wake up?
        affected_systems = ["cinematographer", "audio"]
        if trigger == TriggerSource.ECOLOGY: affected_systems.append("ecology")
        elif trigger == TriggerSource.SOCIAL: affected_systems.append("social")
        elif trigger == TriggerSource.NARRATIVE: affected_systems.append("narrative")
        elif trigger == TriggerSource.ECONOMY: affected_systems.append("economy")
        elif trigger == TriggerSource.FLOW: affected_systems.append("tutorial")

        return ContentWeaverDNA(
            moment_id=str(uuid.uuid4()),
            trigger_source=trigger,
            intensity=intensity,
            affected_systems=affected_systems,
            duration_ticks=300, 
            emotional_arc=arc
        )

    def orchestrate_moment(self, dna: ContentWeaverDNA, flow_state: FlowDNA) -> AAAMoment:
        """
        Translates the DNA into actionable JSON directives for every affected engine.
        """
        # 1. Camera
        if dna.intensity >= 0.7: cam_action = {"action": "shaky_cam_chase", "fov": 85}
        elif dna.intensity <= 0.3: cam_action = {"action": "static_wide_calm", "fov": 60}
        else: cam_action = {"action": "slow_zoom_dramatic", "fov": 70}
            
        # 2. Audio
        if dna.intensity >= 0.7: audio_profile = {"track": "percussion_building", "vol": 0.9}
        elif dna.intensity <= 0.3: audio_profile = {"track": "ambient_soft", "vol": 0.4}
        else: audio_profile = {"track": "tension_drone_high", "vol": 0.7}

        # 3. Ecology
        eco_event = None
        if dna.trigger_source == TriggerSource.ECOLOGY:
            eco_event = {"event": "wolf_pack_appears", "count": 3}
        elif dna.trigger_source == TriggerSource.SOCIAL and dna.intensity < 0.5:
            eco_event = {"event": "birds_scatter", "count": 15}
            
        # 4. Social
        soc_event = None
        if dna.trigger_source == TriggerSource.SOCIAL:
            if dna.intensity >= 0.7: soc_event = {"event": "faction_betrayal", "severity": 0.8}
            else: soc_event = {"event": "alliance_offered", "trust_bonus": 10}
                
        # 5. Narrative
        nar_event = None
        if dna.trigger_source == TriggerSource.NARRATIVE:
            nar_event = {"event": "quest_node_unlock", "node_id": "chapter_2"}
        elif dna.trigger_source == TriggerSource.RANDOM:
            nar_event = {"event": "mystery_clue_found", "item": "diary_page"}

        # 6. Economy
        eco_sys_event = None
        if dna.intensity >= 0.8: eco_sys_event = {"event": "loot_drop_high", "mult": 2.5}
        elif dna.intensity <= 0.3: eco_sys_event = {"event": "vendor_discount", "percent": 20}

        # 7. Tutorial (Empathy)
        tut_event = None
        if flow_state.flow_score < 30.0:
            tut_event = {"event": "hint_projected", "concept": "dodge"}

        # 8. Final Package
        return AAAMoment(
            moment_id=dna.moment_id,
            timestamp=datetime.now(timezone.utc),
            trigger_source=dna.trigger_source.value,
            cinematographer_directive=json.dumps(cam_action),
            audio_directive=json.dumps(audio_profile),
            ecology_directive=json.dumps(eco_event) if eco_event else "{}",
            social_directive=json.dumps(soc_event) if soc_event else "{}",
            narrative_directive=json.dumps(nar_event) if nar_event else "{}",
            economy_directive=json.dumps(eco_sys_event) if eco_sys_event else "{}",
            tutorial_directive=json.dumps(tut_event) if tut_event else None,
            resolved=False
        )

    def build_tension_curve(self, moments: List[AAAMoment]) -> Dict[str, Any]:
        """
        Calculates the dramatic arc using a sine wave + noise function.
        Enforces pacing rules to prevent fatigue or boredom.
        """
        curve = []
        base_intensity = 0.5
        amplitude = 0.3
        frequency = 0.5
        phase = 0.0
        
        # 1. Calculate raw curve based on history using Working Math
        for t in range(len(moments)):
            noise = random.uniform(-0.1, 0.1)
            # tension(t) = base + amp * sin(freq * t + phase) + noise
            t_val = base_intensity + amplitude * math.sin(frequency * t + phase) + noise
            t_val = max(0.0, min(1.0, t_val)) # Clamp between 0 and 1
            curve.append(round(t_val, 3))
            
        # 2. Analyze recent history to enforce the dramatic rhythm
        # We look at the last 5 moments in the curve
        recent_curve = curve[-5:] if len(curve) >= 5 else curve
        
        # "Rising" means high tension (> 0.6), "Valley" means low tension (< 0.4)
        rising_count = sum(1 for val in recent_curve if val > 0.6)
        valley_count = sum(1 for val in recent_curve if val < 0.4)
        
        forced_next_arc = None
        if rising_count >= 5:
            forced_next_arc = "valley" # Force quiet moment to prevent fatigue
        elif valley_count >= 3:
            forced_next_arc = "rising" # Force tension event to prevent boredom
            
        return {
            "tension_curve": curve,
            "forced_next_arc": forced_next_arc
        }