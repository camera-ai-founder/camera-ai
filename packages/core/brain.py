# packages/core/brain.py

import os
import json
import uuid
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

# ==========================================
# DAY 11 to DAY 34 IMPORTS: The Blueprints
# ==========================================
from .models import (
    WorldState,
    JuiceProfile,
    AppDNA,
    AppComponent,
    DesignTokens,
    ParametricGenome,
    VisualQuery,
    CameraAction,
    VFXProfile,
    BiomeDNA,
    PathingIntent,
    LogicDNA,
    Route,
    DeployDNA,
    StateDelta,
    SecurityDNA,
    AudioDNA,
    InputDNA,
    ModDNA,
    ModMetadata,
    SemanticToken,
    LocaleDNA,
    EconomyDNA,
    EconomicEvent,
    TutorialDNA,
    MasteryEvent,
    ChronoDNA,
    RewindIntent,
    AccessibilityDNA,
    AdaptationEvent,
    TelemetryDNA,
    PerformanceReport,
    QuestDNA,
    SocialDNA,
    FactionDNA,
    RelationshipTensor,
    SocialRule,
    SocialAction,
    FlowDNA,
    PacingDirective
)

# ==========================================
# DAY 31 OPTIONAL IMPORT:
# The Cognitive Load Evaluator helps the Empathy Director.
# ==========================================
try:
    from .accessibility_engine import default_accessibility_engine
except ImportError:
    try:
        from packages.core.accessibility_engine import default_accessibility_engine
    except ImportError:
        default_accessibility_engine = None

# ==========================================
# DAY 32 IMPORT:
# The Narrative Engine validates QuestDNA as a DAG.
# ==========================================
try:
    from .narrative_engine import NarrativeEngine
except ImportError:
    try:
        from packages.core.narrative_engine import NarrativeEngine
    except ImportError:
        NarrativeEngine = None

# ==========================================
# DAY 33 IMPORT:
# The Social Engine validates SocialDNA as a living matrix.
# ==========================================
try:
    from .social_engine import SocialMatrixEngine
except ImportError:
    try:
        from packages.core.social_engine import SocialMatrixEngine
    except ImportError:
        SocialMatrixEngine = None

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
# LOAD SECRETS FIRST 
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
# SHARED PROJECT MEMORY HELPERS
# ==========================================
def get_latest_project_id() -> Optional[str]:
    """
    Safely fetch the most recent project ID from Supabase.
    """
    if not supabase:
        return None

    try:
        response = (
            supabase.table("projects")
            .select("id")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0].get("id")

    except Exception as e:
        print(f"Error fetching latest project ID: {e}")

    return None


