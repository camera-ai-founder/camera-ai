# ==========================================
# DAY 39: INFINITE SCALE ENGINE (PILLAR 26)
# SHARD CALCULATOR, WORKER COORDINATOR, DELTA SYNC & SCALE MONITOR
# ==========================================

import math
from typing import List, Dict, Any, Tuple
from packages.core.models import (
    ShardConfig, WorkerType, HardwareTier, ShardStatus,
    StateDelta, ChangedNode, ScaleEvent, ScaleEventType
)

def calculate_shards(total_entities: int, hardware_tier: HardwareTier) -> List[ShardConfig]:
    """
    Divides the world into optimal shards based on the hardware budget.
    This is pure, deterministic math. No AI hallucinations.
    """
    
    # 1. Determine shard configuration based on Hardware Tier
    if hardware_tier == HardwareTier.POTATO:
        shard_count = 1
        worker_type = WorkerType.MAIN_THREAD
    elif hardware_tier == HardwareTier.MID:
        shard_count = 2
        worker_type = WorkerType.WEB_WORKER
    elif hardware_tier == HardwareTier.HIGH:
        shard_count = 4
        worker_type = WorkerType.WEB_WORKER
    elif hardware_tier == HardwareTier.ULTRA:
        shard_count = 8
        worker_type = WorkerType.WEB_WORKER
    elif hardware_tier == HardwareTier.CLOUD:
        # Cloud scales infinitely. 50,000 entities per shard.
        shard_count = math.ceil(total_entities / 50000) if total_entities > 0 else 1
        worker_type = WorkerType.EDGE_FUNCTION
    else:
        # Fallback to potato to protect the i3 laptop
        shard_count = 1
        worker_type = WorkerType.MAIN_THREAD

    # 2. Initialize the empty shards
    shards = []
    for i in range(shard_count):
        shards.append(ShardConfig(
            shard_id=i,
            entity_ids=[],
            worker_id=f"{worker_type.value}_{i}",
            status=ShardStatus.ACTIVE,
            entity_count=0
        ))
        
    # 3. Distribute entities round-robin across shards
    for e in range(total_entities):
        target_shard_index = e % shard_count
        # Generate a deterministic entity ID
        entity_id = f"entity_{e}"
        shards[target_shard_index].entity_ids.append(entity_id)
        shards[target_shard_index].entity_count += 1

    return shards


def assign_workers(shards: List[ShardConfig], sync_rate_ms: int = 100) -> Dict[str, Any]:
    """
    Generates the WorkerAssignment JSON.
    The frontend (game_engine.js) reads this JSON to spawn workers.
    We do NOT modify game_engine.js.
    """
    assignment = {
        "worker_type": "",
        "assignments": []
    }

    if not shards:
        return assignment

    # Infer worker type from the first shard's worker_id
    sample_worker_id = shards[0].worker_id
    
    if "main_thread" in sample_worker_id:
        assignment["worker_type"] = WorkerType.MAIN_THREAD.value
        assignment["assignments"].append({
            "action": "run_main_thread",
            "shards": [{"shard_id": s.shard_id, "entity_ids": s.entity_ids} for s in shards]
        })
        
    elif "web_worker" in sample_worker_id:
        assignment["worker_type"] = WorkerType.WEB_WORKER.value
        for s in shards:
            assignment["assignments"].append({
                "worker_id": s.worker_id,
                "message": {
                    "action": "init_shard",
                    "shard_id": s.shard_id,
                    "entity_ids": s.entity_ids,
                    "sync_rate_ms": sync_rate_ms
                }
            })
            
    elif "edge_function" in sample_worker_id:
        assignment["worker_type"] = WorkerType.EDGE_FUNCTION.value
        for s in shards:
            assignment["assignments"].append({
                "worker_id": s.worker_id,
                "http_payload": {
                    "endpoint": "/functions/v1/process-shard",
                    "method": "POST",
                    "body": {
                        "action": "init_shard",
                        "shard_id": s.shard_id,
                        "entity_ids": s.entity_ids,
                        "sync_rate_ms": sync_rate_ms
                    }
                }
            })
    else:
        assignment["worker_type"] = WorkerType.CLOUD_INSTANCE.value

    return assignment


