import os
import sys
import click
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & IMPORTS
# ==========================================
load_dotenv()
console = Console()

# This magic line allows our CLI to look backwards into the 'packages' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the Supabase connection and our Brain functions
from supabase import create_client
from packages.core.brain import get_world_state, update_world_state, generate

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

def get_active_project_id():
    """Finds the ID of the most recently created project."""
    if not supabase:
        return None
    try:
        response = supabase.table("projects").select("id").order("created_at", desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
    except Exception as e:
        console.print(f"[red]Error finding project: {e}[/red]")
    return None

# ==========================================
# 2. THE CLI BUTTONS (Click Library)
# ==========================================
@click.group()
def cli():
    """Camera AI: The Ontological Genesis Fabric CLI."""
    pass

@cli.command()
@click.argument('prompt', required=False)
def gen(prompt):
    """Generate a new fractal world. (e.g., camera gen 'build a neon city')"""
    if not prompt:
        prompt = "Generate a cyberpunk city district"
    
    with console.status("[bold green]Camera AI is thinking...[/bold green]"):
        result = generate(prompt)
        
    if result:
        console.print(Panel(result, title="[bold]Generated Fractal JSON[/bold]", border_style="green"))

@cli.command()
@click.argument('action', required=False)
@click.argument('key', required=False)
@click.argument('value', required=False)
def state(action, key, value):
    """
    View or update the World State.
    Usage: 'camera state' (to view) or 'camera state set heat_level 5' (to update)
    """
    project_id = get_active_project_id()
    if not project_id:
        console.print("[bold red]No project found in Supabase! Please create a project first.[/bold red]")
        return

    # If they just type "camera state", show the current state
    if not action:
        current_state = get_world_state(project_id)
        info = f"[bold]Heat Level:[/bold] {current_state.heat_level}/5\n[bold]Time of Day:[/bold] {current_state.time_of_day}"
        console.print(Panel(info, title="[bold blue]Current World State[/bold blue]", border_style="blue"))
        return

    # If they type "camera state set heat_level 5"
    if action.lower() == 'set' and key and value:
        # Try to convert the value to an integer if it's a number (like 5)
        try:
            value = int(value)
        except ValueError:
            pass # Keep it as text if it's not a number (like "Night")

        changes = {key: value}
        update_world_state(project_id, changes)
        console.print(f"[bold green]Successfully updated {key} to {value}![/bold green]")
    else:
        console.print("[yellow]Invalid command. Use 'camera state' to view, or 'camera state set key value' to update.[/yellow]")

# ==========================================
# 3. START THE ENGINE
# ==========================================
if __name__ == '__main__':
    cli()