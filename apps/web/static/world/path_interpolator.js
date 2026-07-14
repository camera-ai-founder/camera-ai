import * as THREE from 'three';

/**
 * The Path Interpolator.
 * Takes a deterministic list of waypoints from our Python A* engine 
 * and smoothly moves a Three.js mesh along that path.
 * No heavy physics, no AI hallucinations. Just pure, smooth math.
 */
export class PathInterpolator {
    constructor(mesh, speed = 5.0) {
        this.mesh = mesh;
        this.speed = speed; // Units per second
        this.waypoints = [];
        this.currentIndex = 0;
        this.isMoving = false;
    }

    /**
     * Receives the path from the Python backend.
     * @param {Array} pathArray - List of coordinates, e.g., [{x: 10, z: 5}, {x: 12, z: 5}]
     */
    setPath(pathArray) {
        // Convert our 2D Python coordinates into 3D Three.js vectors.
        // We keep the mesh's current Y (height) so it doesn't fall through the floor.
        this.waypoints = pathArray.map(point => 
            new THREE.Vector3(point.x, this.mesh.position.y, point.z)
        );
        
        this.currentIndex = 0;
        this.isMoving = this.waypoints.length > 1;
    }

    /**
     * Called every frame by the main game loop.
     * @param {number} deltaTime - Time passed since last frame (keeps speed consistent)
     */
    update(deltaTime) {
        if (!this.isMoving || this.currentIndex >= this.waypoints.length - 1) {
            this.isMoving = false;
            return;
        }

        const targetWaypoint = this.waypoints[this.currentIndex + 1];
        
        // Calculate direction and distance to the next breadcrumb
        const direction = new THREE.Vector3().subVectors(targetWaypoint, this.mesh.position);
        const distance = direction.length();

        // If we are practically touching the waypoint, snap to it and grab the next one
        if (distance < 0.1) {
            this.mesh.position.copy(targetWaypoint);
            this.currentIndex++;
            return;
        }

        // Normalize the direction (make it exactly length 1)
        direction.normalize();

        // Calculate how far we should move this exact frame
        const moveDistance = this.speed * deltaTime;

        // Deterministic Movement: Move exactly along the math line
        if (moveDistance >= distance) {
            this.mesh.position.copy(targetWaypoint);
            this.currentIndex++;
        } else {
            this.mesh.position.add(direction.multiplyScalar(moveDistance));
        }
        
        // Make the entity smoothly rotate to face the direction they are walking
        if (distance > 0.1) {
            const lookAtPos = new THREE.Vector3().addVectors(this.mesh.position, direction);
            this.mesh.lookAt(lookAtPos);
        }
    }
}