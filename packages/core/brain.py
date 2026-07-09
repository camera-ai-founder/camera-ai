import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from groq import Groq
from supabase import create_client, Client

# CRITICAL FIX: Load .env from the root folder, no matter where we run the code from!
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. Pydantic Models (The Blueprint for Camera AI)
class OntologicalNode(BaseModel):
    id: str = Field(description="Unique identifier for the node")
    label: str = Field(description="The main name or label of the concept")
    description: str = Field(description="A brief description of the concept")

class OntologicalEdge(BaseModel):
    source: str = Field(description="The ID of the source node")
    target: str = Field(description="The ID of the target node")
    relationship: str = Field(description="How the source connects to the target")

class OntologicalGraph(BaseModel):
    nodes: List[OntologicalNode]
    edges: List[OntologicalEdge]

# 2. Initialize Cloud Connections
groq_api_key = os.getenv("GROQ_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
# Check for standard key or default Supabase 'anon' key
supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not groq_api_key:
    raise ValueError("Missing GROQ_API_KEY! Check your root .env file.")
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase keys! Check your root .env file.")
    
client = Groq(api_key=groq_api_key)
supabase: Client = create_client(supabase_url, supabase_key)

# 3. The Core Brain Function
def generate_ontology(prompt: str) -> OntologicalGraph:
    """Connects to Groq, forces JSON, and saves to Supabase."""
    
    # Format the schema nicely as a string so the AI understands it better
    schema_str = json.dumps(OntologicalGraph.model_json_schema(), indent=2)
    
    system_prompt = """You are Camera AI, an expert ontological engineer. 
    You must output ONLY valid JSON. The JSON must be an object with two keys: "nodes" and "edges".
    CRITICAL: DO NOT output the schema definition or the blueprint. You must generate ACTUAL DATA instances that follow the schema.
    Do not include Markdown formatting like ```json. Just the raw JSON string."""
    
    user_prompt = f"Generate an ontology for: {prompt}.\n\nFollow this schema strictly:\n{schema_str}"

    # Groq AI Generation
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"} # Forces Groq to output pure JSON
    )
    
    raw_json = completion.choices[0].message.content
    
    # Parse the AI's response into our strict Pydantic models
    graph_data = OntologicalGraph.model_validate_json(raw_json)
    
    # Save to Supabase (with a safety net!)
    try:
        nodes_to_save = [node.model_dump() for node in graph_data.nodes]
        edges_to_save = [edge.model_dump() for edge in graph_data.edges]
        
        if nodes_to_save:
            supabase.table("nodes").insert(nodes_to_save).execute()
        if edges_to_save:
            supabase.table("edges").insert(edges_to_save).execute()
            
        print("✅ Camera AI successfully saved data to Supabase!")
    except Exception as e:
        print(f"⚠️ Supabase save skipped (Check your table columns): {e}")
        
    return graph_data