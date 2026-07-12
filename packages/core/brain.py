import os
import json
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# 1. DAY 11 NEW IMPORT: The Blueprint
# ==========================================
from .models import WorldState

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
# 4. DAY 8: THE FRACTAL ENGINE GENERATION (WITH STEP 4 UPGRADE)
# ==========================================
def generate(user_prompt: str):
    if not client:
        print("Error: Groq client is not initialized.")
        return None

    print(f"Camera AI is thinking about: '{user_prompt}'...")
    project_memory = get_current_context()

    # --- DAY 11 STEP 4: INJECTING THE WORLD STATE ---
    project_id = None
    if supabase:
        id_response = supabase.table("projects").select("id").order("created_at", desc=True).limit(1).execute()
        if id_response.data and len(id_response.data) > 0:
            project_id = id_response.data[0]["id"]

    current_state = get_world_state(project_id)
    state_context = f"CURRENT GAME STATE: The player's Heat/Wanted Level is {current_state.heat_level}/5. The current time of day is {current_state.time_of_day}."
    # ------------------------------------------------

    system_prompt = f"""You are Camera AI, the Ontological Genesis Fabric. 
    You are a master at building massive, hierarchical 3D worlds using nested JSON.

    {state_context}

    FRACTAL ENGINE RULES:
    1. Always structure your output as a hierarchy. Top-level items (like a City or World) must contain a "children" array.
    2. Child items (like Districts, Buildings, or Rooms) go inside that "children" array. Children can also have their own "children" arrays for infinite depth.
    3. Every single item must have a "name", "type", and "description".
    4. You MUST output strict, valid JSON. No markdown, no explanations, no code blocks.
    5. If updating an existing scene, preserve the existing hierarchy and attach new children to the correct parent.
    6. CRITICAL: Respect the CURRENT GAME STATE. If Heat Level is high, generate chaotic or dangerous elements. If it is 0, generate peaceful elements.

    Here is the current state of the user's project: 
    {project_memory}

    Based on this memory, the game state, and their new request, generate the hierarchical JSON.
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
        # 1. Read the current state using our Librarian
        current_state = get_world_state(project_id)

        # 2. Convert our Pydantic blueprint back into a normal Python dictionary
        # (model_dump is Pydantic's way of turning the blueprint back into raw JSON data)
        state_dict = current_state.model_dump()

        # 3. Merge the new changes into our dictionary
        # (e.g., updating heat_level from 0 to 3)
        state_dict.update(changes_dict)

        # 4. Save it back to Supabase!
        response = supabase.table('projects').update({
            'world_state': state_dict
        }).eq('id', project_id).execute()

        print(f"World state updated for project {project_id}: {changes_dict}")
        return response

    except Exception as e:
        print(f"Error updating world state: {e}")