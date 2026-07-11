import os
from supabase import create_client
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Connect to Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

print(" Creating Cyberpunk City in Supabase...")

# Define the hierarchy
cyberpunk_data = {
    "Cyberpunk City": {
        "description": "A futuristic city with a dystopian atmosphere",
        "children": {
            "Corporate District": {
                "description": "The financial and business hub",
                "children": {
                    "NeoCorp Tower": {
                        "description": "Headquarters of a powerful corporation",
                        "children": {
                            "Executive Office": {"description": "The CEO's office"},
                            "Research Lab": {"description": "Cutting-edge research facility"}
                        }
                    }
                }
            },
            "Street Market": {
                "description": "Bustling marketplace with vendors",
                "children": {
                    "Food Stalls": {
                        "description": "Various food vendors",
                        "children": {
                            "Sushi Bar": {"description": "A small sushi bar"}
                        }
                    }
                }
            },
            "Gaming Zone": {
                "description": "Virtual reality gaming area",
                "children": {
                    "VR Arcade": {"description": "Virtual reality arcade"},
                    "Neon Lounge": {"description": "Gaming lounge with neon lights"}
                }
            }
        }
    }
}

def insert_nodes(data, parent_id=None):
    """Recursively insert nodes into Supabase"""
    nodes_created = 0
    
    for name, info in data.items():
        node_id = str(uuid.uuid4())
        
        node = {
            "id": node_id,
            "label": name,
            "description": info.get("description", ""),
            "parent_id": parent_id
        }
        
        supabase.table("nodes").insert(node).execute()
        print(f"  ✓ {name}")
        nodes_created += 1
        
        # Insert children if they exist
        if "children" in info:
            nodes_created += insert_nodes(info["children"], node_id)
    
    return nodes_created

# Insert the root node
total = insert_nodes(cyberpunk_data)
print(f"\n🎉 SUCCESS! Created {total} nodes in Supabase!")
print("Now refresh your web browser to see the graph!")