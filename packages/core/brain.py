import os
import json
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# 1. DAY 11, 12 & 14 NEW IMPORTS: The Blueprints
# ==========================================
# Added AppDNA, AppComponent, and DesignTokens for Day 14
from .models import WorldState, JuiceProfile, AppDNA, AppComponent, DesignTokens

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
    """
    The Librarian: Goes to Supabase, grabs the JSONB memory folder, 
    and returns it as our WorldState Pydantic blueprint.
    """
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
    """
    The Writer (DAY 11 STEP 5): Takes new game events, merges them 
    into our World State, and saves the folder back to Supabase.
    """
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
    """
    Asks the Groq AI to turn our math (JuiceProfile) into a cool story description!
    """
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
    """
    TIER 2 BRAIN: Context Pruning.
    Compresses massive game history into 3 simple 'World Truths' so the AI never forgets.
    """
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
# We use a strict System Prompt to remind the AI it is ONLY allowed to output JSON.
UI_SYSTEM_PROMPT = """
You are the Camera AI UI Architect. 
You DO NOT write React code, HTML, or CSS. You ONLY output structured JSON.
Your job is to select components from our Vault and define visual tokens.
Available Vault Components: 'NavBar', 'DataGrid'.
Motion options: 'fade-in-up', 'scale-in'.
"""

def get_ui_blueprint(user_request: str) -> dict:
    """
    DAY 14: Asks the Groq Brain for AppDNA and DesignTokens.
    By forcing JSON mode, we mathematically prevent the AI from hallucinating code.
    """
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
        # We use a fast, lightweight model for simple JSON generation
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
        
        # THE CRITICAL SAFETY NET: Pydantic validation
        app_dna = AppDNA(**data.get("app_dna", {}))
        design_tokens = DesignTokens(**data.get("design_tokens", {}))
        
        print("Camera AI generated a flawless UI Blueprint!")
        return {"app_dna": app_dna, "design_tokens": design_tokens}
        
    except Exception as e:
        print(f"Brain Error (Using Failsafe): {e}")
        # Failsafe defaults so the app NEVER crashes
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