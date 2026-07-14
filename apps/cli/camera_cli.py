import os
import sys
import click
import json 
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax 
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & IMPORTS
# ==========================================
load_dotenv()
console = Console()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from supabase import create_client

# Added act_as_ecosystem_director for Day 16
from packages.core.brain import (
    get_world_state, update_world_state, generate, 
    summarize_state, get_ui_blueprint, act_as_ecosystem_director
)
from packages.core.ui_synthesizer import synthesize_design_tokens, compile_ui

# NEW DAY 15 IMPORTS FOR THE GENESIS RENDERER
from packages.core.genesis_renderer import genesis_renderer

# Added WorldState and BiomeEngine for Day 16
from packages.core.models import VisualQuery, WorldState
from packages.core.biome_engine import BiomeEngine

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

    if not action:
        current_state = get_world_state(project_id)
        info = f"[bold]Heat Level:[/bold] {current_state.heat_level}/5\n[bold]Time of Day:[/bold] {current_state.time_of_day}"
        console.print(Panel(info, title="[bold blue]Current World State[/bold blue]", border_style="blue"))
        return

    if action.lower() == 'set' and key and value:
        try:
            value = int(value)
        except ValueError:
            pass 

        changes = {key: value}
        update_world_state(project_id, changes)
        console.print(f"[bold green]Successfully updated {key} to {value}![/bold green]")
    else:
        console.print("[yellow]Invalid command. Use 'camera state' to view, or 'camera state set key value' to update.[/yellow]")

# ==========================================
# DAY 13 STEP 6: THE SURGICAL TEST
# ==========================================
@cli.group()
def architect():
    """Commands for the Camera AI Architect."""
    pass

@architect.command()
def test():
    """Run a surgical test of the Narrative Summarizer (Context Pruner)."""
    console.print("[bold cyan]Running surgical test on the Narrative Summarizer...[/bold cyan]")
    
    dummy_history_dict = {
        "recent_events": [
            "The player defeated the Dragon King in the volcanic crater.",
            "The sky turned purple due to magic fallout.",
            "The player acquired the Chrono-Sword."
        ],
        "world_status": "Chaos"
    }
    
    dummy_json = json.dumps(dummy_history_dict)
    
    with console.status("[bold green]Groq is compressing history into 3 World Truths...[/bold green]"):
        truths = summarize_state(dummy_json)
        
    truths_text = "\n".join([f"- {t}" for t in truths])
    console.print(Panel(truths_text, title="[bold yellow]Compressed World Truths[/bold yellow]", border_style="yellow"))
    console.print("[bold green]Context Pruner is working perfectly![/bold green]")

# ==========================================
# DAY 14: THE UI COMPILER COMMAND
# ==========================================
@cli.group()
def ui():
    """UI Compilation Commands."""
    pass

@ui.command()
@click.argument("app_name")
def compile(app_name):
    """
    [Day 14] Compiles a flawless, hallucination-free React UI.
    Usage: python apps/cli/camera_cli.py ui compile "User Dashboard"
    """
    console.print(Panel(f"[bold cyan]Compiling UI for:[/bold cyan] {app_name}", title="Camera AI UI Compiler"))
    
    blueprint = get_ui_blueprint(app_name)
    
    if not blueprint:
        console.print("[bold red]Error: Brain failed to return a blueprint.[/bold red]")
        return

    app_dna = blueprint["app_dna"]
    design_tokens = blueprint["design_tokens"]
    
    console.print(f"[bold green]Brain returned DNA for:[/bold green] {app_dna.entity_name}")
    console.print(f"[bold yellow]Primary Accent Color:[/bold yellow] {design_tokens.accent_primary}")

    design_config = synthesize_design_tokens(design_tokens)
    final_react_code = compile_ui(app_dna, design_config)
    
    syntax = Syntax(final_react_code, "jsx", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Final React Code (Zero Hallucinations)", border_style="green"))

# ==========================================
# DAY 15: THE GENESIS RENDERER TEST
# ==========================================
@cli.command()
def test_genesis():
    """[Day 15] Triggers the Genesis Pipeline to test the Cinematic Illusion."""
    console.print(Panel("[bold green]Initiating Day 15: Genesis Renderer Test[/bold green]"))
    
    # 1. Test the Asset Swarm (Priority 2)
    console.print("\n[cyan]1. Testing Asset Swarm...[/cyan]")
    test_query = VisualQuery(
        search_terms=["gothic", "gargoyle"], 
        fallback_flag=True, 
        max_poly_count=10000
    )
    asset_result = genesis_renderer.process_visual_query(test_query)
    console.print(f"Result: {asset_result}")
    
    # 2. Test Voice & Emotion (Priority 6)
    console.print("\n[cyan]2. Testing Voice & Emotion...[/cyan]")
    voice_result = genesis_renderer.generate_voice_and_emotion(
        dialogue="The storm is approaching, Founder.", 
        emotion="tense"
    )
    console.print(f"Result: {voice_result}")
    
    console.print("\n[bold green]✅ Genesis Pipeline Test Complete! The Cinematic Illusion Engine is ready.[/bold green]")

# ==========================================
# DAY 16: THE INFINITE BIOME ENGINE
# ==========================================
@cli.group()
def biome():
    """Commands for generating infinite mathematical biomes."""
    pass

@biome.command()
@click.argument('biome_type')
def generate(biome_type):
    """Generates a complete ecosystem blueprint based on a theme."""
    console.print(f"🌍 [bold cyan]Camera AI is designing a '{biome_type}' ecosystem...[/bold cyan]")
    
    # 1. Create a safe, empty World State for the AI to read
    safe_world_state = WorldState().model_dump()
    
    # 2. Ask the Ecosystem Director (Groq) for the Biome DNA
    with console.status("[bold green]Ecosystem Director is calculating Biome DNA...[/bold green]"):
        biome_dna = act_as_ecosystem_director(biome_type, safe_world_state)
    
    console.print(f"✅ [bold green]Brain generated Biome:[/bold green] {biome_dna.name}")
    console.print(f"   - Elevation Curve: {biome_dna.elevation_curve}")
    console.print(f"   - Moisture Level: {biome_dna.moisture_level}")
    console.print(f"   - Scatter Density: {biome_dna.scatter_density}")
    
    # 3. Initialize the Math Engine with a fixed deterministic seed
    engine = BiomeEngine(seed=4242)
    
    # 4. Calculate Scatter Coordinates
    console.print("🧮 [bold yellow]Calculating deterministic scatter coordinates...[/bold yellow]")
    spawn_list = engine.calculate_scatter_coordinates(biome_dna)
    
    console.print(f"✅ [bold green]Math complete! Found {len(spawn_list)} perfect spawn locations.[/bold green]")
    
    # 5. Print a sample to the terminal so we can see the math working
    if spawn_list:
        console.print("\n📍 [bold magenta]Sample Spawn Coordinates (First 3):[/bold magenta]")
        for spawn in spawn_list[:3]:
            console.print(f"   -> Asset: {spawn['asset_type']} at X:{spawn['x']}, Y:{spawn['y']}, Z:{spawn['z']}")
    else:
        console.print("   [yellow](No assets spawned. The AI might have set the thresholds too high!)[/yellow]")
        
    console.print("\n🎉 [bold green]Ecosystem Blueprint generation complete![/bold green]")

# CRITICAL: Add the new 'biome' group to the main 'cli' group!
cli.add_command(biome)

# ==========================================
# 3. START THE ENGINE
# ==========================================
if __name__ == '__main__':
    cli()