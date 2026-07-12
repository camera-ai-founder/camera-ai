import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client

# --- DAY 12 IMPORTS: The Juice Engine & Brain ---
from packages.core.models import ImpactVector, JuiceProfile
from packages.core import brain

# --- 0. LOAD THE .ENV FILE ---
load_dotenv()

# --- 1. SETUP SUPABASE ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# --- 2. SETUP FLASK ---
app = Flask(__name__)

# --- 3. MAIN WEB PAGE ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 4. API ROUTE FOR CYTOSCAPE ---
@app.route('/api/graph')
def get_graph_data():
    """Fetches Camera AI ontology nodes and formats them for the web visualizer."""
    
    # Fetch all nodes from Supabase
    response = supabase.table('nodes').select('*').execute()
    all_nodes = response.data

    cy_nodes = []
    cy_edges = []
    edges_created = 0

    for node in all_nodes:
        node_label = node.get('label', 'Node')
        parent_id = node.get('parent_id')

        # Add the node
        cy_nodes.append({
            "data": {
                "id": str(node['id']),
                "label": str(node_label)
            }
        })
        
        # Check if parent_id exists and is not null/None/empty
        if parent_id is not None and parent_id != 'null' and parent_id != '':
            edges_created += 1
            cy_edges.append({
                "data": {
                    "source": str(parent_id),
                    "target": str(node['id'])
                }
            })

    # Return data PLUS debug info
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
    """
    Receives the ImpactVector JSON, calculates the narrative, and sends it back.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # 1. Rebuild our Pydantic models from the incoming JSON
    impact_vector = ImpactVector(**data.get('impact_vector', {}))
    juice = JuiceProfile(
        impact_type=data.get('impact_type', 'default'),
        ragdoll_decay=data.get('ragdoll_decay', 0.5),
        impact_vector=impact_vector
    )

    # 2. Ask our AI brain to generate the cinematic narrative!
    narrative = brain.generate_narrative_impact(juice, object_name="the target")

    # 3. Send the math and the story back to the browser
    return jsonify({
        "status": "success",
        "narrative": narrative,
        "vector": impact_vector.model_dump(),
        "decay": juice.ragdoll_decay
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)