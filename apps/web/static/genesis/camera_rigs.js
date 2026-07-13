// apps/web/static/genesis/camera_rigs.js
// PRIORITY 4 & 5: THE AI CINEMATOGRAPHER & PROCEDURAL VFX
// This file uses pure math to create Hollywood-style camera movements and cinematic fog.

import * as THREE from 'three';

/**
 * Applies deterministic Hollywood camera movements based on the AI's CameraAction JSON.
 * @param {THREE.Camera} camera - The Three.js camera to manipulate.
 * @param {Object} action - The CameraAction JSON (movement_type, intensity, etc.).
 * @param {number} time - The current elapsed time in seconds (used for math waves).
 */
export function executeCameraRig(camera, action, time) {
    if (!action || action.movement_type === "static") return; // No math needed if static!

    const intensity = action.intensity || 1.0;

    // PRIORITY 4: THE AI CINEMATOGRAPHER
    switch (action.movement_type) {
        case "shaky_cam":
            // We use the Math.sin() wave function to create a violent, handheld camera feel.
            // This is incredibly cheap to compute and looks very cinematic.
            camera.position.x += Math.sin(time * 15) * 0.05 * intensity;
            camera.position.y += Math.cos(time * 12) * 0.05 * intensity;
            break;

        case "orbit":
            // Smoothly circles the target using basic circle math (sine for X, cosine for Z).
            const radius = 5;
            camera.position.x = Math.sin(time * 0.5) * radius;
            camera.position.z = Math.cos(time * 0.5) * radius;
            camera.lookAt(0, 0, 0); // Keep looking at the center
            break;

        case "dolly_zoom":
            // The "Vertigo" effect. Move camera forward, but zoom lens out (simplified for this engine).
            camera.position.z -= 0.02 * intensity;
            camera.fov += 0.1 * intensity;
            camera.updateProjectionMatrix(); // Required when changing FOV
            break;
    }
}

/**
 * Applies mathematical VFX to the scene based on the AI's VFXProfile JSON.
 * @param {THREE.Scene} scene - The Three.js scene.
 * @param {Object} vfx - The VFXProfile JSON (fog_density, etc.).
 */
export function applyVFX(scene, vfx) {
    if (!vfx) return;

    // PRIORITY 5: PROCEDURAL CINEMATIC VFX
    // We apply volumetric-style fog using Three.js built-in math.
    if (vfx.fog_density > 0) {
        // The higher the density, the closer the fog starts and ends.
        // We multiply by 10 to turn the AI's 0.0-1.0 scale into realistic 3D distances.
        const nearDistance = 1;
        const farDistance = 50 - (vfx.fog_density * 40); 
        
        scene.fog = new THREE.Fog(0x111111, nearDistance, farDistance);
        scene.background = new THREE.Color(0x111111); // Match background to fog color for seamless blending
    }
}