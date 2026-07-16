/**
 * TELEMETRY PROFILER
 * The lightweight watchdog that measures Three.js frame times and reports 
 * health back to the AI Brain via our Flask backend.
 */

export class TelemetryProfiler {
    constructor(config = {}) {
        // Health rules injected from our TelemetryDNA
        this.fpsThreshold = config.fpsThreshold || 60.0;
        this.maxMemoryMB = config.maxMemoryMB || 512;
        
        // Reporting rules
        this.reportIntervalMs = config.reportIntervalMs || 2000; // Send report every 2 seconds
        
        // Internal state
        this.frameCount = 0;
        this.accumulatedFps = 0;
        this.droppedFrames = 0;
        this.lastTime = performance.now();
        this.lastReportTime = performance.now();
        
        // The exact endpoint our Flask backend is listening on
        this.backendUrl = config.backendUrl || '/api/telemetry/report';
    }

    /**
     * Call this method inside your Three.js requestAnimationFrame loop.
     * @param {number} currentTime - performance.now()
     */
    tick(currentTime) {
        const deltaMs = currentTime - this.lastTime;
        this.lastTime = currentTime;

        // Prevent division by zero or negative time
        if (deltaMs > 0) {
            const currentFps = 1000 / deltaMs;
            this.accumulatedFps += currentFps;
            this.frameCount++;

            // If a frame takes longer than 16.6ms (60fps), count it as dropped
            if (deltaMs > 16.67) {
                this.droppedFrames++;
            }
        }

        // Check if it's time to send a report to the backend
        if (currentTime - this.lastReportTime >= this.reportIntervalMs) {
            this.evaluateAndReport(currentTime);
            // Reset counters for the next interval
            this.frameCount = 0;
            this.accumulatedFps = 0;
            this.droppedFrames = 0;
            this.lastReportTime = currentTime;
        }
    }

    evaluateAndReport(currentTime) {
        if (this.frameCount === 0) return; // No frames rendered, nothing to report

        const rollingAverageFps = this.accumulatedFps / this.frameCount;
        
        // Determine the bottleneck based on our strict DNA rules
        let bottleneck = "none";
        if (rollingAverageFps < this.fpsThreshold) {
            // For now, if FPS drops, we flag the renderer. 
            bottleneck = "render"; 
        }

        // Construct the exact JSON payload matching our Pydantic PerformanceReport
        const report = {
            report_id: crypto.randomUUID(),
            timestamp_ms: Math.floor(currentTime),
            current_fps: parseFloat(rollingAverageFps.toFixed(2)),
            dropped_frames: this.droppedFrames,
            memory_usage_mb: this.getMemoryUsageMB(),
            bottleneck_component: bottleneck
        };

        // Only send the report if we are unhealthy, OR if we just recovered.
        // This saves network bandwidth.
        if (rollingAverageFps < this.fpsThreshold || bottleneck !== "none") {
            this.sendToBackend(report);
        }
    }

    getMemoryUsageMB() {
        // Use the browser's performance API if available (Chrome/Edge)
        if (performance.memory) {
            return parseFloat((performance.memory.usedJSHeapSize / 1048576).toFixed(2));
        }
        return 0.0; // Fallback for browsers that hide memory stats
    }

    async sendToBackend(report) {
        try {
            // Fire and forget. We do not block the main render thread.
            fetch(this.backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(report),
                keepalive: true // Ensures the request finishes even if the page is closing
            });
        } catch (error) {
            // The telemetry system must NEVER crash the main game loop.
            console.warn('Telemetry heartbeat failed silently:', error);
        }
    }
}