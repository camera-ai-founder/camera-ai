// ==========================================
// DAY 12 & 13: THE 3D PROJECTION ENGINE
// Runs entirely in the browser. Pure Math, no heavy physics plugins!
// ==========================================

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

// ==========================================
// DAY 13 STEP 5: THE GLSL BREATHING SHADER
// ==========================================

/**
 * Creates a standard Three.js material but injects custom GLSL math 
 * to make the primitive box gently "breathe" in and out.
 */
function createBreathingMaterial(colorHex = 0x00ff00) {
    // Start with a normal material so we keep our lighting and shadows
    const material = new THREE.MeshStandardMaterial({ color: colorHex });
    
    // onBeforeCompile lets us inject our own math into Three.js's default code
    material.onBeforeCompile = function (shader) {
        // 1. Create a 'time' variable (uniform) that we can update every frame
        shader.uniforms.time = { value: 0.0 };
        
        // 2. Inject the 'time' variable into the top of the Vertex Shader
        shader.vertexShader = 'uniform float time;\n' + shader.vertexShader;
        
        // 3. Replace the default vertex math with our custom breathing math
        shader.vertexShader = shader.vertexShader.replace(
            '#include <begin_vertex>',
            `#include <begin_vertex>
            
            // --- DAY 13 GLSL MATH ---
            // sin(time * 2.0) creates a smooth wave between -1 and 1.
            // We multiply by 0.05 to keep the breathing subtle.
            // We multiply by position.y so the top of the box breathes more than the bottom.
            float breath = sin(time * 2.0) * 0.05 * position.y;
            
            // Push the corners of the box outward
            transformed += vec3(breath, breath, breath);
            `
        );
        
        // Save the shader to the material so we can update the time in our animation loop
        material.userData.shader = shader;
    };
    
    return material;
}

/**
 * Call this inside your main animation/render loop 
 * to keep the shader's internal clock moving forward.
 */
function updateBreathingMaterials(scene, elapsedTime) {
    // traverse just means "look at every object in the scene"
    scene.traverse((child) => {
        if (child.isMesh && child.material && child.material.userData && child.material.userData.shader) {
            // Feed the current time into our GLSL shader
            child.material.userData.shader.uniforms.time.value = elapsedTime;
        }
    });
}

// 1. Setup the Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a1a); // Dark, cinematic background

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;
camera.position.y = 2;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Lighting for that AAA feel
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 5, 5);
scene.add(light);
scene.add(new THREE.AmbientLight(0x404040, 0.5));

// 2. Create a Test Object (A simple box we can smash AND breathe!)
const geometry = new THREE.BoxGeometry(1, 1, 1);

// DAY 13 UPGRADE: Use our custom breathing material instead of the basic one
const material = createBreathingMaterial(0x00ff00); // Neon Green
const testMesh = new THREE.Mesh(geometry, material);
scene.add(testMesh);

// 3. Physics State (Pure Kinematic Math)
let physicsState = {
    velocityX: 0,
    velocityY: 0,
    velocityZ: 0,
    gravity: -9.8,
    decay: 0.98 // Air resistance / friction
};

// 4. The Juice Engine: Apply Impact Vector
// This function is exposed to the global 'window' so our Python backend can trigger it!
window.applyImpact = function(impactVector, ragdollDecay) {
    console.log("Applying impact!", impactVector);
    
    // Transfer the math from Python into our physics state
    physicsState.velocityX = impactVector.velocity_x;
    physicsState.velocityY = impactVector.velocity_y;
    physicsState.velocityZ = impactVector.velocity_z;
    
    // Convert the AI's "flavor" decay into physical air resistance
    physicsState.decay = 1.0 - (ragdollDecay * 0.1); 
};

// 5. The Animation Loop (Updates position using pure math)
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    
    const delta = clock.getDelta(); // Time passed since last frame
    const elapsedTime = clock.getElapsedTime(); // Total time since engine started (for the shader)

    // Apply gravity to Y velocity
    physicsState.velocityY += physicsState.gravity * delta;

    // Update mesh position based on velocity
    testMesh.position.x += physicsState.velocityX * delta;
    testMesh.position.y += physicsState.velocityY * delta;
    testMesh.position.z += physicsState.velocityZ * delta;

    // Apply decay (air resistance) to X and Z so it eventually stops sliding
    physicsState.velocityX *= physicsState.decay;
    physicsState.velocityZ *= physicsState.decay;

    // Simple floor collision (don't let it fall into the void forever)
    if (testMesh.position.y < -0.5) {
        testMesh.position.y = -0.5;
        // Bounce! Reverse velocity and lose some energy
        physicsState.velocityY = -physicsState.velocityY * 0.5; 
    }

    // DAY 13: Tell our breathing shader what time it is so it can animate
    updateBreathingMaterials(scene, elapsedTime);

    // Render the frame
    renderer.render(scene, camera);
}

// Start the engine!
animate();

// Handle browser window resizing so it always looks perfect
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});