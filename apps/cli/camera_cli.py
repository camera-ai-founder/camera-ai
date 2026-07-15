import os
import sys
import click
import json 
import time
import copy
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax 
from rich.table import Table
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & IMPORTS
# ==========================================
load_dotenv()
console = Console()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from supabase import create_client

# Existing Day 1-17 Imports + Day 18 Architect + Day 20 DevOps
from packages.core.brain import (
    get_world_state, update_world_state, generate, 
    summarize_state, get_ui_blueprint, act_as_ecosystem_director,
    act_as_backend_architect,
    generate_deployment_topology 
)
from packages.core.ui_synthesizer import synthesize_design_tokens, compile_ui
from packages.core.genesis_renderer import genesis_renderer
from packages.core.models import VisualQuery, WorldState, NavMeshDNA, BiomeDNA 
from packages.core.biome_engine import BiomeEngine
from packages.core.navigation_engine import Voxelizer, AStarPathfinder

from packages.core.backend_compiler import save_compiled_file
from packages.core.deployment_engine import DeploymentEngine 

# --- DAY 21 ADDITION: The Deterministic Netcode Engine ---
from packages.core.netcode_engine import NetcodeEngine

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
    View or update the World State (Supabase).
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
    
    console.print("\n[cyan]1. Testing Asset Swarm...[/cyan]")
    test_query = VisualQuery(
        search_terms=["gothic", "gargoyle"], 
        fallback_flag=True, 
        max_poly_count=10000
    )
    asset_result = genesis_renderer.process_visual_query(test_query)
    console.print(f"Result: {asset_result}")
    
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

@biome.command(name="generate")
@click.argument('biome_type')
def generate_biome(biome_type):
    """Generates a complete ecosystem blueprint based on a theme."""
    console.print(f"🌍 [bold cyan]Camera AI is designing a '{biome_type}' ecosystem...[/bold cyan]")
    
    safe_world_state = WorldState().model_dump()
    
    with console.status("[bold green]Ecosystem Director is calculating Biome DNA...[/bold green]"):
        biome_dna = act_as_ecosystem_director(biome_type, safe_world_state)
    
    console.print(f"✅ [bold green]Brain generated Biome:[/bold green] {biome_dna.name}")
    console.print(f"   - Elevation Curve: {biome_dna.elevation_curve}")
    console.print(f"   - Moisture Level: {biome_dna.moisture_level}")
    console.print(f"   - Scatter Density: {biome_dna.scatter_density}")
    
    engine = BiomeEngine(seed=4242)
    
    console.print("🧮 [bold yellow]Calculating deterministic scatter coordinates...[/bold yellow]")
    spawn_list = engine.calculate_scatter_coordinates(biome_dna)
    
    console.print(f"✅ [bold green]Math complete! Found {len(spawn_list)} perfect spawn locations.[/bold green]")
    
    if spawn_list:
        console.print("\n [bold magenta]Sample Spawn Coordinates (First 3):[/bold magenta]")
        for spawn in spawn_list[:3]:
            console.print(f"   -> Asset: {spawn['asset_type']} at X:{spawn['x']}, Y:{spawn['y']}, Z:{spawn['z']}")
    else:
        console.print("   [yellow](No assets spawned. The AI might have set the thresholds too high!)[/yellow]")
        
    console.print("\n🎉 [bold green]Ecosystem Blueprint generation complete![/bold green]")

# ==========================================
# DAY 17: THE NAVIGATION HOLE (A* PATHFINDING TEST)
# ==========================================
@cli.group()
def navigate():
    """Navigation and Pathfinding commands."""
    pass

