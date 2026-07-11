import os
import sys
import click
import json
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# ==========================================
# 1. LOAD SECRETS FIRST
# ==========================================
load_dotenv()

# ==========================================
# 2. SETUP PATHS SO WE CAN FIND CORE PACKAGES
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
core_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'packages', 'core'))

if core_path not in sys.path:
    sys.path.insert(0, core_path)

from brain import generate, get_current_context
# NEW IMPORT FOR DAY 9: Bringing in our tree builder!
from graph_engine import render_tree 

# ==========================================
# 3. SETUP CLI & CONNECTIONS
# ==========================================
console = Console()

def get_supabase_client():
    """Safely connects to the Supabase Memory Vault."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        console.print("[bold red]Error: Supabase URL or Key not found in .env![/bold red]")
        return None
    
    from supabase import create_client
    try:
        return create_client(url, key)
    except Exception as e:
        console.print(f"[bold red]Error connecting to Supabase: {e}[/bold red]")
        return None

@click.group()
def cli():
    """Camera AI - The Ontological Genesis Fabric CLI"""
    pass

@cli.command(name="list")
def list_projects():
    """List all saved projects in the Memory Vault."""
    console.print("[bold cyan]Fetching projects from the Memory Vault...[/bold cyan]")
    
    supabase = get_supabase_client()
    if not supabase: return

    try:
        response = supabase.table("projects").select("*").order("created_at", desc=True).execute()
        projects = response.data
        
        if not projects:
            console.print("[yellow]No projects found in the vault. Generate some first![/yellow]")
            return

        table = Table(title="Camera AI - Saved Projects", show_lines=True)
        # Made the ID column wider for the full ID!
        table.add_column("ID", style="dim", width=36)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        
        for p in projects:
            # DAY 9 FIX: Removed the [:8] so we get the FULL ID!
            p_id = str(p.get("id"))
            p_name = p.get("name") or p.get("title") or "Untitled"
            created_at = p.get("created_at")
            p_date = created_at[:10] if created_at else "N/A"
            table.add_row(p_id, p_name, p_date)
            
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error fetching projects:[/bold red] {e}")

@cli.command()
@click.argument("query_string")
def search(query_string):
    """Search for projects by name."""
    console.print(f"[bold cyan]Searching Memory Vault for:[/cyan] [magenta]'{query_string}'[/magenta]")
    
    supabase = get_supabase_client()
    if not supabase: return

    try:
        response = supabase.table("projects").select("*").ilike("name", f"%{query_string}%").execute()
        results = response.data
        
        if not results:
            console.print(f"[yellow]No projects found matching '{query_string}'.[/yellow]")
            return
            
        table = Table(title=f"Search Results for '{query_string}'", show_lines=True)
        table.add_column("ID", style="dim", width=36)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        
        for p in results:
            # DAY 9 FIX: Removed the [:8] so we get the FULL ID!
            p_id = str(p.get("id"))
            p_name = p.get("name") or p.get("title") or "Untitled"
            created_at = p.get("created_at")
            p_date = created_at[:10] if created_at else "N/A"
            table.add_row(p_id, p_name, p_date)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error searching:[/bold red] {e}")

@cli.command(name="generate")
@click.argument("prompt")
@click.option("--name", "-n", default=None, help="Name for the project (optional)")
def run_generate(prompt, name):
    """Generate an ontological graph from a prompt and save to Memory Vault."""
    console.print("[bold cyan]Camera AI is thinking...[/bold cyan]")
    
    result_json = generate(prompt)
    
    if not result_json:
        console.print("[bold red]Error: Brain failed to generate output[/bold red]")
        return
    
    try:
        result_data = json.loads(result_json)
        
        console.print("\n[bold green]✓ Generation Complete![/bold green]")
        console.print(f"[dim]{result_json}[/dim]\n")
        
        supabase = get_supabase_client()
        if supabase:
            project_name = name or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # We save the ENTIRE JSON into our new 'scene_data' box!
            response = supabase.table("projects").insert({
                "name": project_name,
                "description": f"Generated via CLI: {prompt[:50]}...",
                "scene_data": result_data
            }).execute()
            
            if response.data:
                project_id = response.data[0].get("id")
                console.print(f"[bold green]✓ Saved to Memory Vault![/bold green]")
                console.print(f"[dim]Project ID: {project_id}[/dim]")
            else:
                console.print("[yellow]Warning: Generated but failed to save to vault[/yellow]")
        
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error: Invalid JSON from brain: {e}[/bold red]")
        console.print(f"[dim]Raw output: {result_json}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing result: {e}[/bold red]")

# ==========================================
# 4. NEW DAY 9 COMMAND: VIEW THE FRACTAL TREE
# ==========================================
@cli.command(name="view")
@click.argument("project_id")
def view_project(project_id):
    """Visualize the fractal ontology tree for a specific project ID."""
    console.print(f"[bold cyan]Fetching fractal tree for Project ID: {project_id}...[/bold cyan]")
    try:
        render_tree(project_id)
    except Exception as e:
        console.print(f"[bold red]Error rendering tree: {e}[/bold red]")

if __name__ == "__main__":
    cli()