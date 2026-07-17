"""
OGF (Ontological Genesis Framework) - The Localization Engine
This engine acts as the universal translator. It takes pure, language-agnostic 
concepts (SemanticTokens) and queries the Supabase Cloud Dictionary to return 
the exact human-readable string for the target language (LocaleDNA).
"""

import os
from supabase import create_client, Client
from typing import Optional
from packages.core.models import SemanticToken, LocaleDNA

class LocalizationEngine:
    """
    The bridge between universal concepts and human languages.
    It communicates strictly with the cloud to keep local resources at zero.
    """
    
    def __init__(self):
        """
        Initializes the connection to the Supabase cloud.
        We use environment variables so our API keys are kept secret and secure.
        """
        url = os.environ.get("SUPABASE_URL")
        # We use the ANON key because our Row Level Security (RLS) policies 
        # allow public read access to the dictionary. This is safe and secure.
        key = os.environ.get("SUPABASE_ANON_KEY") 
        
        if not url or not key:
            raise ValueError("Supabase credentials missing from environment variables.")
            
        self.supabase: Client = create_client(url, key)

    def get_translated_text(self, token: SemanticToken, locale: LocaleDNA) -> str:
        """
        The core translation method. 
        Takes a universal concept and a target language, and returns the exact string.
        """
        target_lang = locale.target_language
        concept_id = token.concept_id
        
        try:
            # 1. Ask the cloud for the translation row matching our concept ID
            response = self.supabase.table("semantic_dictionary") \
                .select("translations") \
                .eq("concept_id", concept_id) \
                .execute()
            
            # 2. If we got data back, process it
            if response.data and len(response.data) > 0:
                translations = response.data[0]["translations"]
                
                # 3. Check if the requested language exists in our JSONB
                if target_lang in translations:
                    base_text = translations[target_lang]
                    
                    # 4. Inject Context Variables (e.g., replacing "{player_name}" with "Sarah")
                    if token.context_vars:
                        for key, value in token.context_vars.items():
                            # Replaces {key} with the string value
                            base_text = base_text.replace(f"{{{key}}}", str(value))
                            
                    return base_text
                
                # FALLBACK 1: If the target language isn't translated yet, fallback to English
                elif "en" in translations:
                    print(f"[Localization] Warning: '{concept_id}' missing '{target_lang}'. Falling back to English.")
                    return translations["en"]
                    
        except Exception as e:
            # FALLBACK 2: If the cloud is unreachable, log the error but DO NOT CRASH
            print(f"[LocalizationEngine] Cloud query failed for '{concept_id}': {e}. Using ultimate fallback.")
            
        # ULTIMATE FALLBACK: Return the concept ID itself. 
        # The UI will show "ui_button_start" instead of "Start Game", 
        # which tells the developer a translation is missing, but the app keeps running perfectly.
        return concept_id

    def get_all_concepts_for_language(self, locale: LocaleDNA) -> dict:
        """
        Optional helper: Fetches the entire dictionary for the target language 
        to cache it locally if we want to reduce cloud calls during heavy UI rendering.
        """
        try:
            response = self.supabase.table("semantic_dictionary").select("concept_id, translations").execute()
            
            localized_cache = {}
            for row in response.data:
                concept_id = row["concept_id"]
                translations = row["translations"]
                
                if locale.target_language in translations:
                    localized_cache[concept_id] = translations[locale.target_language]
                elif "en" in translations:
                    localized_cache[concept_id] = translations["en"]
                else:
                    localized_cache[concept_id] = concept_id
                    
            return localized_cache
            
        except Exception as e:
            print(f"[LocalizationEngine] Failed to cache dictionary: {e}")
            return {}