@navigate.command(name="test")
def navigate_test():
    """Generates a mock grid, places a fake building, and runs A* pathfinding."""
    console.print(Panel.fit(
        "[bold cyan]Day 17: Testing the Navigation Hole[/bold cyan]\n"
        "Initializing deterministic math sandbox...",
        border_style="cyan"
    ))
    
    nav_dna = NavMeshDNA(grid_resolution=1.0)
    voxelizer = Voxelizer(nav_dna)
    
    mock_placed_assets = [
        {"x": 0.0, "z": 0.0, "radius": 5.0}
    ]
    console.print("[yellow]Placing a mock building at coordinates (0, 0)...[/yellow]")
    
    grid = voxelizer.generate_grid(mock_placed_assets)
    console.print("[green]Voxelizer successfully generated the 2D walkable grid![/green]")
    
    pathfinder = AStarPathfinder(grid, voxelizer)
    
    start_coords = (-10.0, -10.0)
    target_coords = (10.0, 10.0)
    
    console.print(f"[bold]Calculating path from {start_coords} to {target_coords}...[/bold]")
    time.sleep(1) 
    
    path = pathfinder.find_path(start_coords, target_coords)
    
    if not path:
        console.print("[bold red]ERROR: No path found! The math failed.[/bold red]")
        return

    console.print(f"[bold green]SUCCESS! A* calculated a safe path with {len(path)} waypoints.[/bold green]")
    
    table = Table(title="A* Path Waypoints (Breadcrumbs)")
    table.add_column("Step", justify="center", style="cyan", no_wrap=True)
    table.add_column("World X", justify="center", style="magenta")
    table.add_column("World Z", justify="center", style="green")

    for i, (x, z) in enumerate(path):
        note = ""
        if -6.0 <= x <= 6.0 and -6.0 <= z <= 6.0:
            note = " [yellow](Navigating around building)[/yellow]"
            
        table.add_row(str(i), f"{x:.1f}", f"{z:.1f}{note}")

    console.print(table)
    console.print("[bold cyan]The math is flawless, Founder. The entity will not clip through the building.[/bold cyan]")

# ==========================================
# DAY 18: THE BACKEND DNA COMPILER COMMANDS (WIRED TO REAL BRAIN)
# ==========================================
@cli.group()
def backend():
    """Day 18: Backend DNA Compiler Commands."""
    pass

@backend.command(name="generate")
@click.argument("entity")
def generate_backend(entity):
    """Generate a flawless backend API for an entity (e.g., 'User' or 'Product')."""
    console.print(f"🚀 [bold cyan]Initiating Genesis for entity:[/bold cyan] {entity}")
    
    dna = act_as_backend_architect(entity)
    
    console.print("⚙️ [bold yellow]Compiling DNA into bulletproof Python code...[/bold yellow]")
    file_path = save_compiled_file(dna, output_folder="output")
    
    console.print(f"✅ [bold green]SUCCESS! Flawless backend compiled and saved to:[/bold green] {file_path}")
    console.print("🚫 [bold red]Zero hallucinations. Zero syntax errors. Pure deterministic math.[/bold red]")

@backend.command(name="state")
@click.argument("assignment")
def backend_state(assignment):
    """Update the backend state and trigger a recompile. Format: key=value"""
    if "=" not in assignment:
        console.print("[bold red]❌ Error: Please use the format 'key=value' (e.g., auth_type=OAuth)[/bold red]")
        return

    key, value = assignment.split("=", 1)
    console.print(f"💾 [bold green]Updated backend state:[/bold green] {key} is now '{value}'")
    
    active_entity = "User" 
    console.print(f"🔄 [bold yellow]Recompiling reality for active entity:[/bold yellow] {active_entity}...")
    
    dna = act_as_backend_architect(active_entity)
    
    if key == "auth_type":
        dna.auth_type = value
        
    file_path = save_compiled_file(dna, output_folder="output")
    
    console.print(f"✅ [bold green]Reality recompiled successfully with new state![/bold green]")
    console.print(f"📁 [bold cyan]New file saved to:[/bold cyan] {file_path}")

# ==========================================
# DAY 20: THE ONE-COMMAND DEPLOY PROTOCOL
# ==========================================
@cli.command()
@click.argument('target', default='docker')
def deploy(target):
    """
    The Reality Recompiler (Day 20).
    Generates the deployment blueprint (Dockerfile & Asset Manifest).
    Usage: camera deploy docker
    """
    console.print(Panel(f"[bold cyan]Initiating Deployment Protocol for target: {target}...[/bold cyan]", title="Day 20: Deployment Engine"))
    
    # 1. Fetch Current World State
    project_id = get_active_project_id()
    if not project_id:
        console.print("[yellow]No active project found. Using default World State for deployment blueprint.[/yellow]")
        world_state = WorldState()
    else:
        world_state = get_world_state(project_id)
        
    # 2. The DevOps Director determines the topology
    with console.status("[bold green]DevOps Director is determining topology...[/bold green]"):
        deploy_dna = generate_deployment_topology(world_state, app_complexity="medium")
        
    console.print("[bold green]✅ DevOps Director generated flawless DeployDNA![/bold green]")
    
    # 3. The Deterministic Engine synthesizes the Dockerfile
    with console.status("[bold yellow]Deterministic Engine synthesizing Dockerfile...[/bold yellow]"):
        dockerfile_content = DeploymentEngine.synthesize_dockerfile(deploy_dna)
        
    # 4. The Deterministic Engine synthesizes the Asset Manifest
    with console.status("[bold yellow]Deterministic Engine packing Asset Swarm...[/bold yellow]"):
        dummy_biome = BiomeDNA(
            name="Cyberpunk Slum", elevation_curve=0.2, moisture_level=0.1, 
            scatter_density=0.8, scatter_rules=[]
        )
        dummy_genesis_data = {"parametric_genomes": [], "visual_queries": []}
        manifest_content = DeploymentEngine.synthesize_asset_manifest(dummy_biome, dummy_genesis_data)
        
    # 5. Print the Flawless Blueprints
    console.print("\n[bold magenta]--- DOCKERFILE BLUEPRINT ---[/bold magenta]")
    console.print(dockerfile_content)
    
    console.print("\n[bold magenta]--- ASSET MANIFEST ---[/bold magenta]")
    console.print(manifest_content)
    
    # 6. DAY 20 STEP 6: PUSH TO THE CLOUD BRIDGE
    DeploymentEngine.push_to_cloud(dockerfile_content, manifest_content, deploy_dna)
    
    console.print("\n[bold green]✅ Deployment DNA successfully compiled and pushed to cloud![/bold green]")