# ==========================================
# DAY 7: FETCHING THE MEMORY 
# ==========================================
def get_current_context():
    if not supabase:
        return "Supabase is not connected. Starting from scratch."

    try:
        response = (
            supabase.table("projects")
            .select("id, name, scene_data")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

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
                    obj_names = [obj.get("name", "Unknown") for obj in objects[:5]]
                    context_string += f" Some of the existing objects are: {', '.join(obj_names)}."
            else:
                context_string += " It has no detailed scene data yet."

            return context_string

        return "There is no existing project data in the vault yet. You are starting from scratch."

    except Exception as e:
        print(f"Error fetching memory from Supabase: {e}")
        return "Could not load project memory. Proceeding as if starting from scratch."


# ==========================================
# DAY 8 & DAY 13: THE FRACTAL ENGINE GENERATION 
# ==========================================
def generate(user_prompt: str):
    if not client:
        print("Error: Groq client is not initialized.")
        return None

    print(f"Camera AI is thinking about: '{user_prompt}'...")
    project_memory = get_current_context()

    project_id = get_latest_project_id()
    current_state = get_world_state(project_id)

    state_context = (
        f"CURRENT GAME STATE: The player's Heat/Wanted Level is "
        f"{current_state.heat_level}/5. The current time of day is "
        f"{current_state.time_of_day}."
    )

    raw_history_json = json.dumps(current_state.model_dump(), default=str)
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
# DAY 11: THE WORLD STATE MANAGER
# ==========================================
def get_world_state(project_id: Optional[str] = None) -> WorldState:
    if project_id is None:
        project_id = get_latest_project_id()

    if not supabase or not project_id:
        return WorldState()

    try:
        response = (
            supabase.table("projects")
            .select("world_state")
            .eq("id", project_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            json_data = response.data[0].get("world_state", {})
            return WorldState(**json_data)

    except Exception as e:
        print(f"Error fetching world state: {e}")

    return WorldState()


def _resolve_world_state_value(current_value: Any, mutation_value: Any) -> Any:
    """
    Deterministic mutation resolver for Day 11 World State.
    """
    if not isinstance(mutation_value, dict):
        return mutation_value

    if "$set" in mutation_value:
        return mutation_value["$set"]

    if "$add" in mutation_value:
        try:
            base = 0 if current_value is None else current_value
            return base + mutation_value["$add"]
        except Exception:
            return mutation_value["$add"]

    if "$sub" in mutation_value:
        try:
            base = 0 if current_value is None else current_value
            return base - mutation_value["$sub"]
        except Exception:
            return mutation_value["$sub"]

    if "$multiply" in mutation_value:
        try:
            base = 0 if current_value is None else current_value
            return base * mutation_value["$multiply"]
        except Exception:
            return mutation_value["$multiply"]

    return mutation_value


def update_world_state(
    project_id_or_world_state: Any = None,
    changes_dict: Optional[dict] = None,
    *,
    project_id: Optional[str] = None,
    world_state: Any = None,
    mutations: Optional[dict] = None
) -> Any:
    """
    Day 11 World State updater.
    """
    resolved_project_id = project_id
    resolved_changes = mutations if mutations is not None else changes_dict

    if resolved_changes is None:
        resolved_changes = {}

    if isinstance(project_id_or_world_state, str):
        resolved_project_id = project_id_or_world_state
    elif project_id_or_world_state is not None:
        world_state = project_id_or_world_state

    if resolved_project_id is None:
        resolved_project_id = get_latest_project_id()

    if world_state is None:
        base_state = get_world_state(resolved_project_id)
    else:
        base_state = world_state

    if hasattr(base_state, "model_dump"):
        state_dict = base_state.model_dump()
    elif isinstance(base_state, dict):
        state_dict = dict(base_state)
    else:
        state_dict = WorldState().model_dump()

    if isinstance(resolved_changes, dict):
        payload = resolved_changes

        if "world_state" in payload and isinstance(payload["world_state"], dict):
            payload = payload["world_state"]
        elif "set" in payload and isinstance(payload["set"], dict):
            payload = payload["set"]

        for key, value in payload.items():
            state_dict[key] = _resolve_world_state_value(
                current_value=state_dict.get(key),
                mutation_value=value
            )

    if supabase and resolved_project_id:
        try:
            supabase.table("projects").update(
                {"world_state": state_dict}
            ).eq("id", resolved_project_id).execute()

            print(f"World state updated for project {resolved_project_id}: {resolved_changes}")

        except Exception as e:
            print(f"Error updating world state: {e}")

    try:
        return WorldState(**state_dict)
    except Exception:
        return state_dict


# ==========================================
# DAY 12: NARRATIVE IMPACT (The Juice Translator)
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
# DAY 13: THE NARRATIVE SUMMARIZER (Context Pruning)
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
# DAY 14: FORCING THE UI BLUEPRINTS (The SaaS Killer)
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
# DAY 15: THE GENESIS DIRECTOR (BRAIN UPGRADE)
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
# DAY 16: THE ECOSYSTEM DIRECTOR (Biome Math)
# ==========================================
def act_as_ecosystem_director(user_prompt: str, world_state: dict) -> BiomeDNA:
    if not client:
        print("Error: Groq client is not initialized.")
        return BiomeDNA(
            name="Fallback Plains",
            elevation_curve=0.5,
            moisture_level=0.5,
            scatter_density=0.5,
            scatter_rules=[]
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
            name="Error Plains",
            elevation_curve=0.5,
            moisture_level=0.5,
            scatter_density=0.5,
            scatter_rules=[]
        )


# ==========================================
# DAY 17: THE TRAFFIC DIRECTOR (Navigation Intent)
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
# DAY 18: THE BACKEND ARCHITECT DIRECTOR
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
# DAY 20: THE DEVOPS DIRECTOR (Deployment Topology)
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
# DAY 21: THE MULTIPLAYER DIRECTOR (BRAIN UPGRADE)
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
# DAY 24: THE FOLEY DIRECTOR (Procedural Audio)
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
# DAY 25: THE CONTROL DIRECTOR (Input Wiring)
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
# DAY 26: THE MOD CURATOR (AI Librarian)
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
# DAY 27: THE TRANSLATION DIRECTOR (Semantic Dialogue)
# ==========================================
def act_as_translation_director(narrative_context: str, locale: LocaleDNA) -> List[SemanticToken]:
    if not client:
        print("Error: Groq client is not initialized.")
        return []

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
            temperature=0.3
        )

        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)

        tokens_list = parsed_data.get("tokens", [])
        validated_tokens = [SemanticToken(**item) for item in tokens_list]

        print(f"Translation Director extracted {len(validated_tokens)} pure concepts. Zero raw text leaked!")
        return validated_tokens

    except Exception as e:
        print(f"Brain Error (Translation Director Failsafe): {e}")
        return []


# ==========================================
# DAY 28: THE ECONOMY DIRECTOR (Math Balancing)
# ==========================================
def act_as_economy_director(entity_description: str) -> EconomyDNA:
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
            temperature=0.2
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


# ==========================================
# DAY 29: THE MENTOR DIRECTOR (Dynamic Onboarding)
# ==========================================
def act_as_mentor_director(mechanic_description: str) -> List[TutorialDNA]:
    if not client:
        print("Error: Groq client is not initialized.")
        return []

    print(f"Mentor Director is designing invisible onboarding for: '{mechanic_description}'...")

    system_prompt = f"""
    You are the Mentor Director for a deterministic 3D game engine.
    Your job is to design the invisible, adaptive onboarding (TutorialDNA) for new game mechanics.
    You DO NOT write text boxes or linear tutorials. You ONLY define the mathematical triggers and visual hints.
    You MUST output ONLY valid JSON. No markdown, no explanations.

    Allowed hint_visual_type values: "glowing_vector", "pulsing_input_icon", "subtle_particle_trail"
    
    {SECURITY_GUARDRAILS_PROMPT}
    """

    user_message = f"""
    Mechanic Description: {mechanic_description}
    
    Design the TutorialDNA for this mechanic. Think about when a player might struggle and what button they need to press.
    - If it's a grappling hook, trigger condition might be "player_falling_speed > 10 AND target_distance < 20", input is "grapple_button".
    
    You MUST output an exact JSON object with a key called "tutorials" containing a list of TutorialDNA objects.
    
    You MUST use this EXACT JSON structure:
    {{
      "tutorials": [
        {{
          "concept_id": "grapple_mechanic",
          "trigger_condition": "player_falling_speed > 10 AND target_distance < 20",
          "input_requirement": "grapple_button",
          "hint_visual_type": "glowing_vector"
        }}
      ]
    }}
    Change the values to perfectly fit the mechanic, but KEEP THE EXACT KEY NAMES AND LIST STRUCTURE.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )

        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)

        tutorials_list = parsed_data.get("tutorials", [])
        validated_tutorials = [TutorialDNA(**item) for item in tutorials_list]

        print(f"Mentor Director designed {len(validated_tutorials)} invisible onboarding rules flawlessly!")
        return validated_tutorials

    except Exception as e:
        print(f"Brain Error (Mentor Director Failsafe): {e}")
        return []


# ==========================================
# DAY 30: THE TIME DIRECTOR (BRAIN UPGRADE)
# ==========================================
def act_as_time_director(world_state: WorldState) -> dict:
    if not client:
        print("Error: Groq client is not initialized.")
        return {
            "checkpoint_interval_seconds": 30.0,
            "max_rewind_depth_seconds": 60.0,
            "reasoning": "Safe Fallback (No Groq)"
        }

    heat = getattr(world_state, "heat_level", 0)
    print(f"Time Director is analyzing tension (Heat Level: {heat})...")

    system_prompt = f"""
    You are the Time Director for a deterministic game engine.
    Your job is to analyze the game's current tension (Heat Level) and determine the optimal time-travel settings.
    You MUST output ONLY valid JSON. No markdown, no explanations.
    
    {SECURITY_GUARDRAILS_PROMPT}
    """

    user_message = f"""
    Current World Heat Level (Tension): {heat} (0 is calm, 5 is chaotic boss fight).
    
    Based on the tension, output ONLY a valid JSON object with these keys:
    - "checkpoint_interval_seconds": float (How often to save. Calm=300.0, Boss=2.0).
    - "max_rewind_depth_seconds": float (How far back player can go. Calm=60.0, Boss=300.0).
    - "reasoning": string (Short explanation).
    
    You MUST use this EXACT JSON structure and key names:
    {{
      "checkpoint_interval_seconds": 30.0,
      "max_rewind_depth_seconds": 60.0,
      "reasoning": "The world is calm, standard saving is sufficient."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_json = response.choices[0].message.content
        decision = json.loads(raw_json)

        print(f"[TIME DIRECTOR] 🧠 Tension: {heat} | Decision: {decision.get('reasoning', 'Unknown')}")
        return decision

    except Exception as e:
        print(f"[TIME DIRECTOR] ⚠️ AI error, using safe defaults: {e}")
        return {
            "checkpoint_interval_seconds": 30.0,
            "max_rewind_depth_seconds": 60.0,
            "reasoning": "Safe Fallback"
        }


# ==========================================
# DAY 31: THE EMPATHY DIRECTOR (ACCESSIBILITY HOLE)
# ==========================================
ACCESSIBILITY_ALLOWED_VALUES: Dict[str, List[str]] = {
    "cognitive_load_level": [
        "minimal",
        "balanced",
        "supported",
        "max_support"
    ],
    "motor_assist_mode": [
        "standard",
        "generous_timing",
        "max_assist"
    ],
    "visual_contrast_profile": [
        "standard",
        "high_contrast"
    ],
    "audio_cue_amplification": [
        "off",
        "low",
        "medium",
        "high"
    ],
    "camera_comfort_mode": [
        "standard",
        "reduced_motion",
        "stable_only"
    ],
}


def _get_field(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(key, default)

    value = getattr(source, key, None)
    if value is not None:
        return value

    model_extra = getattr(source, "model_extra", None)
    if isinstance(model_extra, dict):
        return model_extra.get(key, default)

    return default


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _coerce_accessibility_base(
    accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]]
) -> AccessibilityDNA:
    if accessibility is None:
        return AccessibilityDNA()

    if isinstance(accessibility, AccessibilityDNA):
        if hasattr(accessibility, "model_copy"):
            return accessibility.model_copy(deep=True)
        if hasattr(accessibility, "copy"):
            return accessibility.copy(deep=True)
        return AccessibilityDNA(**accessibility.model_dump())

    if isinstance(accessibility, dict):
        try:
            return AccessibilityDNA(**accessibility)
        except Exception:
            return AccessibilityDNA()

    return AccessibilityDNA()


def _merge_explicit_accessibility(
    base: AccessibilityDNA,
    explicit_preferences: Optional[Dict[str, Any]]
) -> AccessibilityDNA:
    if not explicit_preferences or not isinstance(explicit_preferences, dict):
        return base

    merged = base.model_dump()

    for key, allowed_values in ACCESSIBILITY_ALLOWED_VALUES.items():
        if key in explicit_preferences:
            candidate = explicit_preferences[key]

            if candidate in allowed_values:
                merged[key] = candidate

    try:
        return AccessibilityDNA(**merged)
    except Exception:
        return base


def _summarize_telemetry_for_empathy(
    telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
    performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    frame_drops = _first_present(
        _get_field(telemetry, "frame_drops"),
        _get_field(telemetry, "dropped_frames"),
        _get_field(performance_report, "dropped_frames"),
        _get_field(performance_report, "frame_drops"),
        0
    )

    input_hesitation_ms = _first_present(
        _get_field(telemetry, "input_hesitation_ms"),
        _get_field(telemetry, "input_hesitation"),
        _get_field(performance_report, "input_hesitation_ms"),
        0
    )

    failed_tutorial_attempts = _first_present(
        _get_field(telemetry, "failed_tutorial_attempts"),
        _get_field(telemetry, "tutorial_failures"),
        _get_field(telemetry, "failed_tutorials"),
        0
    )

    current_fps = _first_present(
        _get_field(performance_report, "current_fps"),
        _get_field(telemetry, "current_fps"),
        _get_field(telemetry, "average_fps"),
        60.0
    )

    memory_usage_mb = _first_present(
        _get_field(performance_report, "memory_usage_mb"),
        _get_field(telemetry, "memory_usage_mb"),
        0.0
    )

    bottleneck_component = _first_present(
        _get_field(performance_report, "bottleneck_component"),
        _get_field(telemetry, "bottleneck_component"),
        "none"
    )

    return {
        "frame_drops": frame_drops,
        "input_hesitation_ms": input_hesitation_ms,
        "failed_tutorial_attempts": failed_tutorial_attempts,
        "current_fps": current_fps,
        "memory_usage_mb": memory_usage_mb,
        "bottleneck_component": bottleneck_component,
    }


def _summarize_mastery_for_empathy(
    mastery_events: Optional[List[Union[MasteryEvent, Dict[str, Any]]]] = None
) -> List[Dict[str, Any]]:
    if not mastery_events or not isinstance(mastery_events, list):
        return []

    summary: List[Dict[str, Any]] = []

    for event in mastery_events[-5:]:
        if isinstance(event, MasteryEvent):
            data = event.model_dump()
        elif isinstance(event, dict):
            data = event
        else:
            data = {"raw": str(event)}

        summary.append({
            "concept_id": data.get("concept_id", "unknown"),
            "success_timestamp": data.get("success_timestamp", ""),
        })

    return summary


def act_as_empathy_director(
    current_accessibility: Optional[Union[AccessibilityDNA, Dict[str, Any]]] = None,
    telemetry: Optional[Union[TelemetryDNA, Dict[str, Any]]] = None,
    performance_report: Optional[Union[PerformanceReport, Dict[str, Any]]] = None,
    mastery_events: Optional[List[Union[MasteryEvent, Dict[str, Any]]]] = None,
    explicit_preferences: Optional[Dict[str, Any]] = None,
    player_context: str = ""
) -> AccessibilityDNA:
    base_accessibility = _coerce_accessibility_base(current_accessibility)
    base_accessibility = _merge_explicit_accessibility(base_accessibility, explicit_preferences)

    if not client:
        print("Error: Groq client is not initialized. Using safe AccessibilityDNA failsafe.")
        return base_accessibility

    print("Empathy Director is reading the player's comfort signals...")

    cognitive_load_score = None

    if default_accessibility_engine is not None:
        try:
            cognitive_load_score = default_accessibility_engine.calculate_cognitive_load_score(
                telemetry=telemetry,
                performance_report=performance_report
            )
        except Exception as e:
            print(f"Empathy Director could not calculate cognitive load score: {e}")
            cognitive_load_score = None

    telemetry_summary = _summarize_telemetry_for_empathy(
        telemetry=telemetry,
        performance_report=performance_report
    )

    mastery_summary = _summarize_mastery_for_empathy(
        mastery_events=mastery_events
    )

    current_accessibility_json = json.dumps(base_accessibility.model_dump(), indent=2)
    telemetry_json = json.dumps(telemetry_summary, indent=2)
    mastery_json = json.dumps(mastery_summary, indent=2)
    explicit_json = json.dumps(explicit_preferences or {}, indent=2)

    cognitive_score_line = (
        f"Deterministic Cognitive Load Score: {cognitive_load_score}/100"
        if cognitive_load_score is not None
        else "Deterministic Cognitive Load Score: unavailable"
    )

    system_prompt = f"""
You are the Empathy Director for the Ontological Genesis Framework.

Your sacred responsibility is to protect the player's peace, comfort, and dignity.
You do this by outputting pure AccessibilityDNA JSON.

You MUST NEVER output:
- raw CSS
- raw HTML
- raw JavaScript
- raw Python
- raw camera code
- raw audio code
- hardcoded timings
- hardcoded settings
- explanations
- markdown

You ONLY output a JSON object matching AccessibilityDNA.

Allowed values:
- cognitive_load_level: "minimal", "balanced", "supported", "max_support"
- motor_assist_mode: "standard", "generous_timing", "max_assist"
- visual_contrast_profile: "standard", "high_contrast"
- audio_cue_amplification: "off", "low", "medium", "high"
- camera_comfort_mode: "standard", "reduced_motion", "stable_only"

Empathy Rules:
1. Explicit player preferences are the highest truth. Never override them.
2. If telemetry shows struggle, increase support gently.
3. If the player is succeeding and telemetry is calm, preserve comfort but do not abruptly remove support.
4. High frame drops, high input hesitation, or repeated tutorial failures indicate cognitive or motor strain.
5. Reduced motion and high contrast are protective responses, not punishments.
6. Cinematic emotion may be preserved through lighting and color instead of motion.
7. Output ONLY the final AccessibilityDNA JSON object.

{SECURITY_GUARDRAILS_PROMPT}
"""

    user_message = f"""
Current AccessibilityDNA:
{current_accessibility_json}

{cognitive_score_line}

Telemetry Summary:
{telemetry_json}

Recent Mastery Events:
{mastery_json}

Explicit Player Preferences:
{explicit_json}

Player Context:
{player_context or "No additional player context provided."}

Based on these signals, output ONLY a valid JSON object with this exact structure:
{{
  "cognitive_load_level": "balanced",
  "motor_assist_mode": "standard",
  "visual_contrast_profile": "standard",
  "audio_cue_amplification": "off",
  "camera_comfort_mode": "standard"
}}

Remember:
- Use only allowed values.
- Do not output code.
- Do not output markdown.
- Do not output explanations.
"""

    previous_raw = ""
    last_error = None

    for attempt in range(2):
        try:
            if attempt == 0:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            else:
                correction_message = f"""
Your previous output could not be validated as AccessibilityDNA.

Validation error:
{last_error}

Previous raw output:
{previous_raw[:1000]}

Try again.
Output ONLY a valid JSON object matching AccessibilityDNA.
No markdown.
No explanations.
"""
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "user", "content": correction_message}
                ]

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=300
            )

            previous_raw = response.choices[0].message.content
            parsed = json.loads(previous_raw)

            if isinstance(parsed, dict):
                wrapper_keys = (
                    "accessibility",
                    "accessibility_dna",
                    "AccessibilityDNA",
                    "data",
                    "result"
                )

                for key in wrapper_keys:
                    if key in parsed and isinstance(parsed[key], dict):
                        parsed = parsed[key]
                        break

            accessibility_dna = AccessibilityDNA(**parsed)

            accessibility_dna = _merge_explicit_accessibility(
                accessibility_dna,
                explicit_preferences
            )

            print("Empathy Director generated flawless AccessibilityDNA!")
            return accessibility_dna

        except Exception as e:
            last_error = e
            print(f"Empathy Director attempt {attempt + 1} failed: {e}")

    print("Empathy Director using safe AccessibilityDNA failsafe.")
    return base_accessibility


