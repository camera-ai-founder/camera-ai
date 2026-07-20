import os
import sys
# CRITICAL FIX: Tell Python to look in the root folder for our packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import json
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client

# ==========================================
# DAY 12 IMPORTS: The Juice Engine & Brain
# ==========================================
try:
    from packages.core.models import ImpactVector, JuiceProfile, StateDelta
except ImportError:
    ImpactVector = None
    JuiceProfile = None
    StateDelta = None

try:
    from packages.core import brain
except ImportError:
    brain = None

# ==========================================
# DAY 21 IMPORT: The Deterministic Netcode Engine
# ==========================================
try:
    from packages.core.netcode_engine import NetcodeEngine
except ImportError:
    NetcodeEngine = None

# ==========================================
# DAY 23 IMPORTS: Telemetry & Self-Healing
# ==========================================
try:
    from packages.core.models import PerformanceReport, AppDNA
    from packages.core.telemetry_engine import telemetry_brain
except ImportError:
    PerformanceReport = None
    AppDNA = None
    telemetry_brain = None

# ==========================================
# DAY 26 IMPORTS: The Mod Loader API
# ==========================================
try:
    from packages.core.models import ModDNA, DramaBudget, WorldState
    from packages.core.modding_engine import engine as modding_engine
except ImportError as e:
    ModDNA = None
    DramaBudget = None
    WorldState = None
    modding_engine = None
    print(f"WARNING: Modding system import failed: {e}")

# ==========================================
# DAY 32 IMPORTS: The Quest Hole / Narrative Graphs
# ==========================================
try:
    from packages.core.models import QuestDNA
    from packages.core.narrative_engine import NarrativeEngine
except ImportError as e:
    QuestDNA = None
    NarrativeEngine = None
    print(f"WARNING: Day 32 Narrative Graph system import failed: {e}")

# --- 0. LOAD THE .ENV FILE ---
load_dotenv()

# --- SET UP LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("FlaskApp")

# --- 1. SETUP SUPABASE ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    logger.warning("Supabase credentials not found. Black Box and Realtime are offline.")
    supabase = None
else:
    supabase: Client = create_client(url, key)

# --- 2. SETUP FLASK ---
app = Flask(__name__)

# ==========================================
# DAY 21: STATE MANAGEMENT HELPERS
# ==========================================
STATE_FILE_PATH = "OGF_STATE.json"

def load_current_state() -> dict:
    """Reads the current master state from our JSON DNA file."""
    if not os.path.exists(STATE_FILE_PATH):
        return {"nodes": [], "world_state": {}}
    with open(STATE_FILE_PATH, "r") as f:
        return json.load(f)

def save_current_state(state: dict):
    """Saves the updated master state back to our JSON DNA file."""
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f, indent=4)

# ==========================================
# DAY 23: BACKGROUND WORKER (THE BLACK BOX WRITER)
# ==========================================
def save_to_blackbox(report_data: dict):
    if not supabase:
        return
    try:
        supabase.table("telemetry_logs").insert(report_data).execute()
        logger.info("📦 Black Box: Telemetry report saved successfully.")
    except Exception as e:
        logger.error(f"Black Box write failed: {e}")

# ==========================================
# DAY 32: QUEST LOG HELPERS
# ==========================================
def _quest_log_latest_project_id():
    """
    Safely fetch the latest project ID.

    Priority:
    1. Use brain.get_latest_project_id() if available.
    2. Fall back to direct Supabase query.
    """
    if brain and hasattr(brain, "get_latest_project_id"):
        try:
            return brain.get_latest_project_id()
        except Exception as e:
            logger.error(f"Quest Log could not use brain.get_latest_project_id: {e}")

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
        logger.error(f"Quest Log could not fetch latest project ID: {e}")

    return None


def _quest_log_default_tokens():
    """
    Day 10 Atomic Token Synthesizer fallback.

    These tokens are pure visual DNA.
    The React Quest Log reads these tokens and compiles reality.
    """
    return {
        "accent_primary": "#3B82F6",
        "accent_active": "#38BDF8",
        "accent_completed": "#22C55E",
        "accent_locked": "#64748B",
        "background_color": "#0F172A",
        "surface_color": "#111827",
        "text_color": "#E2E8F0",
        "muted_text_color": "#94A3B8",
        "spacing_unit": 8,
        "radius": 12,
        "border_width": 1,
        "motion_entrance": "fade-in-up"
    }


