import os
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

# --- 0. LOAD THE .ENV FILE ---
load_dotenv()

# --- SET UP LOGGING ---
logging.basicConfig(level=logging.INFO)
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
    """
    Runs in a separate thread. Writes telemetry to Supabase
    without freezing the main Flask request thread.
    """
    if not supabase:
        return
    try:
        supabase.table("telemetry_logs").insert(report_data).execute()
        logger.info("📦 Black Box: Telemetry report saved successfully.")
    except Exception as e:
        logger.error(f"Black Box write failed: {e}")

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
    """Fetches Camera AI ontology nodes and formats them for the web visualizer."""
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
        
        if parent_id is not None and parent_id != 'null' and parent_id != '':
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
    """Receives the ImpactVector JSON, calculates the narrative, and sends it back."""
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
    """Receives state from the CLI and broadcasts it via Supabase Realtime."""
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
        return jsonify({
            "status": "error", 
            "message": f"Could not broadcast. Please ensure the 'live_canvas_state' table exists in Supabase. Error: {str(e)}"
        }), 500

# ==========================================
# 7. DAY 21: DETERMINISTIC NETCODE BROADCAST
# ==========================================
@app.route('/api/update_state', methods=['POST'])
def update_state():
    """
    THE REALTIME DELTA BROADCAST HOOK.
    Calculates the surgical Delta using pure math,
    then broadcasts ONLY the Delta via Supabase Realtime.
    """
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
            "changed_nodes_count": len(delta_payload["changed_nodes"]),
            "changed_tokens_count": len(delta_payload["changed_tokens"]),
            "removed_nodes_count": len(delta_payload["removed_node_ids"])
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Could not broadcast delta. Error: {str(e)}"
        }), 500

# ==========================================
# 8. DAY 23: TELEMETRY BLACK BOX ENDPOINTS
# ==========================================
@app.route('/api/telemetry/report', methods=['POST'])
def receive_telemetry_report():
    """
    The endpoint the frontend Profiler calls when FPS drops.
    Validates the report, saves to Black Box in background, 
    and immediately responds without blocking.
    """
    if not PerformanceReport:
        return jsonify({"status": "error", "message": "Telemetry models not available"}), 500

    try:
        raw_json = request.json
        report = PerformanceReport.model_validate(raw_json)
        
        logger.info(f"🚨 Telemetry Received: FPS {report.current_fps} | Bottleneck: {report.bottleneck_component}")

        # Fire and forget: Send to the Black Box in a background thread
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
    """
    Endpoint for the CLI (Step 6) to pull the last 5 performance reports.
    """
    if not supabase:
        return jsonify({"error": "Black Box offline"}), 500
        
    try:
        response = supabase.table("telemetry_logs").select("*").order("created_at", desc=True).limit(5).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telemetry/heal', methods=['POST'])
def trigger_ai_healing():
    """
    The full self-healing endpoint. Receives a performance report,
    asks the AI Brain to downgrade the DNA, and returns the healed DNA.
    """
    if not PerformanceReport or not telemetry_brain or not AppDNA:
        return jsonify({"status": "error", "message": "AI Healing system not available"}), 500

    try:
        raw_json = request.json
        report = PerformanceReport.model_validate(raw_json)
        
        # Load the current master DNA
        current_dna = AppDNA()  # In production, load from DB or OGF_STATE.json
        
        # Ask the AI Brain to heal
        healed_dna = telemetry_brain.heal_dna(report, current_dna)
        
        return jsonify({
            "status": "healed",
            "healed_dna": healed_dna.model_dump(mode='json')
        }), 200

    except Exception as e:
        logger.error(f"AI Healing failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# RUN THE SERVER
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)