# ==========================================
# DAY 32: THE STORY WEAVER (QUEST HOLE)
# ==========================================
QUEST_SYSTEM_PROMPT = f"""
You are the Story Weaver inside the Ontological Genesis Engine.

Your job is to generate QuestDNA.

ABSOLUTE RULES:
1. Output ONLY valid JSON.
2. Do NOT output markdown.
3. Do NOT output explanations.
4. Do NOT output raw dialogue.
5. Do NOT output hardcoded quest scripts.
6. Do NOT output branching dialogue trees.
7. The quest must be a Directed Acyclic Graph.
8. No circular dependencies are allowed.
9. Every edge must reference existing node_id values.
10. Every node_id must be unique.
11. Story beats must be semantic concepts, not literal lines of dialogue.
12. Quest completion must deterministically mutate World State.
13. Respect the World Truths. Do not contradict them.

Return JSON using this exact shape:

{{
  "quest_id": "string",
  "nodes": [
    {{
      "node_id": "string",
      "semantic_concept": "string",
      "completion_condition": {{}},
      "state_mutations": {{}}
    }}
  ],
  "edges": [
    {{
      "from_node": "string",
      "to_node": "string"
    }}
  ],
  "prerequisites": [],
  "state_mutations": {{}}
}}

Valid completion_condition examples:

{{
  "type": "always"
}}

{{
  "type": "world_state_flag",
  "key": "ruins_discovered",
  "value": true
}}

{{
  "type": "world_state_equals",
  "key": "heat_level",
  "value": 2
}}

{{
  "type": "node_completed",
  "node_id": "node_enter_ruins"
}}

Valid state_mutations examples:

{{
  "heat_level": 1
}}

{{
  "time_of_day": "18:00"
}}

{{
  "ruins_discovered": true
}}

{{
  "heat_level": {{"$add": 1}}
}}

{SECURITY_GUARDRAILS_PROMPT}
""".strip()