def _quest_log_demo_dna():
    """
    Safe demo QuestDNA.

    This is used only when no active Supabase quest graph exists yet.
    It allows the Quest Log UI to render deterministically.
    """
    return {
        "quest_id": "quest_demo_ruins",
        "nodes": [
            {
                "node_id": "node_enter_ruins",
                "semantic_concept": "player_discovers_the_old_world_ruins",
                "completion_condition": {
                    "type": "always"
                },
                "state_mutations": {
                    "ruins_discovered": True
                }
            },
            {
                "node_id": "node_find_signal",
                "semantic_concept": "player_finds_a_weak_unknown_signal",
                "completion_condition": {
                    "type": "node_completed",
                    "node_id": "node_enter_ruins"
                },
                "state_mutations": {
                    "signal_found": True,
                    "heat_level": {"$add": 1}
                }
            },
            {
                "node_id": "node_open_vault",
                "semantic_concept": "player_opens_the_hidden_vault_door",
                "completion_condition": {
                    "type": "node_completed",
                    "node_id": "node_find_signal"
                },
                "state_mutations": {
                    "vault_open": True,
                    "time_of_day": "18:00"
                }
            }
        ],
        "edges": [
            {
                "from_node": "node_enter_ruins",
                "to_node": "node_find_signal"
            },
            {
                "from_node": "node_find_signal",
                "to_node": "node_open_vault"
            }
        ],
        "prerequisites": [],
        "state_mutations": {
            "quest_demo_ruins_complete": True
        }
    }


def _quest_log_node_state_mutations(node):
    """
    Safely read node-level state_mutations.

    NarrativeNode allows extra fields, so state_mutations may exist
    inside model_extra until we formally type it later.
    """
    mutations = getattr(node, "state_mutations", None)

    if mutations is None:
        extra = getattr(node, "model_extra", {}) or {}
        mutations = extra.get("state_mutations", {})

    if mutations is None:
        return {}

    if isinstance(mutations, dict):
        return mutations

    return {}


def _quest_log_parse_completed_node_ids(raw_value: str):
    """
    Parse completed node IDs from the query string.

    Supported formats:
    - ?completed=node_1,node_2
    - ?completed=["node_1","node_2"]
    """
    if not raw_value:
        return []

    raw_value = raw_value.strip()

    if raw_value.startswith("["):
        try:
            parsed = json.loads(raw_value)

            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]

        except Exception:
            pass

    return [
        part.strip()
        for part in raw_value.split(",")
        if part.strip()
    ]

# ==========================================
# 3. MAIN WEB PAGE ROUTE
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# 4. API ROUTE FOR CYTOSCAPE
# ==========================================
@app.route('/api/graph')
def get_graph_data():
    if not supabase:
        return jsonify({"nodes": [], "edges": [], "debug": {"error": "Supabase offline"}}), 500

    response = supabase.table('nodes').select('*').execute()
    all_nodes = response.data

    cy_nodes = []
    cy_edges = []
    edges_created = 0

    for node in all_nodes:
        node_label = node.get('label', 'Node')
        parent_id = node.get('parent_id')

        cy_nodes.append({
            "data": {
                "id": str(node['id']),
                "label": str(node_label)
            }
        })
        
        if parent_id is not None and str(parent_id).lower() not in ['null', '']:
            edges_created += 1
            cy_edges.append({
                "data": {
                    "source": str(parent_id),
                    "target": str(node['id'])
                }
            })

    return jsonify({
        "nodes": cy_nodes,
        "edges": cy_edges,
        "debug": {
            "total_nodes": len(cy_nodes),
            "total_edges": len(cy_edges),
            "edges_created": edges_created
        }
    })

