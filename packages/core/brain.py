import os
import json
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# 1. DAY 11, 12, 14, 15 & 16 IMPORTS: The Blueprints
# ==========================================
from .models import (
    WorldState, JuiceProfile, AppDNA, AppComponent, DesignTokens,
    ParametricGenome, VisualQuery, CameraAction, VFXProfile, BiomeDNA
)

# ==========================================
# 2. LOAD SECRETS FIRST 
# ==========================================
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")

supabase = None
if supabase_url and supabase_key:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Warning: Could not connect to Supabase. {e}")
else:
    print("Warning: Supabase URL/Key missing in .env. Memory won't work until fixed.")

client = None
if groq_api_key:
    client = Groq(api_key=groq_api_key)
else:
    print("Warning: Groq API key missing in .env. Generation won't work until fixed.")


# ==========================================
# 3. DAY 7: FETCHING THE MEMORY 
# ==========================================
def get_current_context():
    if not supabase:
        return "Supabase is not connected. Starting from scratch."

    try:
        response = supabase.table("projects").select("id, name, scene_data").order("created_at", desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            latest_project = response.data[0]
            project_name = latest_project.get("name", "Unnamed Project")
            scene_data = latest_project.get("scene_data", {})
            
            context_string = f"The user's current project is named '{project_name}'."
            
            if scene_data and isinstance(scene_data, dict):
                scene_info = scene_data.get("scene", {})
                scene_name = scene_info.get("name", "a generated scene")
                objects = scene_info.get("objects", [])
                
                context_string += f" It currently contains a scene named '{scene_name}' with {len(objects)} objects."
                
                if len(objects) > 0:
                    obj_names = [obj.get('name', 'Unknown') for obj in objects[:5]]
                    context_string += f" Some of the existing objects are: {', '.join(obj_names)}."
            else:
                context_string += " It has no detailed scene data yet."
                
            return context_string
        else:
            return "There is no existing project data in the vault yet. You are starting from scratch."
            
    except Exception as e:
        print(f"Error fetching memory from Supabase: {e}")
        return "Could not load project memory. Proceeding as if starting from scratch."


# ==========================================
# 4. DAY 8 & DAY 13: THE FRACTAL ENGINE GENERATION 
# ==========================================
def generate(user_prompt: str):
    if not client:
        print("Error: Groq client is not initialized.")
        return None

    print(f"Camera AI is thinking about: '{user_prompt}'...")
    project_memory = get_current_context()

    # --- DAY 11 & 13: FETCHING STATE & WORLD TRUTHS ---
    project_id = None
    if supabase:
        id_response = supabase.table("projects").select("id").order("created_at", desc=True).limit(1).execute()
        if id_response.data and len(id_response.data) > 0:
            project_id = id_response.data[0]["id"]

    current_state = get_world_state(project_id)
    state_context = f"CURRENT GAME STATE: The player's Heat/Wanted Level is {current_state.heat_level}/5. The current time of day is {current_state.time_of_day}."
    
    # DAY 13 STEP 3: INJECTING CONTEXT PRUNING (WORLD TRUTHS)
    raw_history_json = json.dumps(current_state.model_dump())
    world_truths = summarize_state(raw_history_json)
    
    truths_string = "\n".join([f"- {truth}" for truth in world_truths])

    system_prompt = f"""You are Camera AI, the Ontological Genesis Fabric. 
    You are a master at building massive, hierarchical 3D worlds using nested JSON.

    {state_context}

    CRITICAL WORLD TRUTHS (DO NOT CONTRADICT THESE):
    {truths_string}

    FRACTAL ENGINE RULES:
    1. Always structure your output as a hierarchy. Top-level items (like a City or World) must contain a "children" array.
    2. Child items (like Districts, Buildings, or Rooms) go inside that "children" array. Children can also have their own "children" arrays for infinite depth.
    3. Every single item must have a "name", "type", and "description".
    4. You MUST output strict, valid JSON. No markdown, no explanations, no code blocks.
    5. If updating an existing scene, preserve the existing hierarchy and attach new children to the correct parent.
    6. CRITICAL: Respect the CURRENT GAME STATE and WORLD TRUTHS. If Heat Level is high, generate chaotic elements. 

    Here is the current state of the user's project: 
    {project_memory}

    Based on this memory, the game state, the World Truths, and their new request, generate the hierarchical JSON.
    Do not output markdown or anything else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        raw_json = response.choices[0].message.content
        json.loads(raw_json) 
        
        print("Camera AI generated new Fractal JSON!")
        return raw_json

    except Exception as e:
        print(f"Error talking to Groq or parsing JSON: {e}")
        return None


# ==========================================
# 5. DAY 11: THE WORLD STATE MANAGER (Step 3 & Step 5)
# ==========================================
def get_world_state(project_id: str) -> WorldState:
    if not supabase or not project_id:
        return WorldState()

    try:
        response = supabase.table('projects').select('world_state').eq('id', project_id).execute()
        
        if response.data and len(response.data) > 0:
            json_data = response.data[0].get('world_state', {})
            return WorldState(**json_data)
            
    except Exception as e:
        print(f"Error fetching world state: {e}")
        
    return WorldState()


def update_world_state(project_id: str, changes_dict: dict):
    if not supabase or not project_id:
        print("Cannot update world state: No Supabase or Project ID.")
        return

    try:
        current_state = get_world_state(project_id)
        state_dict = current_state.model_dump()
        state_dict.update(changes_dict)

        response = supabase.table('projects').update({
            'world_state': state_dict
        }).eq('id', project_id).execute()

        print(f"World state updated for project {project_id}: {changes_dict}")
        return response

    except Exception as e:
        print(f"Error updating world state: {e}")

# ==========================================
# 6. DAY 12: NARRATIVE IMPACT (The Juice Translator)
# ==========================================
def generate_narrative_impact(juice: JuiceProfile, object_name: str = "the object") -> str:
    if not client:
        print("Error: Groq client is not initialized.")
        return "The object hits something."

    force = juice.impact_vector.force if juice.impact_vector else 0
    impact_type = juice.impact_type

    prompt = f"""
    You are a cinematic game director. Describe a physical impact in one exciting sentence.
    The object is: {object_name}.
    The type of impact is: {impact_type}.
    The raw force applied was: {force} units.
    
    Make it sound intense and juicy!
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a cinematic game narrative writer."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating narrative impact: {e}")
        return f"The {object_name} impacts with {impact_type} force."