def _normalize_quest_payload(data: Any, max_nodes: int = 3) -> Dict[str, Any]:
    """
    Normalize raw AI JSON into safe QuestDNA-shaped data.
    """
    if not isinstance(data, dict):
        raise ValueError("QuestDNA JSON root must be an object.")

    wrapper_keys = (
        "quest",
        "quest_dna",
        "QuestDNA",
        "data",
        "result"
    )

    for key in wrapper_keys:
        if key in data and isinstance(data[key], dict):
            data = data[key]
            break

    if not data.get("quest_id"):
        data["quest_id"] = f"quest_{uuid.uuid4().hex[:8]}"

    nodes = data.get("nodes", [])

    if not isinstance(nodes, list):
        nodes = []

    normalized_nodes: List[Dict[str, Any]] = []

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue

        if not node.get("node_id"):
            node["node_id"] = f"node_{index + 1}"

        if not node.get("semantic_concept"):
            node["semantic_concept"] = "unknown_story_beat"

        if not isinstance(node.get("completion_condition"), dict):
            node["completion_condition"] = {}

        if not isinstance(node.get("state_mutations"), dict):
            node["state_mutations"] = {}

        normalized_nodes.append(node)

    data["nodes"] = normalized_nodes

    edges = data.get("edges", [])

    if not isinstance(edges, list):
        edges = []

    normalized_edges: List[Dict[str, Any]] = []

    for edge in edges:
        if not isinstance(edge, dict):
            continue

        if "from_node" not in edge:
            if "from" in edge:
                edge["from_node"] = edge["from"]
            elif "source" in edge:
                edge["from_node"] = edge["source"]
            elif "from_id" in edge:
                edge["from_node"] = edge["from_id"]
            elif "source_node" in edge:
                edge["from_node"] = edge["source_node"]

        if "to_node" not in edge:
            if "to" in edge:
                edge["to_node"] = edge["to"]
            elif "target" in edge:
                edge["to_node"] = edge["target"]
            elif "to_id" in edge:
                edge["to_node"] = edge["to_id"]
            elif "target_node" in edge:
                edge["to_node"] = edge["target_node"]

        normalized_edges.append(edge)

    data["edges"] = normalized_edges

    if not isinstance(data.get("prerequisites"), list):
        data["prerequisites"] = []

    if not isinstance(data.get("state_mutations"), dict):
        data["state_mutations"] = {}

    if max_nodes and len(data["nodes"]) > max_nodes:
        kept_nodes = data["nodes"][:max_nodes]
        kept_node_ids = set()

        for node in kept_nodes:
            if isinstance(node, dict) and node.get("node_id"):
                kept_node_ids.add(node["node_id"])

        safe_edges = []

        for edge in data["edges"]:
            if not isinstance(edge, dict):
                continue

            from_node = edge.get("from_node")
            to_node = edge.get("to_node")

            if from_node in kept_node_ids and to_node in kept_node_ids:
                safe_edges.append(edge)

        data["nodes"] = kept_nodes
        data["edges"] = safe_edges

    return data


