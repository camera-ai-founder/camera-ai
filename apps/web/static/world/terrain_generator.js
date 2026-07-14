import * as THREE from 'three';

/**
 * DAY 16: DETERMINISTIC TERRAIN GENERATOR
 * Takes the 2D mathematical noise grid from Python and turns it into a 3D mesh.
 */
export function generateTerrainMesh(heightmapData, biomeDNA) {
    // 1. Get the dimensions of our math grid from Python
    const rows = heightmapData.length;
    const cols = heightmapData[0].length;

    // 2. Create a flat piece of digital "paper" (PlaneGeometry)
    // We use (cols - 1) segments so the grid of dots matches our Python grid exactly.
    // We multiply by 2 to give it some physical scale in the 3D world.
    const geometry = new THREE.PlaneGeometry(cols * 2, rows * 2, cols - 1, rows - 1);

    // 3. THE MATH MAGIC: Displace the vertices!
    const positions = geometry.attributes.position;
    
    for (let i = 0; i < positions.count; i++) {
        // Map the 1D vertex array back to our 2D grid coordinates
        const row = Math.floor(i / cols);
        const col = i % cols;

        // Get the mathematical noise value (0.0 to 1.0) from our Python array
        const noiseValue = heightmapData[row][col];

        // Calculate the physical height. 
        // We multiply by the Biome's elevation_curve and a max height factor (15.0)
        const height = noiseValue * biomeDNA.elevation_curve * 15.0;

        // The Plane faces the camera initially, so 'Z' is the up/down axis before we rotate it
        positions.setZ(i, height);
    }

    // Tell Three.js we changed the shape, so it needs to update the graphics card
    positions.needsUpdate = true;
    
    // Recalculate how the light hits the hills so they look 3D, not flat
    geometry.computeVertexNormals();

    // 4. Create the visual skin (Material)
    // flatShading: true gives it that highly stylized, lightweight low-poly aesthetic
    const material = new THREE.MeshStandardMaterial({ 
        color: 0x22c55e, // A nice base green (we can map moisture to color later!)
        flatShading: true, 
        wireframe: false
    });

    const mesh = new THREE.Mesh(geometry, material);
    
    // Rotate the flat plane 90 degrees so it lays flat on the ground (X/Z plane)
    mesh.rotation.x = -Math.PI / 2;

    return mesh;
}