# ==========================================
# 7. DAY 13: THE NARRATIVE SUMMARIZER (Context Pruning)
# ==========================================
def summarize_state(raw_history_json: str) -> list:
    if not client:
        print("Error: Groq client is not initialized.")
        return ["The world is in an unknown state."]

    prompt = f"""
    You are the Narrative Summarizer for an AI game. 
    Here is the raw JSON history of recent game events:
    {raw_history_json}

    Your task: Compress this history into exactly 3 permanent 'World Truths'. 
    Keep them short, factual, and crucial for the AI to remember so it doesn't contradict itself.
    
    You MUST return ONLY a JSON object with a key called "truths" that contains a list of 3 strings.
    Example format: {{ "truths": ["The king is dead.", "The player has the sword.", "It is raining."] }}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} 
        )
        
        content = json.loads(response.choices[0].message.content)
        return content.get("truths", ["The world is currently calm."])
    except Exception as e:
        print(f"Error summarizing state: {e}")
        return ["The world is in an unknown state."]


# ==========================================
# 8. DAY 14: FORCING THE UI BLUEPRINTS (The SaaS Killer)
# ==========================================
UI_SYSTEM_PROMPT = """
You are the Camera AI UI Architect. 
You DO NOT write React code, HTML, or CSS. You ONLY output structured JSON.
Your job is to select components from our Vault and define visual tokens.
Available Vault Components: 'NavBar', 'DataGrid'.
Motion options: 'fade-in-up', 'scale-in'.
"""

def get_ui_blueprint(user_request: str) -> dict:
    if not client:
        print("Error: Groq client is not initialized.")
        return None

    print(f"Camera AI is designing UI for: '{user_request}'...")
    
    prompt = f"""
    The user wants to build an app for: "{user_request}"
    
    Generate the AppDNA and DesignTokens. 
    Output ONLY valid JSON with this exact structure:
    {{
      "app_dna": {{
        "entity_name": "string (e.g., 'User Dashboard')",
        "required_components": [
          {{"component_name": "NavBar" or "DataGrid", "props": {{}}}}
        ]
      }},
      "design_tokens": {{
        "accent_primary": "string (Hex code like '#3B82F6')",
        "spacing_unit": integer (e.g., 4 or 8),
        "motion_entrance": "string ('fade-in-up' or 'scale-in')"
      }}
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": UI_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2 
        )
        
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        
        app_dna = AppDNA(**data.get("app_dna", {}))
        design_tokens = DesignTokens(**data.get("design_tokens", {}))
        
        print("Camera AI generated a flawless UI Blueprint!")
        return {"app_dna": app_dna, "design_tokens": design_tokens}
        
    except Exception as e:
        print(f"Brain Error (Using Failsafe): {e}")
        return {
            "app_dna": AppDNA(
                entity_name="Fallback Dashboard", 
                required_components=[
                    AppComponent(component_name="NavBar"), 
                    AppComponent(component_name="DataGrid")
                ]
            ),
            "design_tokens": DesignTokens(
                accent_primary="#3B82F6", 
                spacing_unit=8, 
                motion_entrance="fade-in-up"
            )
        }

# ==========================================
# 9. DAY 15: THE GENESIS DIRECTOR (BRAIN UPGRADE)
# ==========================================
def generate_genesis_scene(scene_prompt: str) -> dict:
    genome = ParametricGenome(
        seed=4096, 
        rules=["recursive_branch", "scale_down"], 
        scale_factor=1.5
    )
    
    visual_query = VisualQuery(
        search_terms=["cyberpunk", "neon", "building"], 
        fallback_flag=False,
        max_poly_count=10000
    )
    
    camera_action = CameraAction(
        movement_type="shaky_cam", 
        duration_seconds=5.0, 
        intensity=0.8
    )
    
    vfx_profile = VFXProfile(
        fog_density=0.6, 
        rain_intensity=0.3, 
        neon_reflection=0.9
    )
    
    return {
        "scene_prompt": scene_prompt,
        "parametric_genome": genome.model_dump(),
        "visual_query": visual_query.model_dump(),
        "camera_action": camera_action.model_dump(),
        "vfx_profile": vfx_profile.model_dump()
    }

# ==========================================
# 10. DAY 16: THE ECOSYSTEM DIRECTOR (Biome Math)
# ==========================================
def act_as_ecosystem_director(user_prompt: str, world_state: dict) -> BiomeDNA:
    """
    Upgrades the Brain to design cohesive, mathematical ecosystems.
    Forces Groq to output strict BiomeDNA JSON using an exact template.
    """
    if not client:
        print("Error: Groq client is not initialized.")
        return BiomeDNA(
            name="Fallback Plains", elevation_curve=0.5, moisture_level=0.5, 
            scatter_density=0.5, scatter_rules=[]
        )

    print(f"Camera AI is designing an ecosystem for: '{user_prompt}'...")
    
    system_prompt = """
    You are the Ecosystem Director for a deterministic 3D game engine. 
    You DO NOT place objects randomly. You define environmental math and ScatterRules.
    You must output ONLY valid JSON. No markdown, no explanations.
    """
    
    # CRITICAL FIX: We give the AI the exact JSON skeleton to fill out.
    # This prevents it from hallucinating wrong key names like "biome_name" or using dictionaries instead of lists.
    user_message = f"""
    Current World State: {world_state}
    User Request: {user_prompt}
    
    Design the BiomeDNA. You MUST use this EXACT JSON structure and key names:
    {{
      "name": "Mystic Rainforest",
      "elevation_curve": 0.4,
      "moisture_level": 0.9,
      "scatter_density": 0.8,
      "scatter_rules": [
        {{
          "asset_type": "parametric_pine_tree",
          "noise_threshold": 0.6,
          "density_multiplier": 1.2
        }},
        {{
          "asset_type": "ruined_shrine",
          "noise_threshold": 0.2,
          "density_multiplier": 0.5
        }}
      ]
    }}
    Change the values and asset types to match the User Request, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7 
        )
        
        raw_json = response.choices[0].message.content
        
        # The Pydantic Bouncer catches any bad data here
        biome_dna = BiomeDNA.model_validate_json(raw_json)
        print("Camera AI generated a flawless Biome Blueprint!")
        return biome_dna
        
    except Exception as e:
        print(f"Brain Error (Using Failsafe): {e}")
        return BiomeDNA(
            name="Error Plains", elevation_curve=0.5, moisture_level=0.5, 
            scatter_density=0.5, scatter_rules=[]
        )