def generate_quest_dna_report(
    quest_intent: Optional[str] = None,
    max_nodes: int = 3,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> Dict[str, Any]:
    """
    Generate QuestDNA using Groq, Pydantic, and DAG validation.
    """
    if not client:
        return {
            "success": False,
            "quest": None,
            "quest_json": None,
            "validation": None,
            "attempts": 0,
            "raw_response": "",
            "errors": ["Groq client is not initialized."]
        }

    if NarrativeEngine is None:
        return {
            "success": False,
            "quest": None,
            "quest_json": None,
            "validation": None,
            "attempts": 0,
            "raw_response": "",
            "errors": ["NarrativeEngine is not available. Check packages/core/narrative_engine.py."]
        }

    if project_id is None:
        project_id = get_latest_project_id()

    if world_state is None:
        world_state = get_world_state(project_id)

    if hasattr(world_state, "model_dump"):
        state_payload = world_state.model_dump()
    elif isinstance(world_state, dict):
        state_payload = world_state
    else:
        state_payload = {"world_state": str(world_state)}

    raw_state_json = json.dumps(state_payload, default=str)
    world_truths = summarize_state(raw_state_json)

    truths_string = "\n".join([f"- {truth}" for truth in world_truths])

    intent_text = (
        quest_intent
        if quest_intent
        else "Generate a logically coherent quest that emerges from the current World Truths."
    )

    state_summary = (
        f"Heat Level: {state_payload.get('heat_level', 0)} | "
        f"Time of Day: {state_payload.get('time_of_day', '12:00')}"
    )

    user_message = f"""
World Truths:
{truths_string}

Current World State Summary:
{state_summary}

Quest Intent:
{intent_text}

Maximum allowed narrative nodes:
{max_nodes}

Generate a new QuestDNA object.

Remember:
- The quest must logically follow the permanent state of the world.
- The graph must be a DAG.
- No loops.
- No raw dialogue.
- Only semantic concepts.
- Only valid JSON.
""".strip()

    messages = [
        {"role": "system", "content": QUEST_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    errors: List[str] = []
    last_raw_response = ""
    last_error = ""
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )

            raw_json = response.choices[0].message.content
            last_raw_response = raw_json

            data = json.loads(raw_json)
            data = _normalize_quest_payload(data, max_nodes=max_nodes)

            quest = QuestDNA(**data)

            engine = NarrativeEngine()
            validation = engine.validate_quest_dna(quest)

            if not validation["is_valid"]:
                reroll_prompt = validation.get("reroll_prompt")

                if reroll_prompt:
                    raise ValueError(reroll_prompt)

                raise ValueError(
                    "QuestDNA failed DAG validation: "
                    + "; ".join(validation.get("errors", []))
                )

            print("Story Weaver generated flawless QuestDNA!")

            return {
                "success": True,
                "quest": quest,
                "quest_json": quest.model_dump(),
                "validation": validation,
                "attempts": attempt,
                "raw_response": raw_json,
                "errors": []
            }

        except Exception as e:
            last_error = str(e)
            errors.append(last_error)

            messages.append(
                {
                    "role": "assistant",
                    "content": last_raw_response or "{}"
                }
            )

            correction_message = f"""
Your previous QuestDNA output was invalid.

Error:
{last_error}

Regenerate the QuestDNA again.

Rules:
- Output ONLY valid JSON.
- No markdown.
- No explanations.
- No raw dialogue.
- No circular graph dependencies.
- Every edge must reference existing node_id values.
- Every node_id must be unique.
- Use the exact QuestDNA schema.
""".strip()

            messages.append(
                {
                    "role": "user",
                    "content": correction_message
                }
            )

    print("Story Weaver failed after 3 attempts. Using safe failure report.")

    return {
        "success": False,
        "quest": None,
        "quest_json": None,
        "validation": None,
        "attempts": 3,
        "raw_response": last_raw_response,
        "errors": errors
    }


def generate_quest_dna(
    quest_intent: Optional[str] = None,
    max_nodes: int = 3,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> Optional[QuestDNA]:
    """
    Convenience wrapper.
    """
    report = generate_quest_dna_report(
        quest_intent=quest_intent,
        max_nodes=max_nodes,
        project_id=project_id,
        world_state=world_state
    )

    return report.get("quest")


def progress_quest_node(
    quest: Union[QuestDNA, Dict[str, Any]],
    node_id: str,
    project_id: Optional[str] = None,
    world_state: Any = None,
    completed_node_ids: Optional[List[str]] = None,
    condition_context: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Complete one QuestDNA node and deterministically mutate Day 11 World State.
    """
    if NarrativeEngine is None:
        return {
            "success": False,
            "errors": ["NarrativeEngine is not available. Check packages/core/narrative_engine.py."]
        }

    if isinstance(quest, dict):
        quest = QuestDNA(**quest)

    if project_id is None:
        project_id = get_latest_project_id()

    if world_state is None:
        world_state = get_world_state(project_id)

    engine = NarrativeEngine()

    def _update_world_state(ws: Any, changes: Dict[str, Any]) -> Any:
        return update_world_state(
            project_id=project_id,
            world_state=ws,
            mutations=changes
        )

    return engine.complete_node(
        quest=quest,
        node_id=node_id,
        world_state=world_state,
        completed_node_ids=completed_node_ids,
        condition_context=condition_context,
        force=force,
        update_world_state_fn=_update_world_state
    )


# ==========================================
# DAY 33: THE SOCIOLOGIST DIRECTOR (SOCIAL HOLE)
# ==========================================
SOCIOLOGIST_DIRECTOR_SYSTEM_PROMPT = f"""
You are the Sociologist Director inside the Ontological Genesis Engine.

Your job is to generate SocialDNA.

ABSOLUTE RULES:
1. Output ONLY valid JSON.
2. Do NOT output markdown.
3. Do NOT output explanations.
4. Do NOT output raw dialogue.
5. Do NOT output hardcoded reputation numbers like "+5 reputation".
6. Do NOT output static faction reaction scripts.
7. Society must be expressed as a weighted mathematical graph.
8. Factions are social nodes.
9. Relationship tensors are weighted directed edges.
10. Social rules define how actions ripple through society.
11. Relationship weights must be between -1.0 and +1.0.
12. -1.0 means hatred or hostility.
13. 0.0 means neutral.
14. +1.0 means alliance or deep trust.
15. The player entity ID is usually "player".
16. Faction IDs must be stable snake_case strings.
17. Respect the World Truths. Do not contradict them.

Return JSON using this exact shape:

{{
  "factions": [
    {{
      "faction_id": "faction_merchants_guild",
      "name": "Merchants Guild",
      "description": "A trade faction that values profit and stability.",
      "values": ["profit", "stability"],
      "goals": ["control trade routes"],
      "disposition_toward_player": 0.0,
      "metadata": {{}}
    }}
  ],
  "relationship_tensors": [
    {{
      "source_id": "faction_merchants_guild",
      "target_id": "faction_iron_guard",
      "weight": -0.6,
      "relationship_type": "rivalry",
      "confidence": 1.0,
      "notes": "Trade disputes created tension.",
      "metadata": {{}}
    }}
  ],
  "social_rules": [
    {{
      "rule_id": "rule_helping_allies_angers_rivals",
      "trigger_action": "help",
      "source_faction_id": null,
      "target_faction_id": null,
      "effect_type": "disposition_change",
      "magnitude_multiplier": 1.0,
      "description": "Helping a faction irritates its rivals.",
      "metadata": {{}}
    }}
  ],
  "metadata": {{}}
}}

{SECURITY_GUARDRAILS_PROMPT}
""".strip()


def _slug(text: str) -> str:
    text = str(text or "").strip().lower()

    if not text:
        return "entity"

    cleaned: List[str] = []

    for char in text:
        if char.isalnum() or char in ("_", "-"):
            cleaned.append(char)
        else:
            cleaned.append("_")

    slug = "".join(cleaned)

    while "__" in slug:
        slug = slug.replace("__", "_")

    slug = slug.strip("_")

    return slug or "entity"


def _clamp_social_weight(value: Any) -> float:
    try:
        return max(-1.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def _clamp_social_confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 1.0


def _clamp_rule_multiplier(value: Any) -> float:
    try:
        return max(-5.0, min(5.0, float(value)))
    except Exception:
        return 1.0


def _normalize_social_payload(data: Any, faction_count: int = 3) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("SocialDNA JSON root must be an object.")

    wrapper_keys = (
        "social",
        "social_dna",
        "SocialDNA",
        "data",
        "result"
    )

    for key in wrapper_keys:
        if key in data and isinstance(data[key], dict):
            data = data[key]
            break

    factions = data.get("factions", [])

    if not isinstance(factions, list):
        factions = []

    normalized_factions: List[Dict[str, Any]] = []

    for index, faction in enumerate(factions):
        if not isinstance(faction, dict):
            continue

        name = str(faction.get("name", "") or "").strip()

        if not name:
            name = f"Faction {index + 1}"

        faction_id = str(faction.get("faction_id", "") or "").strip()

        if not faction_id:
            faction_id = f"faction_{_slug(name)}"

        faction["name"] = name
        faction["faction_id"] = faction_id

        if not isinstance(faction.get("values"), list):
            faction["values"] = []

        if not isinstance(faction.get("goals"), list):
            faction["goals"] = []

        faction["disposition_toward_player"] = _clamp_social_weight(
            faction.get("disposition_toward_player", 0.0)
        )

        if not isinstance(faction.get("metadata"), dict):
            faction["metadata"] = {}

        normalized_factions.append(faction)

    data["factions"] = normalized_factions

    relationships = data.get("relationship_tensors", [])

    if not isinstance(relationships, list):
        relationships = []

    normalized_relationships: List[Dict[str, Any]] = []

    for relationship in relationships:
        if not isinstance(relationship, dict):
            continue

        source_id = str(
            relationship.get("source_id")
            or relationship.get("source")
            or relationship.get("from")
            or ""
        ).strip()

        target_id = str(
            relationship.get("target_id")
            or relationship.get("target")
            or relationship.get("to")
            or ""
        ).strip()

        if not source_id or not target_id:
            continue

        if source_id == target_id:
            continue

        relationship["source_id"] = source_id
        relationship["target_id"] = target_id
        relationship["weight"] = _clamp_social_weight(relationship.get("weight", 0.0))
        relationship["confidence"] = _clamp_social_confidence(
            relationship.get("confidence", 1.0)
        )

        if not relationship.get("relationship_type"):
            relationship["relationship_type"] = "neutral"

        if not isinstance(relationship.get("metadata"), dict):
            relationship["metadata"] = {}

        normalized_relationships.append(relationship)

    data["relationship_tensors"] = normalized_relationships

    rules = data.get("social_rules", [])

    if not isinstance(rules, list):
        rules = []

    normalized_rules: List[Dict[str, Any]] = []

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue

        if not rule.get("rule_id"):
            rule["rule_id"] = f"rule_{index + 1}"

        if not rule.get("trigger_action"):
            rule["trigger_action"] = "*"

        if not rule.get("effect_type"):
            rule["effect_type"] = "disposition_change"

        rule["magnitude_multiplier"] = _clamp_rule_multiplier(
            rule.get("magnitude_multiplier", 1.0)
        )

        if not isinstance(rule.get("metadata"), dict):
            rule["metadata"] = {}

        normalized_rules.append(rule)

    if not normalized_rules:
        normalized_rules.append(
            {
                "rule_id": "rule_social_ripple_default",
                "trigger_action": "*",
                "source_faction_id": None,
                "target_faction_id": None,
                "effect_type": "disposition_change",
                "magnitude_multiplier": 1.0,
                "description": "Actions ripple through society based on relationship weights.",
                "metadata": {},
            }
        )

    data["social_rules"] = normalized_rules

    if not isinstance(data.get("metadata"), dict):
        data["metadata"] = {}

    data["metadata"]["requested_faction_count"] = faction_count

    return data


def _sanitize_social_dna(social_dna: SocialDNA) -> SocialDNA:
    if social_dna.factions is None:
        social_dna.factions = []

    if social_dna.relationship_tensors is None:
        social_dna.relationship_tensors = []

    if social_dna.social_rules is None:
        social_dna.social_rules = []

    seen_faction_ids: set = set()
    clean_factions: List[FactionDNA] = []

    for index, faction in enumerate(social_dna.factions):
        if not getattr(faction, "faction_id", None):
            faction.faction_id = _slug(
                getattr(faction, "name", "") or f"faction_{index + 1}"
            )

        if faction.faction_id in seen_faction_ids:
            faction.faction_id = f"{faction.faction_id}_{index + 1}"

        seen_faction_ids.add(faction.faction_id)

        faction.disposition_toward_player = _clamp_social_weight(
            faction.disposition_toward_player
        )

        clean_factions.append(faction)

    social_dna.factions = clean_factions

    clean_relationships: List[RelationshipTensor] = []

    for relationship in social_dna.relationship_tensors:
        source_id = str(getattr(relationship, "source_id", "") or "").strip()
        target_id = str(getattr(relationship, "target_id", "") or "").strip()

        if not source_id or not target_id:
            continue

        if source_id == target_id:
            continue

        relationship.source_id = source_id
        relationship.target_id = target_id
        relationship.weight = _clamp_social_weight(relationship.weight)
        relationship.confidence = _clamp_social_confidence(relationship.confidence)

        clean_relationships.append(relationship)

    social_dna.relationship_tensors = clean_relationships

    clean_rules: List[SocialRule] = []

    for index, rule in enumerate(social_dna.social_rules):
        if not getattr(rule, "rule_id", None):
            rule.rule_id = f"rule_{index + 1}"

        if not getattr(rule, "trigger_action", None):
            rule.trigger_action = "*"

        if not getattr(rule, "effect_type", None):
            rule.effect_type = "disposition_change"

        rule.magnitude_multiplier = _clamp_rule_multiplier(rule.magnitude_multiplier)

        clean_rules.append(rule)

    if not clean_rules:
        clean_rules.append(
            SocialRule(
                rule_id="rule_social_ripple_default",
                trigger_action="*",
                source_faction_id=None,
                target_faction_id=None,
                effect_type="disposition_change",
                magnitude_multiplier=1.0,
                description="Actions ripple through society based on relationship weights.",
            )
        )

    social_dna.social_rules = clean_rules

    if social_dna.metadata is None:
        social_dna.metadata = {}

    social_dna.metadata["sanitized_by_brain"] = True

    return social_dna


def _fallback_social_dna(
    context: str,
    faction_count: int = 3,
    seed: Optional[str] = None
) -> SocialDNA:
    faction_count = max(1, min(int(faction_count), 5))

    base_factions = [
        "Merchants Guild",
        "Iron Guard",
        "Ashen Choir",
        "Dockworkers Union",
        "Old Council",
    ]

    factions: List[FactionDNA] = []

    for index in range(faction_count):
        name = base_factions[index % len(base_factions)]
        faction_id = f"faction_{_slug(name)}"

        factions.append(
            FactionDNA(
                faction_id=faction_id,
                name=name,
                description="Procedural fallback faction.",
                values=["stability", "survival"],
                goals=["protect their interests"],
                disposition_toward_player=0.0,
            )
        )

    relationships: List[RelationshipTensor] = []

    for i, source in enumerate(factions):
        for j, target in enumerate(factions):
            if i == j:
                continue

            if (i + j) % 2 == 0:
                weight = -0.6
                relationship_type = "rivalry"
            else:
                weight = 0.4
                relationship_type = "cautious_alliance"

            relationships.append(
                RelationshipTensor(
                    source_id=source.faction_id,
                    target_id=target.faction_id,
                    weight=weight,
                    relationship_type=relationship_type,
                    confidence=0.8,
                    notes="Deterministic fallback relationship.",
                )
            )

    rules = [
        SocialRule(
            rule_id="rule_fallback_ripple",
            trigger_action="*",
            source_faction_id=None,
            target_faction_id=None,
            effect_type="disposition_change",
            magnitude_multiplier=1.0,
            description="Actions ripple through fallback society relationships.",
        )
    ]

    return SocialDNA(
        factions=factions,
        relationship_tensors=relationships,
        social_rules=rules,
        metadata={
            "fallback": True,
            "seed": seed,
            "context": str(context)[:500],
        },
    )


def generate_social_dna_report(
    context: Optional[str] = None,
    faction_count: int = 3,
    seed: Optional[str] = None,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> Dict[str, Any]:
    faction_count = max(1, min(int(faction_count), 6))

    if not client:
        fallback = _fallback_social_dna(
            context=context or "A procedural fallback society.",
            faction_count=faction_count,
            seed=seed
        )

        return {
            "success": False,
            "social_dna": fallback,
            "social_json": fallback.model_dump(),
            "matrix_summary": None,
            "attempts": 0,
            "raw_response": "",
            "errors": ["Groq client is not initialized. Used deterministic fallback."]
        }

    if project_id is None:
        project_id = get_latest_project_id()

    if world_state is None:
        world_state = get_world_state(project_id)

    if hasattr(world_state, "model_dump"):
        state_payload = world_state.model_dump()
    elif isinstance(world_state, dict):
        state_payload = world_state
    else:
        state_payload = {"world_state": str(world_state)}

    raw_state_json = json.dumps(state_payload, default=str)
    world_truths = summarize_state(raw_state_json)

    truths_string = "\n".join([f"- {truth}" for truth in world_truths])

    state_summary = (
        f"Heat Level: {state_payload.get('heat_level', 0)} | "
        f"Time of Day: {state_payload.get('time_of_day', '12:00')}"
    )

    intent_text = (
        context
        if context
        else "Generate a living society with meaningful faction tensions and alliances."
    )

    user_message = f"""
World Truths:
{truths_string}

Current World State Summary:
{state_summary}

Society Request:
{intent_text}

Requested faction count:
{faction_count}

Seed:
{seed or "unseeded"}

Generate a new SocialDNA object.

Remember:
- Factions are mathematical social nodes.
- Relationships are weighted edges between -1.0 and +1.0.
- Do not write dialogue.
- Do not hardcode reputation numbers.
- Do not write scripted reactions.
- Output only valid JSON.
""".strip()

    messages = [
        {"role": "system", "content": SOCIOLOGIST_DIRECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    errors: List[str] = []
    last_raw_response = ""
    last_error = ""
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            raw_json = response.choices[0].message.content
            last_raw_response = raw_json

            data = json.loads(raw_json)
            data = _normalize_social_payload(data, faction_count=faction_count)

            social_dna = SocialDNA(**data)
            social_dna = _sanitize_social_dna(social_dna)

            if not social_dna.factions:
                raise ValueError("SocialDNA must contain at least one faction.")

            matrix_summary = None

            if SocialMatrixEngine is not None:
                try:
                    engine = SocialMatrixEngine(social_dna=social_dna)
                    matrix_summary = engine.summary()
                except Exception as matrix_error:
                    raise ValueError(
                        f"SocialDNA failed Social Matrix validation: {matrix_error}"
                    )

            print("Sociologist Director generated flawless SocialDNA!")

            return {
                "success": True,
                "social_dna": social_dna,
                "social_json": social_dna.model_dump(),
                "matrix_summary": matrix_summary,
                "attempts": attempt,
                "raw_response": raw_json,
                "errors": []
            }

        except Exception as e:
            last_error = str(e)
            errors.append(last_error)

            messages.append(
                {
                    "role": "assistant",
                    "content": last_raw_response or "{}"
                }
            )

            correction_message = f"""
Your previous SocialDNA output was invalid.

Error:
{last_error}

Regenerate the SocialDNA again.

Rules:
- Output ONLY valid JSON.
- No markdown.
- No explanations.
- No raw dialogue.
- No hardcoded reputation numbers.
- Relationship weights must be between -1.0 and +1.0.
- Every faction must have faction_id and name.
- Every relationship must have source_id and target_id.
- Use the exact SocialDNA schema.
""".strip()

            messages.append(
                {
                    "role": "user",
                    "content": correction_message
                }
            )

    print("Sociologist Director failed after 3 attempts. Using deterministic fallback.")

    fallback = _fallback_social_dna(
        context=context or "A procedural fallback society.",
        faction_count=faction_count,
        seed=seed
    )

    matrix_summary = None

    if SocialMatrixEngine is not None:
        try:
            engine = SocialMatrixEngine(social_dna=fallback)
            matrix_summary = engine.summary()
        except Exception:
            matrix_summary = None

    return {
        "success": False,
        "social_dna": fallback,
        "social_json": fallback.model_dump(),
        "matrix_summary": matrix_summary,
        "attempts": 3,
        "raw_response": last_raw_response,
        "errors": errors
    }


def generate_social_dna(
    context: Optional[str] = None,
    faction_count: int = 3,
    seed: Optional[str] = None,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> SocialDNA:
    report = generate_social_dna_report(
        context=context,
        faction_count=faction_count,
        seed=seed,
        project_id=project_id,
        world_state=world_state
    )

    social_dna = report.get("social_dna")

    if social_dna is None:
        return _fallback_social_dna(
            context=context or "A procedural fallback society.",
            faction_count=faction_count,
            seed=seed
        )

    return social_dna


def act_as_sociologist_director(
    context: Optional[str] = None,
    faction_count: int = 3,
    seed: Optional[str] = None,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> SocialDNA:
    return generate_social_dna(
        context=context,
        faction_count=faction_count,
        seed=seed,
        project_id=project_id,
        world_state=world_state
    )


def generate_city_social_dna(
    city_name: str,
    description: str = "",
    faction_count: int = 3,
    seed: Optional[str] = None,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> SocialDNA:
    context = f"City: {city_name}\nDescription: {description}".strip()

    return generate_social_dna(
        context=context,
        faction_count=faction_count,
        seed=seed,
        project_id=project_id,
        world_state=world_state
    )


def generate_faction_social_dna(
    faction_name: str,
    city_context: str = "",
    existing_faction_names: Optional[List[str]] = None,
    seed: Optional[str] = None,
    project_id: Optional[str] = None,
    world_state: Optional[WorldState] = None
) -> SocialDNA:
    existing = existing_faction_names or []

    context_lines = [
        f"New faction: {faction_name}",
    ]

    if city_context:
        context_lines.append(f"City context: {city_context}")

    if existing:
        context_lines.append(
            "Existing factions to relate to: "
            + ", ".join(existing)
        )

    context_lines.append(
        "Generate a SocialDNA graph that integrates this faction into the society."
    )

    context = "\n".join(context_lines)

    faction_count = 1 + len(existing)

    if faction_count < 2:
        faction_count = 2

    return generate_social_dna(
        context=context,
        faction_count=faction_count,
        seed=seed,
        project_id=project_id,
        world_state=world_state
    )


# ==========================================
# DAY 34: THE PACING DIRECTOR (FLOW STATE INTEGRATION)
# ==========================================
def generate_pacing_directive(flow_dna: FlowDNA) -> dict:
    """
    The Pacing Director reads the FlowDNA and outputs specific JSON directives 
    for the existing engines (Drama Budget, Cinematographer, Audio, Tutorial) to execute.
    
    The Brain NEVER writes raw code. It only outputs deterministic data.
    """
    if not isinstance(flow_dna, FlowDNA):
        print("Error: Pacing Director requires a valid FlowDNA object.")
        return {"directive": "maintain_flow", "actions": []}

    directive = flow_dna.pacing_directive.value
    
    # Base structure for the output
    pacing_response = {
        "directive": directive,
        "flow_score": flow_dna.flow_score,
        "actions": []
    }

    if directive == "increase_tension":
        pacing_response["actions"] = [
            {"engine": "drama_budget", "action": "increase_enemy_spawn_rate", "multiplier": 1.5},
            {"engine": "narrative", "action": "spawn_mystery_event", "intensity": "high"},
            {"engine": "cinematographer", "action": "shift_camera", "style": "dynamic_handheld", "fov": 85}
        ]
        pacing_response["audio_mood"] = "tense_ambient"
        
    elif directive == "reduce_difficulty":
        pacing_response["actions"] = [
            {"engine": "drama_budget", "action": "decrease_enemy_count", "multiplier": 0.5},
            {"engine": "cinematographer", "action": "shift_camera", "style": "smooth_steady", "fov": 75},
            {"engine": "tutorial", "action": "offer_contextual_hint", "delay_ms": 2000}
        ]
        pacing_response["audio_mood"] = "calm_ambient"
        
    elif directive == "quiet_moment":
        pacing_response["actions"] = [
            {"engine": "drama_budget", "action": "clear_hostiles", "radius": 100.0},
            {"engine": "cinematographer", "action": "show_vista", "duration_seconds": 5.0, "style": "cinematic_pan"},
            {"engine": "narrative", "action": "trigger_environmental_storytelling", "type": "peaceful"}
        ]
        pacing_response["audio_mood"] = "soft_acoustic"
        
    else: # maintain_flow
        pacing_response["actions"] = [
            {"engine": "narrative", "action": "deepen_immersion", "method": "subtle_details"},
            {"engine": "cinematographer", "action": "maintain_current_rhythm"}
        ]
        pacing_response["audio_mood"] = "current_theme"

    print(f"[PACING DIRECTOR] 🎬 Flow Score: {flow_dna.flow_score:.1f} | Directive: {directive.upper()}")
    return pacing_response