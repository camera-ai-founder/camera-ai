import os
from supabase import create_client
from rich.tree import Tree
from rich.console import Console

# 1. Get our Supabase credentials from the Codespaces environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 2. Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Initialize Rich Console for beautiful terminal printing
console = Console()

def build_tree_from_json(node_data, tree_branch):
    """
    A recursive function that reads the nested JSON and builds the visual tree.
    """
    # Get the name of the node (fallback to 'type' if name is missing)
    name = node_data.get("name") or node_data.get("type") or "Unknown Node"
    
    # Add this node to the current branch of the tree
    branch = tree_branch.add(f"[bold cyan]{name}[/bold cyan]")
    
    # Find the children of this node in the JSON
    children = node_data.get("children", [])
    
    # RECURSION MAGIC: For every child, call this exact same function again!
    for child in children:
        build_tree_from_json(child, branch)

def render_tree(project_id: str):
    """
    Fetches the project's scene_data from Supabase and draws the tree.
    """
    # 1. Fetch the project from the 'projects' table using the ID
    response = supabase.table("projects").select("scene_data, name").eq("id", project_id).execute()
    
    if not response.data:
        console.print("[red]Project not found in Memory Vault![/red]")
        return
        
    project = response.data[0]
    scene_data = project.get("scene_data")
    
    if not scene_data:
        console.print("[yellow]No fractal data (scene_data) found for this project.[/yellow]")
        return
        
    # 2. Create the base (trunk) of the Rich Tree
    project_name = project.get("name") or "Project"
    rich_tree = Tree(f"[bold green]Camera AI: {project_name}[/bold green]")
    
    # 3. Start the recursion!
    # (We check if it's a list or a single object just to be safe)
    if isinstance(scene_data, list):
        for root_node in scene_data:
            build_tree_from_json(root_node, rich_tree)
    else:
        build_tree_from_json(scene_data, rich_tree)
        
    # 4. Print the beautiful branching tree to the terminal!
    console.print(rich_tree)