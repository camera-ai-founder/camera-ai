# packages/core/genesis_renderer.py
# PRIORITY 2 & 6: THE ASSET SWARM & VOICE/EMOTION LAYER
# This file acts as the bridge between the AI's requests, 3D asset APIs, and local TTS.

import logging
from packages.core.models import VisualQuery

# Setup a logger so we can see what the engine is doing in our terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenesisRenderer:
    def __init__(self):
        self.api_base_url = "https://api.sketchfab.com/v3/models"
        
    def process_visual_query(self, query: VisualQuery) -> dict:
        """
        Handles the AI's request for a downloaded 3D asset (Priority 2).
        """
        if not query.fallback_flag:
            return {"status": "skipped", "reason": "Parametric math is sufficient."}

        search_string = " ".join(query.search_terms)
        logger.info(f"🎨 Asset Swarm querying for: '{search_string}'")

        mock_api_request = f"{self.api_base_url}?search={search_string}&downloadable=true&sort_by=-likeCount&count=1"
        
        mock_downloaded_asset = {
            "status": "success",
            "asset_url": f"https://mock-cdn.com/assets/{search_string.replace(' ', '_').lower()}.glb",
            "poly_count": 8500,  
            "format": "glTF",
            "api_request_used": mock_api_request
        }

        if mock_downloaded_asset["poly_count"] > query.max_poly_count:
            logger.warning(f"❌ Asset rejected! Poly count {mock_downloaded_asset['poly_count']} exceeds the safety limit of {query.max_poly_count}.")
            return {"status": "failed", "reason": "Asset too heavy for browser RAM. Fall back to math."}

        logger.info(f"✅ Asset Swarm found a safe model: {mock_downloaded_asset['asset_url']}")
        return {"status": "success", "asset_data": mock_downloaded_asset}

    def generate_voice_and_emotion(self, dialogue: str, emotion: str = "neutral") -> dict:
        """
        PRIORITY 6: VOICE & EMOTION LAYER
        Generates local TTS audio for the AI's dialogue and calculates lip-sync math.
        """
        logger.info(f"🎙️ Generating TTS for dialogue: '{dialogue}' with emotion: {emotion}")
        
        mock_audio_buffer = f"[Audio Buffer: {len(dialogue)} words spoken with {emotion} tone]"
        lip_sync_intensity = 0.9 if emotion in ["angry", "shouting"] else 0.5
        
        return {
            "status": "success",
            "audio_data": mock_audio_buffer,
            "lip_sync_intensity": lip_sync_intensity
        }

# Initialize a global instance for our Brain and CLI to use easily
genesis_renderer = GenesisRenderer()