# ==========================================
# 5. DAY 12: WEB APP INTEGRATION (The Bridge)
# ==========================================
@app.route('/api/impact', methods=['POST'])
def trigger_impact():
    if not ImpactVector or not JuiceProfile or not brain:
        return jsonify({"error": "Day 12 Juice Engine not available"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    impact_vector = ImpactVector(**data.get('impact_vector', {}))
    juice = JuiceProfile(
        impact_type=data.get('impact_type', 'default'),
        ragdoll_decay=data.get('ragdoll_decay', 0.5),
        impact_vector=impact_vector
    )

    narrative = brain.generate_narrative_impact(juice, object_name="the target")

    return jsonify({
        "status": "success",
        "narrative": narrative,
        "vector": impact_vector.model_dump(),
        "decay": juice.ragdoll_decay
    })

# ==========================================
# 6. DAY 18: THE LIVE CANVAS (SUPABASE REALTIME)
# ==========================================
@app.route('/api/live-canvas', methods=['POST'])
def update_live_canvas():
    if not supabase:
        return jsonify({"status": "error", "message": "Supabase offline"}), 500

    try:
        new_state = request.get_json()
        response = supabase.table("live_canvas_state").upsert({
            "id": 1, 
            "data": new_state
        }).execute()
        return jsonify({"status": "success", "message": "Live Canvas broadcasted!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not broadcast. Error: {str(e)}"}), 500

# ==========================================
# 7. DAY 21: DETERMINISTIC NETCODE BROADCAST
# ==========================================
@app.route('/api/update_state', methods=['POST'])
def update_state():
    if not supabase or not NetcodeEngine:
        return jsonify({"status": "error", "message": "Supabase or Netcode Engine offline"}), 500

    try:
        new_state_data = request.get_json()
        if not new_state_data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        old_state_data = load_current_state()
        delta: StateDelta = NetcodeEngine.calculate_delta(old_state_data, new_state_data)
        save_current_state(new_state_data)
        
        delta_payload = delta.model_dump(mode='json')
        
        supabase.table("state_deltas").insert({
            "delta_data": delta_payload,
            "timestamp": delta_payload["timestamp"]
        }).execute()
        
        return jsonify({
            "status": "success", 
            "message": "Delta calculated and broadcasted via Supabase Realtime!",
            "changed_nodes_count": len(delta_payload.get("changed_nodes", [])),
            "changed_tokens_count": len(delta_payload.get("changed_tokens", {})),
            "removed_nodes_count": len(delta_payload.get("removed_node_ids", []))
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not broadcast delta. Error: {str(e)}"}), 500

# ==========================================
# 8. DAY 23: TELEMETRY BLACK BOX ENDPOINTS
# ==========================================
@app.route('/api/telemetry/report', methods=['POST'])
def receive_telemetry_report():
    if not PerformanceReport:
        return jsonify({"status": "error", "message": "Telemetry models not available"}), 500

    try:
        raw_json = request.json
        report = PerformanceReport.model_validate(raw_json)
        logger.info(f" Telemetry Received: FPS {report.current_fps} | Bottleneck: {report.bottleneck_component}")

        if supabase:
            thread = threading.Thread(target=save_to_blackbox, args=(report.model_dump(mode='json'),))
            thread.daemon = True
            thread.start()

        return jsonify({"status": "received", "message": "Logged to Black Box"}), 200
    except Exception as e:
        logger.error(f"Invalid Telemetry Report received: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/telemetry/history', methods=['GET'])
def get_telemetry_history():
    if not supabase:
        return jsonify({"error": "Black Box offline"}), 500
    try:
        response = supabase.table("telemetry_logs").select("*").order("created_at", desc=True).limit(5).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telemetry/heal', methods=['POST'])
def trigger_ai_healing():
    if not PerformanceReport or not telemetry_brain or not AppDNA:
        return jsonify({"status": "error", "message": "AI Healing system not available"}), 500

    try:
        raw_json = request.json
        report = PerformanceReport.model_validate(raw_json)
        current_dna = AppDNA()
        healed_dna = telemetry_brain.heal_dna(report, current_dna)
        
        return jsonify({
            "status": "healed",
            "healed_dna": healed_dna.model_dump(mode='json')
        }), 200
    except Exception as e:
        logger.error(f"AI Healing failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# DAY 26: THE MOD LOADER API (BULLETPROOF VERSION)
# ==========================================
@app.route('/api/mods', methods=['GET'])
def get_approved_mods():
    if not supabase:
        return jsonify({"error": "Supabase offline"}), 500
    try:
        response = supabase.table('community_vault').select('id, mod_name, metadata').eq('status', 'approved').execute()
        return jsonify(response.data), 200
    except Exception as e:
        logger.error(f"Error fetching mods: {e}")
        return jsonify({"error": "Could not fetch mods"}), 500

@app.route('/api/mods/install', methods=['POST'])
def install_mod():
    """Takes a Mod ID, fetches the safe JSON, and injects it into OGF_STATE."""
    if not supabase:
        logger.error("Supabase not available")
        return jsonify({"success": False, "message": "Supabase not available"}), 500
    
    if not ModDNA or not modding_engine:
        logger.error("Modding system not available. Check imports.")
        logger.error(f"ModDNA: {ModDNA}, modding_engine: {modding_engine}")
        return jsonify({"success": False, "message": "Modding system not available on server."}), 500
        
    try:
        data = request.json
        mod_id = data.get('mod_id')
        logger.info(f"📥 Attempting to install mod ID: {mod_id}")

        # 1. Fetch the pure JSON from our secure vault
        response = supabase.table('community_vault') \
            .select('mod_dna, mod_name, status') \
            .eq('id', mod_id) \
            .single() \
            .execute()
            
        if not response.data:
            logger.error(f"❌ Mod ID {mod_id} not found in database.")
            return jsonify({"success": False, "message": "Mod not found in Vault."}), 404
            
        mod_dna_dict = response.data.get('mod_dna')
        mod_name = response.data.get('mod_name', 'Unknown Mod')

        # CRITICAL CHECK: Is the mod_dna column actually empty in Supabase?
        if not mod_dna_dict:
            logger.error(f"❌ Mod '{mod_name}' has NO 'mod_dna' data in the database!")
            return jsonify({"success": False, "message": f"Mod '{mod_name}' has empty or missing DNA data in Supabase. Please update the row."}), 400

        # 2. Force it through the Pydantic Bouncer
        logger.info(f"🛡️ Validating DNA for: {mod_name}")
        safe_mod = ModDNA(**mod_dna_dict)

        # 3. Get current World State and Drama Budget
        current_state_dict = load_current_state()
        ws_dict = current_state_dict.get("world_state", current_state_dict)
        current_world = WorldState(**ws_dict)
        current_budget = DramaBudget() 

        # 4. Trigger the Safe Injection Engine!
        logger.info(f"⚙️ Injecting mod: {mod_name}")
        new_world = modding_engine.inject_mod(current_world, safe_mod, current_budget)
        
        # 5. Save back to OGF_STATE.json
        current_state_dict["world_state"] = new_world.model_dump(mode='json')
        save_current_state(current_state_dict)
        
        logger.info(f"✅ Successfully injected mod: {safe_mod.mod_name}")
        
        return jsonify({
            "success": True, 
            "message": f"Mod '{safe_mod.mod_name}' safely injected into reality!"
        }), 200

    except ValueError as ve:
        # This catches our Sanitizer/Pydantic rejections!
        error_msg = str(ve)
        logger.error(f"⛔ SANITIZER BLOCKED MOD: {error_msg}")
        return jsonify({"success": False, "message": f"Sanitizer blocked it: {error_msg}"}), 400
    except Exception as e:
        # This catches anything else (like missing columns or network issues)
        error_msg = str(e)
        logger.error(f"❌ CRITICAL INJECTION ERROR: {error_msg}")
        return jsonify({"success": False, "message": f"Critical error: {error_msg}"}), 500

# ==========================================
# DAY 32: THE DYNAMIC QUEST LOG API
# ==========================================
@app.route('/api/quest-log', methods=['GET'])
def get_quest_log():
    """
    Dynamic Quest Log API.

    Query params:
    - project_id: optional project UUID
    - completed: optional comma-separated completed node IDs

    Examples:
    /api/quest-log
    /api/quest-log?completed=node_enter_ruins
    /api/quest-log?project_id=UUID&completed=node_enter_ruins,node_find_signal
    """
    if not QuestDNA or not NarrativeEngine:
        return jsonify({
            "success": False,
            "errors": ["Day 32 Narrative Graph system not available."],
            "quest_id": None,
            "nodes": [],
            "edges": [],
            "active_node_ids": [],
            "completed_node_ids": [],
            "tokens": _quest_log_default_tokens()
        }), 500

    project_id = request.args.get("project_id") or _quest_log_latest_project_id()
    completed_raw = request.args.get("completed", "")
    completed_node_ids = _quest_log_parse_completed_node_ids(completed_raw)

    quest_payload = None

    # --------------------------------------------------
    # 1. Try to read the active QuestDNA from Supabase.
    # --------------------------------------------------
    if supabase and project_id:
        try:
            response = (
                supabase.table("narrative_graphs")
                .select("quest_dna")
                .eq("project_id", project_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                quest_payload = response.data[0].get("quest_dna")

        except Exception as e:
            logger.error(f"Quest Log API could not read narrative_graphs: {e}")

    # --------------------------------------------------
    # 2. Fallback to deterministic demo QuestDNA.
    # --------------------------------------------------
    if not quest_payload:
        quest_payload = _quest_log_demo_dna()

    # --------------------------------------------------
    # 3. Validate QuestDNA through Pydantic.
    # --------------------------------------------------
    try:
        quest = QuestDNA(**quest_payload)
    except Exception as e:
        logger.error(f"QuestDNA validation failed: {e}")

        return jsonify({
            "success": False,
            "errors": [f"QuestDNA validation failed: {e}"],
            "quest_id": None,
            "nodes": [],
            "edges": [],
            "active_node_ids": [],
            "completed_node_ids": completed_node_ids,
            "tokens": _quest_log_default_tokens()
        }), 400

    # --------------------------------------------------
    # 4. Validate DAG and compute active nodes.
    # --------------------------------------------------
    try:
        engine = NarrativeEngine()
        validation = engine.validate_quest_dna(quest)

        if not validation["is_valid"]:
            return jsonify({
                "success": False,
                "errors": validation["errors"],
                "quest_id": quest.quest_id,
                "nodes": [],
                "edges": [],
                "active_node_ids": [],
                "completed_node_ids": completed_node_ids,
                "tokens": _quest_log_default_tokens(),
                "validation": validation
            }), 400

        active_node_ids = engine.get_active_node_ids(
            quest=quest,
            completed_node_ids=completed_node_ids
        )

    except Exception as e:
        logger.error(f"Narrative Engine failed: {e}")

        return jsonify({
            "success": False,
            "errors": [f"Narrative Engine failed: {e}"],
            "quest_id": quest.quest_id,
            "nodes": [],
            "edges": [],
            "active_node_ids": [],
            "completed_node_ids": completed_node_ids,
            "tokens": _quest_log_default_tokens()
        }), 500

    # --------------------------------------------------
    # 5. Serialize UI-safe quest nodes.
    # --------------------------------------------------
    ui_nodes = []

    for node in quest.nodes:
        is_completed = node.node_id in completed_node_ids
        is_active = node.node_id in active_node_ids
        is_locked = (not is_completed) and (not is_active)

        ui_nodes.append({
            "node_id": node.node_id,
            "semantic_concept": node.semantic_concept,
            "completion_condition": node.completion_condition,
            "state_mutations": _quest_log_node_state_mutations(node),
            "is_completed": is_completed,
            "is_active": is_active,
            "is_locked": is_locked
        })

    ui_edges = [
        {
            "from_node": edge.from_node,
            "to_node": edge.to_node
        }
        for edge in quest.edges
    ]

    return jsonify({
        "success": True,
        "quest_id": quest.quest_id,
        "nodes": ui_nodes,
        "edges": ui_edges,
        "active_node_ids": active_node_ids,
        "completed_node_ids": completed_node_ids,
        "tokens": _quest_log_default_tokens(),
        "validation": validation
    })

# ==========================================
# RUN THE SERVER
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)