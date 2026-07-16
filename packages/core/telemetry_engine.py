import os
import json
import logging
from groq import Groq
from typing import Optional

# Import our strict DNA schemas from the models we just upgraded
from packages.core.models import (
    AppDNA, 
    PerformanceReport, 
    BottleneckType
)

# Set up standard logging so we can see the self-healing in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelemetryEngine")

class TelemetryEngine:
    """
    The AI Feedback Loop. It receives performance reports, consults the Groq Brain,
    and forces the AI to output strictly validated, downgraded JSON DNA to heal the engine.
    """
    
    def __init__(self):
        # Initialize the Groq client. 
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found. Self-healing will operate in mock mode.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            
        # Match the model used in brain.py for consistency
        self.model = "llama-3.3-70b-versatile" 

    def generate_healing_prompt(self, report: PerformanceReport, current_dna: AppDNA) -> str:
        """Constructs a highly specific, context-rich prompt for the AI."""
        
        # Convert our current DNA into a clean JSON string for the AI to read
        current_dna_json = current_dna.model_dump_json(indent=2)
        
        # Convert the bad performance report into JSON
        report_json = report.model_dump_json()

        # THE FIX: Safely extract the bottleneck name whether it's a strict Enum or a plain string
        bottleneck_name = report.bottleneck_component.value if hasattr(report.bottleneck_component, 'value') else report.bottleneck_component

        prompt = f"""
        You are the Genesis Engine Self-Healing Core.
        
        CURRENT SYSTEM STATE:
        The engine is lagging. Here is the exact telemetry report:
        {report_json}
        
        CURRENT MASTER DNA:
        Here is the current AppDNA configuration:
        {current_dna_json}
        
        YOUR MISSION:
        The current {bottleneck_name} is causing dropped frames. 
        You MUST downgrade the configuration to restore a flawless 60fps.
        Specifically, adjust the 'renderer' (PriorityDualEngineDNA) and 'drama_budget' fields.
        Reduce VFX complexity, disable heavy shadows, or lower entity caps.
        
        CRITICAL RULES:
        1. Do NOT write python code. Do NOT write explanations.
        2. You MUST output ONLY the fully updated JSON for the entire AppDNA.
        3. The JSON MUST strictly adhere to the original AppDNA schema.
        """
        return prompt.strip()

    def heal_dna(self, report: PerformanceReport, current_dna: AppDNA) -> AppDNA:
        """
        The main self-correction loop.
        Takes the bad report, asks Groq for a fix, and returns the new validated DNA.
        """
        # Safely check if the system is perfectly healthy
        is_healthy = (report.bottleneck_component == BottleneckType.NONE or report.bottleneck_component == "none") and report.current_fps >= current_dna.telemetry.fps_threshold
        
        if is_healthy:
            return current_dna

        logger.info(f"🚨 Performance Drop Detected! FPS: {report.current_fps}. Initiating AI Self-Healing...")

        if not self.client:
            logger.warning("No Groq client. Returning original DNA (Mock Mode).")
            return current_dna

        prompt = self.generate_healing_prompt(report, current_dna)

        try:
            # Ask the AI Brain for the new DNA
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert system architect and performance optimizer. You only output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1, # Keep it highly deterministic and strict
                response_format={"type": "json_object"} # Force Groq to output pure JSON
            )
            
            raw_response = chat_completion.choices[0].message.content
            logger.info("AI Brain responded. Validating the new DNA against our Pydantic shields...")

            # THE GOD-TIER SHIELD: Pydantic Validation
            healed_dna = AppDNA.model_validate_json(raw_response)
            
            logger.info("✅ DNA Successfully Healed and Validated. Sending to frontend.")
            return healed_dna

        except Exception as e:
            logger.error(f"❌ AI Self-Healing Failed. The AI tried to break the schema. Error: {e}")
            # If the AI fails, we protect the engine by returning the original, stable DNA.
            return current_dna

# Create a singleton instance so the whole app shares the same Brain
telemetry_brain = TelemetryEngine()