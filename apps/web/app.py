import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from supabase import create_client, Client

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)