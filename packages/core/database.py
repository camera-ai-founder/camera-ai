import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Camera AI: Load secret keys from the .env file
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    raise ValueError("Camera AI: Error! Missing Supabase credentials in the .env file.")

# Camera AI: Connect to the Memory Vault
supabase: Client = create_client(url, key)

def save_project(name: str, description: str, graph_data: dict = None):
    """Camera AI: Save a new project to the Memory Vault."""
    if graph_data is None:
        graph_data = {}
    
    payload = {
        "name": name,
        "description": description,
        "graph_data": graph_data
    }
    
    response = supabase.table("projects").insert(payload).execute()
    print(f"Camera AI: Saved project '{name}' to the Memory Vault!")
    return response.data

def get_project(name: str):
    """Camera AI: Retrieve a specific project by its name."""
    response = supabase.table("projects").select("*").eq("name", name).execute()
    return response.data

def list_projects():
    """Camera AI: List all saved projects in the Memory Vault."""
    response = supabase.table("projects").select("id, name, created_at").order("created_at", desc=True).execute()
    return response.data