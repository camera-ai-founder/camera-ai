// apps/web/static/genesis/parametric_breeder.js
// PRIORITY 1: THE PARAMETRIC GENOME
// This file takes the JSON from the AI and "grows" a 3D object using pure math.

import * as THREE from 'three';

/**
 * Breeds a parametric 3D object based on the AI's mathematical DNA.
 * @param {Object} genome - The ParametricGenome JSON (seed, rules, scale_factor)
 * @param {THREE.Scene} scene - The Three.js scene to add the object to
 * @returns {THREE.Group} The generated 3D group
 */
export function breedParametricObject(genome, scene) {
    const group = new THREE.Group();
    
    // 1. Setup deterministic pseudo-randomness using the AI's seed
    // This guarantees the exact same shape grows every time for a specific seed!
    let currentSeed = genome.seed || 42;
    const deterministicRandom = () => {
        currentSeed = (currentSeed * 9301 + 49297) % 233280;
        return currentSeed / 233280;
    };

    const scale = genome.scale_factor || 1.0;
    
    // A simple, clean material for our math-grown objects
    const material = new THREE.MeshStandardMaterial({ 
        color: 0x88aa55, // A nice natural green for our math "trees"
        roughness: 0.8,
        metalness: 0.1
    });

    // 2. The Recursive Growth Function (The Math Engine)
    function growBranch(position, rotation, depth, length) {
        // Stop growing if we hit the depth limit (protects the i3 laptop from infinite loops!)
        if (depth <= 0) return;

        // Create a simple branch (a stretched box)
        const geometry = new THREE.BoxGeometry(0.2 * scale, length * scale, 0.2 * scale);
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position and rotate the branch
        mesh.position.copy(position);
        mesh.position.y += (length * scale) / 2; // Anchor at the bottom of the box
        mesh.rotation.set(rotation.x, rotation.y, rotation.z);
        
        group.add(mesh);

        // 3. Spawn child branches based on deterministic math
        const numBranches = Math.floor(deterministicRandom() * 2) + 2; // 2 or 3 branches
        
        for (let i = 0; i < numBranches; i++) {
            const newLength = length * 0.65; // Child branches are 65% the size of the parent
            
            // Calculate a slightly random but deterministic rotation for the new branch
            const newRot = {
                x: rotation.x + (deterministicRandom() - 0.5) * 0.8,
                y: rotation.y + (deterministicRandom() - 0.5) * 1.5,
                z: rotation.z + (deterministicRandom() - 0.5) * 0.8
            };
            
            // Calculate where the new branch should start (at the top of the current branch)
            const offset = new THREE.Vector3(0, length * scale, 0);
            offset.applyEuler(new THREE.Euler(newRot.x, newRot.y, newRot.z));
            
            // Recursively call the function to grow the next level
            growBranch(
                position.clone().add(offset),
                newRot,
                depth - 1,
                newLength
            );
        }
    }

    // 4. Ignite the Growth!
    // We start at ground level (0,0,0), facing straight up, with a depth of 4 and length of 2.
    growBranch(new THREE.Vector3(0, 0, 0), {x: 0, y: 0, z: 0}, 4, 2.0);

    scene.add(group);
    return group;
}