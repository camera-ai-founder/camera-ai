import math
from .models import ImpactVector, JuiceProfile

def calculate_impact_vector(force: float, angle_x: float = 45.0, angle_y: float = 45.0) -> ImpactVector:
    """
    Calculates the initial push (velocity) using basic trigonometry.
    No heavy physics engine required!
    """
    # Convert angles from degrees to radians for math functions
    rad_x = math.radians(angle_x)
    rad_y = math.radians(angle_y)

    # Simple math to split the force into X, Y, and Z directions
    vx = force * math.cos(rad_x) * math.sin(rad_y)
    vy = force * math.sin(rad_x) # Upward push (Y-axis)
    vz = force * math.cos(rad_x) * math.cos(rad_y)

    return ImpactVector(
        velocity_x=vx,
        velocity_y=vy,
        velocity_z=vz,
        force=force
    )

def update_trajectory(vector: ImpactVector, juice: JuiceProfile, gravity: float = -9.8, time_step: float = 0.1) -> ImpactVector:
    """
    Updates the object's position frame-by-frame.
    Applies gravity and slows it down based on the JuiceProfile's decay.
    """
    # Apply gravity to the Y (up/down) velocity
    new_vy = vector.velocity_y + (gravity * time_step)

    # Apply the ragdoll decay (air resistance/friction) to X and Z so it eventually stops
    decay = 1.0 - (juice.ragdoll_decay * time_step)

    return ImpactVector(
        velocity_x=vector.velocity_x * decay,
        velocity_y=new_vy,
        velocity_z=vector.velocity_z * decay,
        force=vector.force
    )