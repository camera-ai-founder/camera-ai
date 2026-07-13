// apps/web/static/genesis/unifier_shader.js
// PRIORITY 3: THE UNIFIER SHADER (COHESION ENGINE)
// This file strips original lighting from Swarm assets and forces them into a global art style.

import * as THREE from 'three';

// The GLSL Vertex Shader: Tells the GPU where the shape's points are.
const vertexShader = `
    void main() {
        // Standard math to project the 3D point onto your 2D screen
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
`;

// The GLSL Fragment Shader: Tells the GPU what color to paint every single pixel.
const fragmentShader = `
    uniform vec3 globalColor;
    uniform float ambientIntensity;
    
    void main() {
        // We completely ignore the downloaded model's original textures!
        // We force everything into our master art style using pure math.
        vec3 finalColor = globalColor * ambientIntensity;
        
        // Output the cohesive, stylized color
        gl_FragColor = vec4(finalColor, 1.0);
    }
`;

/**
 * Creates the Master Unifier Shader.
 * @param {THREE.Color} color - The global palette color to force on the scene.
 * @returns {THREE.ShaderMaterial} The deterministic cohesive material.
 */
export function createUnifierShader(color) {
    return new THREE.ShaderMaterial({
        vertexShader: vertexShader,
        fragmentShader: fragmentShader,
        uniforms: {
            globalColor: { value: color },
            ambientIntensity: { value: 0.8 } // A soft, cinematic ambient light level
        }
    });
}