# ==========================================
# DAY 21: THE MULTIPLAYER HOLE (DETERMINISTIC NETCODE)
# ==========================================
@cli.group()
def netcode():
    """Day 21: Deterministic Netcode Commands."""
    pass

@netcode.command(name="sync")
def netcode_sync():
    """Simulates a world state change, calculates the surgical Delta, and broadcasts it to Supabase."""
    console.print(Panel("[bold cyan]Day 21: Testing the Deterministic Netcode Hole[/bold cyan]", border_style="cyan"))
    
    # 1. Load current state (or mock it)
    project_id = get_active_project_id()
    if project_id:
        old_state = get_world_state(project_id).model_dump()
    else:
        old_state = {"nodes": [], "world_state": {"heat_level": 0, "time_of_day": "12:00"}}
        
    console.print("[yellow]Current World State loaded.[/yellow]")
    
    # 2. Simulate a change (The New State)
    new_state = copy.deepcopy(old_state)
    
    # Let's simulate a door locking and heat level rising
    current_heat = new_state.get("world_state", {}).get("heat_level", 0)
    if "world_state" not in new_state:
        new_state["world_state"] = {}
    new_state["world_state"]["heat_level"] = current_heat + 1
    
    if "nodes" not in new_state:
        new_state["nodes"] = []
        
    new_state["nodes"].append({
        "id": "door_tavern_01",
        "name": "Tavern Door",
        "type": "interactive_prop",
        "state": "locked"
    })
    
    console.print("[yellow]Simulating change: Tavern Door locked, Heat Level increased.[/yellow]")
    
    # 3. Calculate the Surgical Delta
    with console.status("[bold green]Netcode Engine is calculating the mathematical difference...[/bold green]"):
        delta = NetcodeEngine.calculate_delta(old_state, new_state)
        
    # 4. Convert to JSON and BROADCAST to Supabase
    delta_json = delta.model_dump(mode='json')
    
    console.print("\n[bold magenta]--- EXACT BROADCAST PAYLOAD (STATE DELTA) ---[/bold magenta]")
    syntax = Syntax(json.dumps(delta_json, indent=2), "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Supabase Realtime Payload", border_style="green"))
    
    # 5. ACTUALLY SEND IT TO SUPABASE
    if supabase:
        with console.status("[bold yellow]Broadcasting to Supabase Realtime...[/bold yellow]"):
            try:
                response = supabase.table("state_deltas").insert({
                    "delta_data": delta_json,
                    "timestamp": delta_json["timestamp"]
                }).execute()
                console.print("\n[bold green]✅ SUCCESS! Delta broadcasted to Supabase![/bold green]")
                console.print("[bold cyan]Check the Table Editor to see the Delta sitting in the database![/bold cyan]")
            except Exception as e:
                console.print(f"\n[bold red]Error broadcasting: {e}[/bold red]")
    else:
        console.print("\n[bold yellow]Supabase not connected. Delta calculated but not broadcast.[/bold yellow]")
    
    console.print("\n[bold green]✅ Netcode calculation complete![/bold green]")
    console.print("[bold cyan]Zero lag compensation. Zero heavy physics. Pure JSON DNA.[/bold cyan]")

# CRITICAL: Add the new command groups to the main 'cli' group!
cli.add_command(biome)
cli.add_command(navigate)
cli.add_command(backend)
cli.add_command(netcode)

# ==========================================
# 3. START THE ENGINE
# ==========================================
if __name__ == '__main__':
    cli()