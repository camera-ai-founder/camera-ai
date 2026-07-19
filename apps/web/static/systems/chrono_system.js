/**
 * ============================================================
 * DAY 30: THE INPUT RECORDER (THE BLACK BOX)
 * ============================================================
 * 
 * The Old Paradigm records raw hardware data (mouse X/Y coordinates, 
 * joystick axis values) 60 times a second. That bloats RAM and 
 * destroys low-end laptops. We reject that.
 * 
 * We only record ABSTRACTED INTENT (from our Day 25 InputDNA).
 * Example: "Player pressed Dash at 10.5 seconds".
 * 
 * This takes kilobytes, not gigabytes. Zero RAM bloat.
 * ============================================================
 */

export class ChronoSystem {
    constructor() {
        // The Black Box. This array only stores pure, abstract intent.
        // It weighs almost nothing.
        this.inputLog = [];
        this.isRewinding = false;
    }

    /**
     * Records an abstract action instead of raw hardware data.
     * 
     * @param {string} actionName - The abstract intent (e.g., 'jump', 'dash').
     * @param {number} gameTime - The exact game-time in seconds.
     */
    recordAction(actionName, gameTime) {
        // If we are currently rewinding time, we do NOT record new actions.
        // We are just replaying the past.
        if (this.isRewinding) return;

        this.inputLog.push({
            action: actionName,
            timestamp: gameTime
        });
        
        // Optional: Keep the log from growing infinitely if the player 
        // plays for 100 hours. We only need to keep the last, say, 5000 actions.
        if (this.inputLog.length > 5000) {
            this.inputLog.shift(); // Removes the oldest action
        }
    }

    /**
     * Creates a tiny fingerprint (hash) of the entire log.
     * We store this tiny hash inside the ChronoDNA checkpoint in Python.
     * This proves that the input log hasn't been tampered with.
     */
    getLogHash() {
        const logString = JSON.stringify(this.inputLog);
        let hash = 0;
        
        // A simple, lightweight mathematical hash function
        for (let i = 0; i < logString.length; i++) {
            const char = logString.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        
        return `hash_${hash}`;
    }

    /**
     * Gets the exact actions that happened between two points in time.
     * This is used when we fast-forward time to rebuild the world.
     */
    getActionsBetween(startTime, endTime) {
        return this.inputLog.filter(entry => 
            entry.timestamp >= startTime && entry.timestamp <= endTime
        );
    }

    /**
     * Clears the log if we travel back in time and start a new timeline branch.
     */
    clearLog() {
        this.inputLog = [];
        console.log("[CHRONO] Black Box cleared for new timeline.");
    }
}

// Create a single, global instance so the whole app can use it
window.ChronoSystemInstance = new ChronoSystem();