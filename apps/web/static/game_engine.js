// ==========================================
// DAY 12: THE 3D PROJECTION ENGINE
// Runs entirely in the browser. Pure Math, no heavy physics plugins!
// ==========================================

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

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

// 2. Create a Test Object (A simple box we can smash!)
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 }); // Neon Green
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