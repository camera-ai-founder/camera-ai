/**
 * ==========================================================
 * DAY 29: THE MATHEMATICAL UI OVERLAY
 * ==========================================================
 * This system rejects hardcoded text boxes. 
 * Instead, it reads the TutorialDNA and projects pure, 
 * mathematical visual cues (CSS animations and DOM math) 
 * to guide the player's eye naturally.
 */

export class TutorialOverlaySystem {
    constructor() {
        // The container where our hints will live
        this.container = document.getElementById('tutorial-overlay-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'tutorial-overlay-container';
            this.container.style.position = 'fixed';
            this.container.style.top = '0';
            this.container.style.left = '0';
            this.container.style.width = '100%';
            this.container.style.height = '100%';
            this.container.style.pointerEvents = 'none'; // Never block game clicks
            this.container.style.zIndex = '9999';
            document.body.appendChild(this.container);
        }

        // Track active DOM elements by concept_id so we can fade them out later
        this.activeElements = {};

        // Inject our mathematical CSS keyframes into the document head
        this._injectGlobalStyles();
    }

    /**
     * Injects the CSS animations. 
     * We use CSS variables to let the JS math control the speed and intensity.
     */
    _injectGlobalStyles() {
        const style = document.createElement('style');
        style.innerHTML = `
            .tutorial-hint {
                position: absolute;
                transition: opacity 0.5s ease-out;
            }

            /* The Pulsing Icon (e.g., a subtle gamepad button glowing) */
            .hint-pulsing-input-icon {
                width: 60px;
                height: 60px;
                background: radial-gradient(circle, rgba(56,189,248,0.8) 0%, rgba(56,189,248,0) 70%);
                border-radius: 50%;
                animation: math-pulse var(--pulse-speed, 2s) infinite ease-in-out;
                top: 80%;
                left: 50%;
                transform: translateX(-50%);
            }

            /* The Glowing Vector (e.g., a subtle directional line) */
            .hint-glowing-vector {
                width: 4px;
                height: 100px;
                background: linear-gradient(to top, rgba(239,68,68,0.9), rgba(239,68,68,0));
                box-shadow: 0 0 15px rgba(239,68,68,var(--glow-intensity, 0.5));
                top: 30%;
                left: 50%;
                transform: translateX(-50%);
                animation: vector-breathe var(--pulse-speed, 2s) infinite ease-in-out;
            }

            @keyframes math-pulse {
                0%, 100% { transform: translateX(-50%) scale(0.8); opacity: 0.3; }
                50% { transform: translateX(-50%) scale(1.2); opacity: 1.0; }
            }

            @keyframes vector-breathe {
                0%, 100% { height: 80px; opacity: 0.4; }
                50% { height: 120px; opacity: 1.0; }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Renders or updates a hint based on the engine's data.
     * @param {Object} hintData - { concept_id, hint_visual_type, urgency }
     */
    renderHint(hintData) {
        const { concept_id, hint_visual_type, urgency } = hintData;

        // If the element already exists, just update the math variables
        if (this.activeElements[concept_id]) {
            this._updateMathVariables(this.activeElements[concept_id], urgency);
            return;
        }

        // Create the new visual element
        const el = document.createElement('div');
        el.classList.add('tutorial-hint');
        el.dataset.conceptId = concept_id;

        // Map the DNA visual type to our CSS class
        if (hint_visual_type === 'pulsing_input_icon') {
            el.classList.add('hint-pulsing-input-icon');
        } else if (hint_visual_type === 'glowing_vector') {
            el.classList.add('hint-glowing-vector');
        } else {
            el.classList.add('hint-pulsing-input-icon'); // Fallback
        }

        // Apply the initial math variables based on urgency (0.0 to 1.0)
        this._updateMathVariables(el, urgency);

        this.container.appendChild(el);
        this.activeElements[concept_id] = el;
    }

    /**
     * The core math: Translates the engine's "urgency" float 
     * into visual speed and intensity.
     * High urgency = faster pulse, brighter glow.
     */
    _updateMathVariables(element, urgency) {
        // Clamp urgency between 0.1 and 1.0 to prevent division by zero or invisible states
        const u = Math.max(0.1, Math.min(1.0, urgency));

        // As urgency goes up, speed gets faster (from 2.5s down to 0.5s)
        const pulseSpeed = 2.5 - (u * 2.0); 
        element.style.setProperty('--pulse-speed', `${pulseSpeed}s`);

        // As urgency goes up, glow intensity gets brighter (from 0.3 to 1.0)
        element.style.setProperty('--glow-intensity', (0.3 + (u * 0.7)).toString());
        
        // Ensure it is visible
        element.style.opacity = '1';
    }

    /**
     * Instantly vanishes the hint the moment the player succeeds.
     * The player feels like a genius. No "Tutorial Complete" text.
     */
    suppressHint(concept_id) {
        const el = this.activeElements[concept_id];
        if (el) {
            // Smooth fade out using CSS transition
            el.style.opacity = '0';
            
            // Remove from DOM after transition finishes
            setTimeout(() => {
                if (el.parentNode) {
                    el.parentNode.removeChild(el);
                }
                delete this.activeElements[concept_id];
            }, 500);
        }
    }

    /**
     * Clears all hints (e.g., if the player dies or pauses the game).
     */
    clearAll() {
        Object.keys(this.activeElements).forEach(id => this.suppressHint(id));
    }
}