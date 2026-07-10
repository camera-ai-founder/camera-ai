import os
import json
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# 1. LOAD SECRETS FIRST
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
# 2. DAY 7: FETCHING THE MEMORY (UPDATED!)
# ==========================================
def get_current_context():
    if not supabase:
        return "Supabase is not connected. Starting from scratch."

    try:
        # We now select 'scene_data' instead of 'nodes'
        response = supabase.table("projects").select("id, name, scene_data").order("created_at", desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            latest_project = response.data[0]
            project_name = latest_project.get("name", "Unnamed Project")
            scene_data = latest_project.get("scene_data", {})
            
            context_string = f"The user's current project is named '{project_name}'."
            
            # Summarize the awesome 3D scene Groq built!
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
# 3. DAY 7: INJECTING CONTEXT & GENERATING
# ==========================================
def generate(user_prompt: str):
    if not client:
        print("Error: Groq client is not initialized.")
        return None

    print(f"Camera AI is thinking about: '{user_prompt}'...")
    project_memory = get_current_context()

    # We loosen the prompt slightly so Groq can generate its awesome 3D scenes freely!
    system_prompt = f"""You are Camera AI, the Ontological Genesis Fabric. 
    You are a master at building 3D scenes and game logic.

    Here is the current state of the user's project: 
    {project_memory}

    Based on this memory and their new request below, fulfill their request. 
    You MUST output strict JSON. If adding to an existing scene, include the existing objects and add the new ones.
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
        
        print("Camera AI generated new JSON!")
        return raw_json

    except Exception as e:
        print(f"Error talking to Groq or parsing JSON: {e}")
        return None