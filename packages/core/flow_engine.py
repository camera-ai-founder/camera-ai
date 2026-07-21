# packages/core/flow_engine.py

from .models import FlowDNA, PacingDirective

def calculate_flow_score(
    failure_count: int,
    hesitation_ms: float,
    session_minutes: int,
    recent_success_rate: float,
    current_challenge: float
) -> FlowDNA:
    """
    Calculates the player's psychological flow state using the 
    Csikszentmihalyi model (Skill vs. Challenge balance).
    
    Args:
        failure_count: How many times the player has failed recently.
        hesitation_ms: Average delay in their inputs (indicates confusion or fatigue).
        session_minutes: How long they have been playing continuously.
        recent_success_rate: The player's current Skill Level (0.0 to 1.0).
        current_challenge: The current difficulty of the game (0.0 to 1.0).
        
    Returns:
        A fully populated FlowDNA object with the calculated PacingDirective.
    """
    
    # 1. Establish Skill and Challenge Levels (Clamped between 0.0 and 1.0)
    skill_level = max(0.0, min(1.0, recent_success_rate))
    challenge_level = max(0.0, min(1.0, current_challenge))

    # 2. Calculate the Flow Score (0 to 100)
    # The closer skill and challenge are to each other, the higher the score.
    # If they are exactly equal, abs() is 0, and flow_score is a perfect 100.
    flow_score = 100.0 - (abs(skill_level - challenge_level) * 100.0)
    
    # Safety clamp to ensure it never drops below 0 or above 100
    flow_score = max(0.0, min(100.0, flow_score))

    # 3. Determine the Pacing Directive
    # We default to MAINTAIN_FLOW, then apply the Founder's specific logic rules.
    pacing_directive = PacingDirective.MAINTAIN_FLOW

    # Rule A: The Burnout Override
    # If the player has been playing a long time and is struggling, give them peace.
    if session_minutes > 45 and flow_score < 40:
        pacing_directive = PacingDirective.QUIET_MOMENT
        
    # Rule B: The Tension Trigger
    # If the gap between skill and challenge is massive (flow < 30), spike the drama.
    elif flow_score < 30:
        pacing_directive = PacingDirective.INCREASE_TENSION
        
    # Rule C: The Relief Trigger
    # If they are in perfect flow (flow > 80), gently reduce difficulty to let them enjoy it.
    elif flow_score > 80:
        pacing_directive = PacingDirective.REDUCE_DIFFICULTY

    # 4. Construct and return the deterministic FlowDNA object
    # We omit session_start_time so Pydantic uses the safe default factory (current time).
    flow_dna = FlowDNA(
        flow_score=flow_score,
        challenge_level=challenge_level,
        skill_level=skill_level,
        pacing_directive=pacing_directive,
        failure_count=failure_count,
        hesitation_ms=hesitation_ms
    )

    return flow_dna