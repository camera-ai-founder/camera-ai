/**
 * THE FRONTEND HOOK (TIER 1 MUSCLE)
 * Day 25: Deterministic Action Mapping
 * 
 * This system listens to physical hardware (keyboard/mouse) and translates it 
 * into pure "Intent" using our Deterministic Map. It then feeds that intent 
 * directly into the Lite ECS loop for the physics engine to consume.
 */

class InputSystem {
    constructor() {
        // This is our Universal Translator map.
        // The backend will send us this JSON map when the game loads!
        this.inputMap = {};
        
        // The current context (gameplay, ui, cinematic)
        this.currentContext = "gameplay";

        // The list of actions currently being pressed (e.g., ["jump", "dash"])
        // Our Lite ECS physics loop will read from this every single frame!
        this.activeActions = new Set();

        // Bind the hardware listeners safely
        this.setupListeners();
    }

    /**
     * The Backend calls this to give the Frontend the DNA map.
     * @param {Object} mapFromBackend - The JSON map of unique keys to actions
     * @param {string} initialContext - The starting context (usually "gameplay")
     */
    loadInputMap(mapFromBackend, initialContext) {
        this.inputMap = mapFromBackend;
        this.currentContext = initialContext || "gameplay";
        console.log("✅ Input DNA loaded successfully! Map:", this.inputMap);
    }

    /**
     * Switches the Traffic Cop to a new mode (e.g., "cinematic")
     * @param {string} newContext - The new mode ("gameplay", "ui", or "cinematic")
     */
    setContext(newContext) {
        this.currentContext = newContext;
        console.log("🚦 Context switched to:", this.currentContext);
    }

    /**
     * Sets up the physical hardware listeners.
     * NO hardcoded "if (key == 'w')" logic here!
     */
    setupListeners() {
        window.addEventListener('keydown', (event) => this.handleKey(event, true));
        window.addEventListener('keyup', (event) => this.handleKey(event, false));
    }

    /**
     * The Universal Translator logic in JavaScript.
     * @param {KeyboardEvent} event - The physical hardware interrupt
     * @param {boolean} isPressed - True if key down, false if key up
     */
    handleKey(event, isPressed) {
        // Get the physical key pressed (e.g., "Space", "KeyW")
        const hardwarePressed = event.code; 

        // Build the unique key exactly like we did in Python
        const uniqueKey = `${hardwarePressed}_${this.currentContext}`;

        // Look up the "Intent" (e.g., "jump")
        const actionIntent = this.inputMap[uniqueKey];

        // If the DNA says this key does something in this context...
        if (actionIntent) {
            if (isPressed) {
                // Tell the Lite ECS: "The player is trying to JUMP!"
                this.activeActions.add(actionIntent);
            } else {
                // Tell the Lite ECS: "The player stopped trying to jump."
                this.activeActions.delete(actionIntent);
            }
        }
    }

    /**
     * The Lite ECS physics loop calls this every frame to know what to do.
     * @returns {Array} A list of active intents (e.g., ["jump", "move_forward"])
     */
    getActiveActions() {
        return Array.from(this.activeActions);
    }
}

// Create the global instance so the rest of the Genesis Engine can use it
window.GenesisInputSystem = new InputSystem();