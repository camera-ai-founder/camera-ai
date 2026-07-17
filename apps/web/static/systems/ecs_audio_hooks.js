// File: apps/web/static/systems/ecs_audio_hooks.js
// THE ECS AUDIO HOOK: Bridging Rapier WASM Physics to the Procedural DSP Synthesizer.

class ECSAudioHook {
    constructor(world) {
        this.world = world; // The Rapier WASM physics world
        this.eventQueue = null;
        
        // A mathematical map to remember which physics collider belongs to which Entity
        this.colliderMap = new Map(); 
    }

    init() {
        // Rapier requires an EventQueue to listen to physical collisions
        if (this.world && window.RAPIER) {
            this.eventQueue = new window.RAPIER.EventQueue(true);
            console.log("ECS Audio Hook Initialized. Listening for Rapier WASM collisions.");
        } else {
            console.warn("Rapier WASM world not found. ECS Audio Hook waiting...");
        }
    }

    // Register an entity's collider so we know exactly who crashed into what
    registerCollider(colliderHandle, entityData) {
        this.colliderMap.set(colliderHandle, entityData);
    }

    // This function is called every single frame inside the main Lite ECS game loop
    processCollisions() {
        if (!this.eventQueue || !this.world) return;

        // Step the physics world forward and collect all the crash events
        this.world.step(this.eventQueue);

        // Drain the events one by one
        this.eventQueue.drainContactForceEvents((event) => {
            // Filter out tiny, harmless bumps. We only want impacts with real physical force!
            if (event.force < 2.0) return;

            // Get the physics colliders involved in the crash
            const collider1 = this.world.getCollider(event.collider1);
            const collider2 = this.world.getCollider(event.collider2);
            
            // Look up the actual Lite ECS Entities attached to those colliders
            const entity1 = this.colliderMap.get(event.collider1);
            const entity2 = this.colliderMap.get(event.collider2);

            // Find the entity that actually HAS an AudioDNA profile
            let targetEntity = null;
            if (entity1 && entity1.audio) targetEntity = entity1;
            else if (entity2 && entity2.audio) targetEntity = entity2;

            // If we found an entity with AudioDNA, synthesize the impact!
            if (targetEntity && targetEntity.audio && window.AudioSystem) {
                const dna = targetEntity.audio;
                
                // Calculate the exact 3D position of the crash in the world
                let pos = { x: 0, y: 0, z: 0 };
                if (collider1 && collider1.translation) {
                    pos = collider1.translation();
                }

                // Create a DYNAMIC impact DNA based on the physics force!
                // (A harder hit mathematically shifts the pitch and extends the decay)
                const impactDna = {
                    waveform_type: dna.waveform_type === "noise" ? "noise" : "triangle",
                    base_frequency: dna.base_frequency + (event.force * 1.5), 
                    envelope_attack: 0.001, // Impacts are always instant
                    envelope_decay: Math.min(1.0, 0.1 + (event.force / 20.0)), 
                    filter_type: "lowpass"
                };

                // TRIGGER THE DSP SYNTHESIZER IN 3D SPACE!
                window.AudioSystem.play3DSound(impactDna, pos.x, pos.y, pos.z);
            }
        });
    }
}

// We attach it to the window so the main game loop can easily access it
window.ECSAudioHook = ECSAudioHook;