def sync_shards(shard_a: ShardConfig, shard_b: ShardConfig, interacting_entity_a: str, interacting_entity_b: str, interaction_type: str = "collision") -> List[StateDelta]:
    """
    Calculates the Delta between two shards when entities interact across boundaries.
    Uses the Day 21 Netcode Engine pattern without modifying netcode_engine.py.
    """
    # 1. Verify entities actually belong to the shards we are syncing
    if interacting_entity_a not in shard_a.entity_ids or interacting_entity_b not in shard_b.entity_ids:
        return []

    # 2. Generate a deterministic StateDelta
    # This represents the "cross-border" event (e.g., a bullet from Shard A hitting a target in Shard B)
    delta_payload = {
        "interaction_type": interaction_type,
        "entity_a": interacting_entity_a,
        "entity_b": interacting_entity_b,
        "source_shard": shard_a.shard_id,
        "target_shard": shard_b.shard_id
    }

    # 3. Create the ChangedNode for the Delta (reusing Day 21 schemas)
    changed_node = ChangedNode(
        node_id=f"cross_shard_event_{shard_a.shard_id}_{shard_b.shard_id}",
        new_state=delta_payload
    )

    # 4. Create the StateDelta
    state_delta = StateDelta(
        changed_nodes=[changed_node]
    )

    # NOTE: In a live runtime, we would pass this state_delta to netcode_engine.broadcast().
    # The Scale Engine just generates the math. The Netcode Engine handles the broadcasting.
    # We NEVER modify netcode_engine.py.
    
    return [state_delta]


def monitor_scale(shards: List[ShardConfig], max_entities_per_shard: int, rebalance_threshold: float = 0.8) -> Tuple[List[ScaleEvent], List[ShardConfig]]:
    """
    Monitors shard health. Splits overloaded shards, merges underloaded adjacent shards.
    Returns the list of ScaleEvents and the updated list of ShardConfigs.
    """
    events = []
    active_shards = list(shards) # Create a working copy so we don't mutate the original unexpectedly
    
    # 1. Check for global scale limit warning
    total_entities = sum(s.entity_count for s in active_shards)
    if total_entities > 10000000: # Soft limit warning at 10 million
        events.append(ScaleEvent(
            event_type=ScaleEventType.REBALANCE_TRIGGERED,
            details={"type": "scale_limit_warning", "total_entities": total_entities}
        ))

    # 2. Iterate through shards to find splits and merges
    i = 0
    while i < len(active_shards):
        current_shard = active_shards[i]
        
        # --- SHARD SPLIT LOGIC ---
        # If the shard is more full than our threshold, we split it in half.
        if current_shard.entity_count > max_entities_per_shard * rebalance_threshold:
            events.append(ScaleEvent(
                event_type=ScaleEventType.SHARD_SPLIT,
                details={"shard_id": current_shard.shard_id, "entity_count": current_shard.entity_count}
            ))
            
            # Math: Cut the entity list exactly in half
            half = current_shard.entity_count // 2
            new_shard_id = max(s.shard_id for s in active_shards) + 1
            
            # Create the new sibling shard with the second half of the entities
            new_shard = ShardConfig(
                shard_id=new_shard_id,
                entity_ids=current_shard.entity_ids[half:],
                worker_id=f"{current_shard.worker_id.rsplit('_', 1)[0]}_{new_shard_id}",
                status=ShardStatus.ACTIVE,
                entity_count=current_shard.entity_count - half
            )
            
            # Update the current shard to only hold the first half
            current_shard.entity_ids = current_shard.entity_ids[:half]
            current_shard.entity_count = half
            
            active_shards.append(new_shard)

        # --- SHARD MERGE LOGIC ---
        # Look at the next shard in the list to see if we can combine them.
        if i + 1 < len(active_shards):
            next_shard = active_shards[i + 1]
            
            # If BOTH shards are less than 20% full, merge them to free up a worker.
            if (current_shard.entity_count < max_entities_per_shard * 0.2 and 
                next_shard.entity_count < max_entities_per_shard * 0.2):
                
                events.append(ScaleEvent(
                    event_type=ScaleEventType.SHARD_MERGED,
                    details={"merged_into": current_shard.shard_id, "absorbed": next_shard.shard_id}
                ))
                
                # Math: Pour the next shard's entities into the current shard
                current_shard.entity_ids.extend(next_shard.entity_ids)
                current_shard.entity_count += next_shard.entity_count
                
                # Remove the absorbed shard
                active_shards.remove(next_shard)
                
                # Because we removed an item, we don't increment 'i' yet. 
                # The new 'next_shard' will naturally slide into the i+1 position.
                continue 

        i += 1

    return events, active_shards