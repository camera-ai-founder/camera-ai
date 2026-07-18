# packages/core/brain.py
import os
import json
from typing import List
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# 1. DAY 11, 12, 14, 15, 16, 17, 18, 20, 21, 24, 25, 26, 27 & 28 IMPORTS: The Blueprints
# ==========================================
from .models import (
    WorldState, JuiceProfile, AppDNA, AppComponent, DesignTokens,
    ParametricGenome, VisualQuery, CameraAction, VFXProfile, BiomeDNA,
    PathingIntent, LogicDNA, Route, DeployDNA, StateDelta, SecurityDNA,
    AudioDNA, # ADDED FOR DAY 24
    InputDNA, # ADDED FOR DAY 25
    ModDNA, # ADDED FOR DAY 26
    ModMetadata, # ADDED FOR DAY 26
    SemanticToken, # ADDED FOR DAY 27
    LocaleDNA, # ADDED FOR DAY 27
    EconomyDNA, # ADDED FOR DAY 28
    EconomicEvent # ADDED FOR DAY 28
)

# ==========================================
# DAY 22 STEP 5: THE SECURITY GUARDRAILS
# ==========================================
SECURITY_GUARDRAILS_PROMPT = """
=== CRITICAL SECURITY DNA RULES ===
You are operating within a Zero-Trust architecture. You MUST strictly obey these mathematical limits when generating JSON DNA:
1. STRING LIMITS: Never generate a string longer than 2,000 characters. Keep descriptions concise.
2. PAYLOAD SIZE: The total JSON output must be under 1MB. Do not generate massive arrays or redundant data.
3. FORBIDDEN CHARACTERS: NEVER use these characters in any string values: <, >, ;, --, /*, */. Use plain text only.
4. STRICT SCHEMA: Only output the exact keys defined in the Pydantic models. Do not invent new keys or hallucinate extra fields.
5. NUMERICAL BOUNDS: Respect all 'ge' (greater than or equal to) and 'le' (less than or equal to) limits. Tension must be 0-100, etc.
If you violate these rules, the Sanitizer will block your output. Generate clean, safe, and perfectly bounded JSON.
"""

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
    Do not output markdown or anything else.

    {SECURITY_GUARDRAILS_PROMPT}
    """

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
    
    {SECURITY_GUARDRAILS_PROMPT}
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

    {SECURITY_GUARDRAILS_PROMPT}
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
UI_SYSTEM_PROMPT = f"""
You are the Camera AI UI Architect. 
You DO NOT write React code, HTML, or CSS. You ONLY output structured JSON.
Your job is to select components from our Vault and define visual tokens.
Available Vault Components: 'NavBar', 'DataGrid'.
Motion options: 'fade-in-up', 'scale-in'.

