// File: apps/web/static/systems/audio_system.js
// THE DSP SYNTHESIZER: Pure Math, Zero Files, Now in 3D Space.
// DAY 27 UPDATE: Added Audio Cadence Shift for Localization.

class AudioSystem {
    constructor() {
        this.audioContext = null;
        this.masterGain = null;
        this.listener = null;
        this.isInitialized = false;
        
        // DAY 27: Store the Localization DNA to apply cadence shifts
        this.localeDNA = null; 
    }

    // DAY 27: Method to inject LocaleDNA into the audio engine
    setLocale(localeDNA) {
        this.localeDNA = localeDNA;
        console.log(`[AudioSystem] Locale set to: ${this.localeDNA?.target_language || 'en'} | Cadence Shift: ${this.localeDNA?.audio_cadence_shift || 0.0}`);
    }

    // We initialize the AudioContext only when needed to save resources
    init() {
        if (this.isInitialized) return;
        
        // Create the blank canvas for our math-based sounds
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create a master volume knob so we can control the global loudness
        this.masterGain = this.audioContext.createGain();
        this.masterGain.gain.value = 0.5; // Keep it at a safe 50% volume
        
        // Connect the master knob to the browser's actual speakers
        this.masterGain.connect(this.audioContext.destination);
        
        // Initialize the Listener (The "Ears" of our Camera)
        this.listener = this.audioContext.listener;
        
        this.isInitialized = true;
        console.log("Audio System Initialized. Procedural 3D DSP ready. Zero megabytes loaded.");
    }

    // Helper: Generate pure mathematical white noise for impacts
    createNoiseBuffer() {
        // Create a buffer that holds 0.5 seconds of audio data
        const bufferSize = this.audioContext.sampleRate * 0.5; 
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);
        
        // Fill the buffer with random numbers between -1 and 1 (static/white noise)
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1; 
        }
        return buffer;
    }

    // ==========================================
    // SPATIAL AUDIO (THE 3D PANNER)
    // ==========================================
    
    // This updates our "Ears" so the browser knows where the Camera is looking
    updateListenerPosition(x, y, z) {
        if (!this.isInitialized) return;
        if (this.listener.positionX) {
            this.listener.positionX.value = x;
            this.listener.positionY.value = y;
            this.listener.positionZ.value = z;
        } else {
            this.listener.setPosition(x, y, z); // Fallback for older browsers
        }
    }

    // THE CORE 3D SYNTHESIZER: Reads AudioDNA and generates sound in 3D space
    play3DSound(dna, x, y, z) {
        if (!this.isInitialized) this.init();

        const now = this.audioContext.currentTime;

        // DAY 27: AUDIO CADENCE SHIFT
        // Read the shift value (e.g., 0.1 for fast languages, -0.1 for slow)
        const cadenceShift = this.localeDNA?.audio_cadence_shift || 0.0;
        
        // Fast languages (positive shift) get a smaller time multiplier (faster envelope)
        // Slow languages (negative shift) get a larger time multiplier (slower envelope)
        // We use Math.max to ensure the time never drops below 10% to prevent audio glitches
        const timeMultiplier = Math.max(0.1, 1.0 - (cadenceShift * 0.5));

        // 1. Create the PannerNode (The 3D Spatializer)
        const panner = this.audioContext.createPanner();
        panner.panningModel = 'HRTF'; // HRTF uses complex math to mimic how human ears hear 3D space
        panner.distanceModel = 'inverse';
        panner.refDistance = 1;
        panner.maxDistance = 100;
        panner.rolloffFactor = 1; // How fast the sound gets quiet as you walk away

        // Set the exact X, Y, Z coordinates of the object making the sound
        if (panner.positionX) {
            panner.positionX.value = x;
            panner.positionY.value = y;
            panner.positionZ.value = z;
        } else {
            panner.setPosition(x, y, z);
        }

        // 2. Create the Envelope (The Volume Shape)
        const gainNode = this.audioContext.createGain();
        gainNode.gain.setValueAtTime(0, now); // Start at zero volume
        
        // DAY 27: Apply timeMultiplier to attack and decay
        const finalAttack = dna.envelope_attack * timeMultiplier;
        const finalDecay = dna.envelope_decay * timeMultiplier;
        
        gainNode.gain.linearRampToValueAtTime(1, now + finalAttack); 
        gainNode.gain.exponentialRampToValueAtTime(0.001, now + finalAttack + finalDecay);

        // 3. Create the Filter (The Tone Shaper)
        let lastNode = gainNode;
        if (dna.filter_type && dna.filter_type !== "none") {
            const filter = this.audioContext.createBiquadFilter();
            filter.type = dna.filter_type;
            filter.frequency.value = 1000; // Base cutoff frequency
            gainNode.connect(filter);
            lastNode = filter; 
        }

        // 4. Create the Sound Source (The Waveform)
        let source;
        if (dna.waveform_type === "noise") {
            source = this.audioContext.createBufferSource();
            source.buffer = this.createNoiseBuffer();
            // DAY 27: Shift noise speed using playbackRate
            source.playbackRate.value = 1.0 + (cadenceShift * 0.5);
        } else {
            source = this.audioContext.createOscillator();
            source.type = dna.waveform_type;
            source.frequency.setValueAtTime(dna.base_frequency, now);
            // DAY 27: Shift oscillator "weight" using detune (in cents)
            source.detune.setValueAtTime(cadenceShift * 100, now);
        }

        // 5. Wire it all together in the correct order!
        source.connect(gainNode);       // Source -> Envelope
        lastNode.connect(panner);       // Envelope -> Filter -> 3D Panner
        panner.connect(this.masterGain);// 3D Panner -> Master Output

        // 6. Play the sound and clean it up when finished
        source.start(now);
        source.stop(now + finalAttack + finalDecay + 0.1);
    }

    // ==========================================
    // STANDARD 2D SOUNDS (For UI clicks, etc.)
    // ==========================================

    // Standard 2D play for UI elements that don't need 3D space
    playSound(dna) {
        if (!this.isInitialized) this.init();
        // Just pass X:0, Y:0, Z:0 to place it directly inside the listener's head
        this.play3DSound(dna, 0, 0, 0);
    }

    // ==========================================
    // PRE-BUILT ARCHETYPES (For quick testing)
    // ==========================================

    playCyberpunkHum() {
        this.playSound({
            waveform_type: "sine",
            base_frequency: 60.0, 
            envelope_attack: 2.0, 
            envelope_decay: 5.0,  
            filter_type: "lowpass"
        });
    }

    playImpact() {
        this.playSound({
            waveform_type: "noise",
            base_frequency: 0.0, 
            envelope_attack: 0.001, 
            envelope_decay: 0.15,   
            filter_type: "lowpass"
        });
    }
}

// We attach it to the window so our Lite ECS can easily call it in Step 5
window.AudioSystem = new AudioSystem();