{SECURITY_GUARDRAILS_PROMPT}
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
    if not client:
        print("Error: Groq client is not initialized.")
        return BiomeDNA(
            name="Fallback Plains", elevation_curve=0.5, moisture_level=0.5, 
            scatter_density=0.5, scatter_rules=[]
        )

    print(f"Camera AI is designing an ecosystem for: '{user_prompt}'...")
    
    system_prompt = f"""
    You are the Ecosystem Director for a deterministic 3D game engine. 
    You DO NOT place objects randomly. You define environmental math and ScatterRules.
    You must output ONLY valid JSON. No markdown, no explanations.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
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
        
        biome_dna = BiomeDNA.model_validate_json(raw_json)
        print("Camera AI generated a flawless Biome Blueprint!")
        return biome_dna
        
    except Exception as e:
        print(f"Brain Error (Using Failsafe): {e}")
        return BiomeDNA(
            name="Error Plains", elevation_curve=0.5, moisture_level=0.5, 
            scatter_density=0.5, scatter_rules=[]
        )

# ==========================================
# 11. DAY 17: THE TRAFFIC DIRECTOR (Navigation Intent)
# ==========================================
def decide_navigation_intent(entity_id: str, start_coords: tuple, context: str) -> PathingIntent:
    if not client:
        print("Error: Groq client is not initialized.")
        return PathingIntent(
            entity_id=entity_id,
            start_coords=start_coords,
            target_coords=start_coords
        )

    print(f"Traffic Director is routing Entity '{entity_id}'...")

    system_prompt = f"""
    You are the Traffic Director for a deterministic 3D game engine.
    Your ONLY job is to decide the destination coordinates (x, z) for an entity based on the narrative context.
    You DO NOT write movement code. You DO NOT calculate physics. 
    You MUST output ONLY valid JSON matching the PathingIntent schema.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_message = f"""
    Entity ID: {entity_id}
    Current Position (x, z): {start_coords}
    Narrative Context: {context}
    
    Pick a logical destination (x, z) within the world bounds (-50.0 to 50.0).
    You MUST use this EXACT JSON structure:
    {{
      "entity_id": "{entity_id}",
      "start_coords": [{start_coords[0]}, {start_coords[1]}],
      "target_coords": [10.5, -20.0] 
    }}
    Change the "target_coords" to fit the narrative context, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.4 
        )
        
        raw_json = response.choices[0].message.content
        
        intent = PathingIntent.model_validate_json(raw_json)
        print(f"Traffic Director issued Pathing Intent to {intent.target_coords}!")
        return intent
        
    except Exception as e:
        print(f"Brain Error (Traffic Director Failsafe): {e}")
        return PathingIntent(
            entity_id=entity_id,
            start_coords=start_coords,
            target_coords=start_coords
        )

# ==========================================
# 12. DAY 18: THE BACKEND ARCHITECT DIRECTOR (FIXED TEMPLATE)
# ==========================================
def act_as_backend_architect(entity_prompt: str) -> LogicDNA:
    if not client:
        print("Error: Groq client is not initialized.")
        return LogicDNA(
            entity_name="Fallback",
            routes=[Route(method="GET", path="/fallback")],
            auth_type="None",
            database_schema="Fallback schema"
        )

    print(f"Backend Architect is designing architecture for: '{entity_prompt}'...")
    
    system_prompt = f"""
    You are the OGF Backend Architect. Your ONLY job is to design the architecture 
    for a backend API by filling out a strict JSON form.
    You MUST NOT write any Python code. You MUST NOT write any markdown.
    You MUST output ONLY valid JSON.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_prompt = f"""
    Design the backend architecture for this entity: {entity_prompt}
    
    You MUST use this EXACT JSON structure and key names:
    {{
      "entity_name": "User",
      "routes": [
        {{"method": "GET", "path": "/users"}},
        {{"method": "POST", "path": "/users"}}
      ],
      "auth_type": "JWT",
      "database_schema": "A table for users with id, name, and email."
    }}
    
    Allowed HTTP methods for "method": "GET", "POST", "PUT", "DELETE", "PATCH"
    Allowed auth types for "auth_type": "JWT", "OAuth", "API_Key", "Public", "None"
    
    Change the values to match the requested entity, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.1
        )
        
        raw_json = response.choices[0].message.content
        
        dna = LogicDNA.model_validate_json(raw_json)
        print("Backend Architect generated a flawless LogicDNA!")
        return dna
        
    except Exception as e:
        print(f"[ERROR] The Architect Brain failed to fill out the form: {e}")
        return LogicDNA(
            entity_name="Fallback",
            routes=[Route(method="GET", path="/fallback")],
            auth_type="None",
            database_schema="Fallback schema"
        )

# ==========================================
# 13. DAY 20: THE DEVOPS DIRECTOR (Deployment Topology)
# ==========================================
def generate_deployment_topology(world_state: WorldState, app_complexity: str = "lightweight") -> DeployDNA:
    if not client:
        print("Error: Groq client is not initialized.")
        return DeployDNA(
            target_environment="docker",
            port_mappings={8080: 80},
            env_variables={},
            asset_cdn_url=None
        )

    print("DevOps Director is determining deployment topology...")
    
    system_prompt = f"""
    You are the DevOps Director for the Ontological Genesis Framework.
    Your job is to determine the exact deployment topology based on the 
    current World State and application complexity.
    You MUST output strictly valid JSON matching the DeployDNA schema.
    Do not write bash scripts. Do not write Dockerfiles. Only output the JSON topology.
    
    Example target environments: 'docker', 'render', 'railway'.
    Remember to include necessary env variables like SUPABASE_URL if it's a web app.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_prompt = f"""
    Current World State Heat Level: {world_state.heat_level}
    Current Time of Day: {world_state.time_of_day}
    Application Complexity Level: {app_complexity}
    
    Determine the target environment, required port mappings, 
    and necessary environment variables for deployment.
    
    You MUST use this EXACT JSON structure and key names:
    {{
      "target_environment": "docker",
      "port_mappings": {{"8080": 80}},
      "env_variables": {{"SUPABASE_URL": "https://xyz.supabase.co"}},
      "asset_cdn_url": null
    }}
    Change the values to fit the context, but KEEP THE EXACT KEY NAMES AND TYPES.
    """
    
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
        
        deploy_dna = DeployDNA.model_validate_json(raw_json)
        print("DevOps Director generated flawless DeployDNA!")
        return deploy_dna
        
    except Exception as e:
        print(f"Brain Error (DevOps Director Failsafe): {e}")
        return DeployDNA(
            target_environment="docker",
            port_mappings={8080: 80},
            env_variables={},
            asset_cdn_url=None
        )

# ==========================================
# 14. DAY 21: THE MULTIPLAYER DIRECTOR (BRAIN UPGRADE)
# ==========================================
def generate_multiplayer_intent(action_description: str, current_world_state: dict) -> StateDelta:
    if not client:
        print("Error: Groq client is not initialized.")
        return StateDelta()

    print(f"Multiplayer Director is analyzing intent for: '{action_description}'...")
    
    delta_schema = StateDelta.model_json_schema()
    
    system_prompt = f"""
    You are the Multiplayer Director for a deterministic game engine.
    Your job is to calculate the exact mathematical difference (the StateDelta) that needs to be broadcast to all other players.
    Do NOT write any code. Do NOT explain your reasoning. 
    You MUST output ONLY valid JSON that strictly matches the provided schema.
    If a node was changed or added, put it in 'changed_nodes'.
    If a node was destroyed, put its ID in 'removed_node_ids'.
    If a global variable changed (like time of day or heat level), put it in 'changed_tokens'.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_prompt = f"""
    The current world state is: {json.dumps(current_world_state, indent=2)}
    
    A player just performed this action: "{action_description}"
    
    Calculate the StateDelta. You MUST use this EXACT JSON structure:
    {json.dumps(delta_schema, indent=2)}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_json_string = response.choices[0].message.content
        raw_dict = json.loads(raw_json_string)
        
        validated_delta = StateDelta(**raw_dict)
        print("Multiplayer Director generated a flawless StateDelta!")
        return validated_delta
        
    except Exception as e:
        print(f"Brain Error (Multiplayer Director Failsafe): {e}")
        return StateDelta()

# ==========================================
# 15. DAY 24: THE FOLEY DIRECTOR (Procedural Audio)
# ==========================================
def act_as_foley_director(entity_description: str) -> AudioDNA:
    if not client:
        print("Error: Groq client is not initialized.")
        return AudioDNA()

    print(f"Foley Director is designing the soundscape for: '{entity_description}'...")
    
    system_prompt = f"""
    You are the Foley Director and Master Sound Designer for a deterministic 3D game engine.
    You DO NOT use audio files (.mp3, .wav). You ONLY design mathematical sound waves using AudioDNA.
    You MUST output ONLY valid JSON. No markdown, no explanations.

    Allowed waveform_type: "sine", "square", "sawtooth", "triangle", "noise"
    Allowed filter_type: "lowpass", "highpass", "bandpass", "none"

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_message = f"""
    Entity Description: {entity_description}
    
    Design the AudioDNA for this entity. Think about what sound it makes in real life.
    - A neon sign might be a low "sine" wave hum.
    - A steam vent might be "noise" with a fast attack.
    - A heavy metal door might be a low "triangle" wave impact.
    
    You MUST use this EXACT JSON structure and key names:
    {{
      "waveform_type": "sine",
      "base_frequency": 60.0,
      "envelope_attack": 0.5,
      "envelope_decay": 2.0,
      "filter_type": "lowpass"
    }}
    Change the values to perfectly match the acoustic nature of the entity, but KEEP THE EXACT KEY NAMES AND TYPES.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        
        raw_json = response.choices[0].message.content
        
        audio_dna = AudioDNA.model_validate_json(raw_json)
        print("Foley Director generated flawless AudioDNA!")
        return audio_dna
        
    except Exception as e:
        print(f"Brain Error (Foley Director Failsafe): {e}")
        return AudioDNA()

# ==========================================
# 16. DAY 25: THE CONTROL DIRECTOR (Input Wiring)
# ==========================================
def act_as_control_director(mechanic_description: str) -> List[InputDNA]:
    if not client:
        print("Error: Groq client is not initialized.")
        return []

    print(f"Control Director is wiring inputs for: '{mechanic_description}'...")
    
    system_prompt = f"""
    You are the Control Director for a deterministic 3D game engine.
    Your job is to invent the input controls for new game mechanics, vehicles, or items.
    You MUST output ONLY valid JSON. No markdown, no explanations.
    
    Allowed active_context values: "gameplay", "ui", "cinematic"
    Allowed hardware_trigger examples: "Spacebar", "KeyW", "ShiftLeft", "Mouse_Left", "Gamepad_A"

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_message = f"""
    Mechanic Description: {mechanic_description}
    
    Design the input controls for this mechanic. 
    You MUST output an exact JSON object with a key called "inputs" containing a list of InputDNA objects.
    
    You MUST use this EXACT JSON structure:
    {{
      "inputs": [
        {{
          "action_name": "thrust_up",
          "hardware_trigger": "Spacebar",
          "modifier_key": null,
          "active_context": "gameplay"
        }},
        {{
          "action_name": "hover",
          "hardware_trigger": "ShiftLeft",
          "modifier_key": null,
          "active_context": "gameplay"
        }}
      ]
    }}
    Change the action names and hardware triggers to perfectly fit the mechanic, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.4 
        )
        
        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        
        inputs_list = parsed_data.get("inputs", [])
        validated_inputs = [InputDNA(**item) for item in inputs_list]
        
        print(f"Control Director wired {len(validated_inputs)} inputs flawlessly!")
        return validated_inputs
        
    except Exception as e:
        print(f"Brain Error (Control Director Failsafe): {e}")
        return []

# ==========================================
# 17. DAY 26: THE MOD CURATOR (AI Librarian)
# ==========================================
class ModCurator:
    def generate_tags(self, mod: ModDNA) -> ModMetadata:
        if not client:
            print("Error: Groq client is not initialized.")
            return mod.metadata

        print(f"Curator is analyzing mod: {mod.mod_name}")
        
        mod_summary = {
            "mod_name": mod.mod_name,
            "nodes_count": len(mod.injected_nodes),
            "sample_tags": [n.get("semantic_tags", []) for n in mod.injected_nodes[:3]]
        }

        prompt = f"""
        You are the Master Mod Curator for a game engine. 
        Analyze this mod's data: {json.dumps(mod_summary)}
        
        Generate 3 to 5 highly relevant, consistent semantic tags for this mod 
        (e.g., 'cyberpunk', 'cozy', 'high_tension', 'new_biome', 'vehicle').
        
        CRITICAL RULE: You MUST return ONLY a valid JSON object with a key "tags" containing a list of strings. 
        Example: {{"tags": ["cyberpunk", "vehicle", "neon"]}}
        
        {SECURITY_GUARDRAILS_PROMPT}
        """

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", 
                temperature=0.2,
                max_tokens=50,
                response_format={"type": "json_object"}
            )
            
            raw_response = chat_completion.choices[0].message.content
            parsed = json.loads(raw_response)
            
            tags_list = parsed.get("tags", [])
            if not isinstance(tags_list, list):
                tags_list = []
                
            print(f"Curator generated tags: {tags_list}")
            
            new_metadata_dict = mod.metadata.model_dump()
            existing_tags = set(new_metadata_dict.get("tags", []))
            for tag in tags_list:
                if isinstance(tag, str) and tag not in existing_tags:
                    new_metadata_dict["tags"].append(tag)
                    
            return ModMetadata(**new_metadata_dict)

        except Exception as e:
            print(f"Curator failed to generate tags for {mod.mod_name}: {e}")
            return mod.metadata


# ==========================================
# 18. DAY 27: THE TRANSLATION DIRECTOR (Semantic Dialogue)
# ==========================================
def act_as_translation_director(narrative_context: str, locale: LocaleDNA) -> List[SemanticToken]:
    """
    DAY 27: THE TRANSLATION DIRECTOR.
    Forces the AI to act as a Universal Concept Generator.
    It is STRICTLY FORBIDDEN from outputting raw human text (English, German, etc.).
    It MUST output only SemanticTokens (concept_ids) so the Localization Engine 
    can map them perfectly to any language in the Supabase Dictionary.
    """
    if not client:
        print("Error: Groq client is not initialized.")
        return [] # Safe empty list

    print(f"Translation Director is extracting concepts for: '{narrative_context}'...")
    
    system_prompt = f"""
    You are the Translation Director for the Ontological Genesis Framework.
    Your absolute rule: You are COMPLETELY FORBIDDEN from writing human words, sentences, or raw text.
    You DO NOT output English, German, Spanish, or any human language.
    
    You ONLY output Universal Concepts using SemanticTokens (concept_ids).
    
    If the narrative requires the UI to say "Start Game", you DO NOT output "Start Game". 
    You output the concept_id: "ui_button_start".
    If an NPC needs to say "Halt! Who goes there?", you output the concept_id: "greeting_hostile".
    
    You MUST output ONLY valid JSON. No markdown, no explanations.
    
    Allowed intensity: 0.0 to 1.0
    
    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_message = f"""
    Narrative Context: {narrative_context}
    Target Locale (for your awareness, but DO NOT write in this language): {locale.target_language}
    
    Extract the core concepts needed for this scene and output them as SemanticTokens.
    
    You MUST use this EXACT JSON structure:
    {{
      "tokens": [
        {{
          "concept_id": "greeting_hostile",
          "intensity": 0.8,
          "context_vars": {{"player_name": "Sarah"}}
        }},
        {{
          "concept_id": "combat_warn_fire",
          "intensity": 1.0,
          "context_vars": {{}}
        }}
      ]
    }}
    Change the concept_ids to match the narrative context, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.3 # Keep it strict and conceptual
        )
        
        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        
        # Extract the list and force it through our Pydantic Bouncer
        tokens_list = parsed_data.get("tokens", [])
        validated_tokens = [SemanticToken(**item) for item in tokens_list]
        
        print(f"Translation Director extracted {len(validated_tokens)} pure concepts. Zero raw text leaked!")
        return validated_tokens
        
    except Exception as e:
        print(f"Brain Error (Translation Director Failsafe): {e}")
        return [] # Returns an empty list so the engine doesn't crash


# ==========================================
# 19. DAY 28: THE ECONOMY DIRECTOR (Math Balancing)
# ==========================================
def act_as_economy_director(entity_description: str) -> EconomyDNA:
    """
    DAY 28: THE ECONOMY DIRECTOR.
    Forces the AI to act as an Economic Flow Designer.
    It is STRICTLY FORBIDDEN from guessing raw prices or loot amounts (e.g., "500 gold").
    It MUST output the mathematical flow tags (EconomyDNA) so the Engine can 
    deterministically calculate the exact balanced numbers.
    """
    if not client:
        print("Error: Groq client is not initialized.")
        return EconomyDNA(
            resource_name="Gold",
            faucet_type="active_quest",
            sink_type="vendor_purchase",
            target_velocity=2.0,
            inflation_cap=100.0
        )

    print(f"Economy Director is balancing the flow for: '{entity_description}'...")
    
    system_prompt = f"""
    You are the Economy Director for a deterministic 3D game engine.
    You DO NOT output raw prices, loot amounts, or hardcoded numbers like '500 gold'.
    You ONLY define the MATHEMATICAL FLOW (the EconomyDNA) of a resource.
    
    Faucet Types (How it enters): "active_quest", "passive_income", "loot_drop"
    Sink Types (How it leaves): "vendor_purchase", "crafting_cost", "tax"
    
    target_velocity: Expected transactions per hour (e.g., 2.0 to 10.0)
    inflation_cap: Maximum allowed accumulation rate per hour to prevent exploits (e.g., 50.0 to 500.0)
    
    You MUST output ONLY valid JSON. No markdown, no explanations.

    {SECURITY_GUARDRAILS_PROMPT}
    """
    
    user_message = f"""
    Entity Description: {entity_description}
    
    Design the EconomyDNA for this entity. 
    Think about how this entity interacts with the economy.
    - A blacksmith is a "vendor_purchase" sink.
    - A daily login reward is a "passive_income" faucet.
    
    You MUST use this EXACT JSON structure and key names:
    {{
      "resource_name": "Gold",
      "faucet_type": "active_quest",
      "sink_type": "vendor_purchase",
      "target_velocity": 5.0,
      "inflation_cap": 100.0
    }}
    Change the values to perfectly balance the flow for the entity, but KEEP THE EXACT KEY NAMES AND TYPES.
    REMEMBER: Do NOT output raw item prices. Only output the flow rates!
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.2 # Keep it strict and mathematical
        )
        
        raw_json = response.choices[0].message.content
        
        economy_dna = EconomyDNA.model_validate_json(raw_json)
        print("Economy Director generated flawless EconomyDNA! Zero raw numbers leaked.")
        return economy_dna
        
    except Exception as e:
        print(f"Brain Error (Economy Director Failsafe): {e}")
        return EconomyDNA(
            resource_name="Gold",
            faucet_type="active_quest",
            sink_type="vendor_purchase",
            target_velocity=2.0,
            inflation_cap=100.0
        )