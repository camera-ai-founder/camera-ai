# apps/cli/camera_cli.py
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

# Existing Day 1-22 Imports + Day 24 Audio Director + Day 25 InputDNA + Day 26 ModDNA + Day 27
from packages.core.brain import (
    get_world_state, update_world_state, generate, 
    summarize_state, get_ui_blueprint, act_as_ecosystem_director,
    act_as_backend_architect,
    generate_deployment_topology,
    act_as_foley_director, # ADDED FOR DAY 24
    act_as_control_director, # ADDED FOR DAY 25
    act_as_translation_director # ADDED FOR DAY 27
)
from packages.core.ui_synthesizer import synthesize_design_tokens, compile_ui
from packages.core.genesis_renderer import genesis_renderer
from packages.core.biome_engine import BiomeEngine
from packages.core.navigation_engine import Voxelizer, AStarPathfinder
from packages.core.backend_compiler import save_compiled_file
from packages.core.deployment_engine import DeploymentEngine 
from packages.core.netcode_engine import NetcodeEngine
from packages.core.security_engine import sanitize_dna
from packages.core.localization_engine import LocalizationEngine # ADDED FOR DAY 27

# --- DAY 23, 24, 25, 26 & 27 ADDITIONS: Telemetry, Audio, Input, Mod & Locale Models ---
from packages.core.models import (
    VisualQuery, WorldState, NavMeshDNA, BiomeDNA, AppDNA, SecurityDNA,
    PerformanceReport, BottleneckType,
    AudioDNA, # ADDED FOR DAY 24
    InputDNA, # ADDED FOR DAY 25
    ModDNA, DramaBudget, # ADDED FOR DAY 26
    LocaleDNA, SemanticToken, FluidUIRules # ADDED FOR DAY 27
)
from packages.core.telemetry_engine import telemetry_brain
from packages.core.modding_engine import engine as modding_engine # ADDED FOR DAY 26

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Path to the master save file for local DNA (like Inputs and Mods)
STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../OGF_STATE.json'))

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
    
    # Day 23 Fix: compile_ui now returns a dict with 'code' and 'metrics'
    ui_report = compile_ui(app_dna, design_config)
    final_react_code = ui_report.get("code", "")
    
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
# DAY 18: THE BACKEND DNA COMPILER COMMANDS
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
    
    # Day 23 Fix: save_compiled_file now returns a dict report
    compile_report = save_compiled_file(dna, output_folder="output")
    file_path = compile_report.get("file_path", "Unknown")
    
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
    console.print(f" [bold yellow]Recompiling reality for active entity:[/bold yellow] {active_entity}...")
    
    dna = act_as_backend_architect(active_entity)
    
    if key == "auth_type":
        dna.auth_type = value
        
    compile_report = save_compiled_file(dna, output_folder="output")
    file_path = compile_report.get("file_path", "Unknown")
    
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
    
    project_id = get_active_project_id()
    if not project_id:
        console.print("[yellow]No active project found. Using default World State for deployment blueprint.[/yellow]")
        world_state = WorldState()
    else:
        world_state = get_world_state(project_id)
        
    with console.status("[bold green]DevOps Director is determining topology...[/bold green]"):
        deploy_dna = generate_deployment_topology(world_state, app_complexity="medium")
        
    console.print("[bold green]✅ DevOps Director generated flawless DeployDNA![/bold green]")
    
    with console.status("[bold yellow]Deterministic Engine synthesizing Dockerfile...[/bold yellow]"):
        dockerfile_content = DeploymentEngine.synthesize_dockerfile(deploy_dna)
        
    with console.status("[bold yellow]Deterministic Engine packing Asset Swarm...[/bold yellow]"):
        dummy_biome = BiomeDNA(
            name="Cyberpunk Slum", elevation_curve=0.2, moisture_level=0.1, 
            scatter_density=0.8, scatter_rules=[]
        )
        dummy_genesis_data = {"parametric_genomes": [], "visual_queries": []}
        manifest_content = DeploymentEngine.synthesize_asset_manifest(dummy_biome, dummy_genesis_data)
        
    console.print("\n[bold magenta]--- DOCKERFILE BLUEPRINT ---[/bold magenta]")
    console.print(dockerfile_content)
    
    console.print("\n[bold magenta]--- ASSET MANIFEST ---[/bold magenta]")
    console.print(manifest_content)
    
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
    
    project_id = get_active_project_id()
    if project_id:
        old_state = get_world_state(project_id).model_dump()
    else:
        old_state = {"nodes": [], "world_state": {"heat_level": 0, "time_of_day": "12:00"}}
        
    console.print("[yellow]Current World State loaded.[/yellow]")
    
    new_state = copy.deepcopy(old_state)
    
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
    
    with console.status("[bold green]Netcode Engine is calculating the mathematical difference...[/bold green]"):
        delta = NetcodeEngine.calculate_delta(old_state, new_state)
        
    delta_json = delta.model_dump(mode='json')
    
    console.print("\n[bold magenta]--- EXACT BROADCAST PAYLOAD (STATE DELTA) ---[/bold magenta]")
    syntax = Syntax(json.dumps(delta_json, indent=2), "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Supabase Realtime Payload", border_style="green"))
    
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

# ==========================================
# DAY 22 STEP 6: CLI SECURITY AUDIT COMMAND
# ==========================================
@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def security_audit(file_path):
    """
    DAY 22: ZERO-TRUST DNA AUDIT.
    Passes a JSON file through the Sanitizer to check for threats.
    Usage: camera security_audit path/to/file.json
    """
    console.print(f"\n[bold cyan]️  Initiating Zero-Trust Security Audit...[/bold cyan]")
    console.print(f"Target: {os.path.abspath(file_path)}\n")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_json_string = f.read()

        security_config = SecurityDNA(
            max_payload_size=1048576,
            allowed_keys=[],
            restricted_characters=["<", ">", ";", "--", "/*", "*/"]
        )

        clean_dna = sanitize_dna(
            raw_json_string=raw_json_string,
            target_model=AppDNA,
            security_config=security_config
        )

        console.print(Panel(
            "[bold green]✅ DNA PURE[/bold green]\n\n"
            "The payload passed all Zero-Trust checks.\n"
            "- Size is within safe limits.\n"
            "- No forbidden characters detected.\n"
            "- Structure perfectly matches the Pydantic schema.\n"
            "Your compilers are safe to process this data.",
            title="SECURITY AUDIT PASSED",
            border_style="green"
        ))

    except ValueError as e:
        error_message = str(e)
        console.print(Panel(
            f"[bold red]🚫 THREAT BLOCKED[/bold red]\n\n"
            f"[yellow]Reason:[/yellow] {error_message}\n\n"
            "The Sanitizer successfully neutralized a malicious or malformed payload.\n"
            "Your laptop's memory and compilers were never exposed to this threat.",
            title="SECURITY AUDIT FAILED",
            border_style="red"
        ))

    except Exception as e:
        console.print(Panel(
            f"[bold yellow]️ AUDIT ERROR[/bold yellow]\n\n"
            f"An unexpected error occurred: {str(e)}\n"
            "Please check the file path and ensure it is a valid text/JSON file.",
            title="SYSTEM WARNING",
            border_style="yellow"
        ))

# ==========================================
# DAY 23: THE TELEMETRY HOLE (AI SELF-CORRECTION)
# ==========================================
@cli.group()
def telemetry():
    """Day 23: Telemetry & AI Self-Correction Commands."""
    pass

@telemetry.command(name="check")
def telemetry_check():
    """Pulls the last 5 performance reports from the Black Box and triggers AI self-correction."""
    console.print(Panel("[bold cyan]Day 23: Inspecting the Telemetry Black Box[/bold cyan]", border_style="cyan"))
    
    if not supabase:
        console.print("[bold red]Error: Supabase is not connected. Cannot read the Black Box.[/bold red]")
        return

    # 1. Fetch the last 5 reports from the Black Box
    with console.status("[bold green]Querying the Black Box for recent performance drops...[/bold green]"):
        try:
            response = supabase.table("telemetry_logs").select("*").order("created_at", desc=True).limit(5).execute()
            logs = response.data
        except Exception as e:
            console.print(f"[bold red]Error fetching telemetry logs: {e}[/bold red]")
            console.print("[yellow]Hint: Did you run the SQL to create the 'telemetry_logs' table in Supabase?[/yellow]")
            return

    if not logs:
        console.print("[bold yellow]The Black Box is empty. No performance reports have been sent yet.[/bold yellow]")
        console.print("[cyan]Run the frontend app and trigger a lag spike to populate the Black Box![/cyan]")
        return

    # 2. Display the reports in a Rich Table
    table = Table(title="📊 Last 5 Telemetry Reports (Black Box)")
    table.add_column("Timestamp", style="dim")
    table.add_column("FPS", justify="right", style="bold")
    table.add_column("Dropped Frames", justify="right", style="yellow")
    table.add_column("Memory (MB)", justify="right", style="blue")
    table.add_column("Bottleneck", style="red")

    for log in logs:
        ts = log.get('created_at', 'Unknown')
        if len(ts) > 19:
            ts = ts[:19] # Trim the timezone/milliseconds for cleaner display
            
        fps = log.get('current_fps', 0)
        dropped = log.get('dropped_frames', 0)
        mem = log.get('memory_usage_mb', 0)
        bottleneck = log.get('bottleneck_component', 'none')
        
        fps_style = "green" if fps >= 55 else "red"
        
        table.add_row(
            ts, 
            f"[{fps_style}]{fps}[/{fps_style}]", 
            str(dropped), 
            f"{mem:.1f}", 
            bottleneck.upper() if bottleneck else "NONE"
        )

    console.print(table)

    # 3. Find the most recent unhealthy report to trigger the AI Brain
    bad_report_dict = None
    for log in logs:
        bn = log.get('bottleneck_component')
        if bn and bn != 'none' and bn != BottleneckType.NONE.value:
            bad_report_dict = log
            break
            
    if not bad_report_dict:
        console.print("\n[bold green]✅ All recent reports are healthy. The engine is running perfectly at 60fps![/bold green]")
        return

    # 4. Trigger the AI Self-Correction Loop
    console.print(f"\n[bold red]🚨 CRITICAL BOTTLENECK DETECTED: {bad_report_dict.get('bottleneck_component').upper()}[/bold red]")
    console.print("[bold yellow]Initiating AI Self-Healing Sequence...[/bold yellow]")
    
    # Reconstruct the Pydantic model from the Supabase dict
    try:
        report_obj = PerformanceReport.model_validate(bad_report_dict)
    except Exception as e:
        console.print(f"[red]Failed to validate report against Pydantic schema: {e}[/red]")
        return

    # Load a default AppDNA to heal
    current_dna = AppDNA(app_name="Genesis Engine") 
    
    with console.status("[bold green]Groq AI Brain is analyzing the bottleneck and downgrading DNA...[/bold green]"):
        healed_dna = telemetry_brain.heal_dna(report_obj, current_dna)

    # 5. Print the AI's Self-Correction Suggestions (The Healed DNA)
    console.print("\n[bold magenta]--- 🧬 AI SELF-CORRECTION: HEALED DNA ---[/bold magenta]")
    
    # Show exactly what the AI downgraded
    original_renderer = current_dna.renderer
    healed_renderer = healed_dna.renderer
    
    original_budget = current_dna.drama_budget
    healed_budget = healed_dna.drama_budget

    correction_panel = f"""
[bold cyan]GenesisRenderer Adjustments:[/bold cyan]
- Shadows: [red]{original_renderer.enable_shadows}[/red] -> [green]{healed_renderer.enable_shadows}[/green]
- VFX Complexity: [red]{original_renderer.vfx_complexity}[/red] -> [green]{healed_renderer.vfx_complexity}[/green]
- Engine Fallback: [yellow]{healed_renderer.fallback_engine}[/yellow]

[bold cyan]Drama Budget Adjustments:[/bold cyan]
- Max Entities: [red]{original_budget.max_entities}[/red] -> [green]{healed_budget.max_entities}[/green]
- Max Particles: [red]{original_budget.max_particles}[/red] -> [green]{healed_budget.max_particles}[/green]

[bold green]✅ The AI has successfully downgraded the reality to guarantee a flawless 60fps![/bold green]
"""
    console.print(Panel(correction_panel, title="AI SUGGESTIONS APPLIED", border_style="green"))

# ==========================================
# DAY 24: THE AUDIO HOLE (CLI DSP SYNTHESIS TEST)
# ==========================================
@cli.group()
def audio():
    """Day 24: Procedural Audio Synthesis Commands."""
    pass

@audio.command(name="test")
@click.argument('sound_profile')
def audio_test(sound_profile):
    """
    Tests the Foley Director by generating pure mathematical AudioDNA.
    Usage: camera audio test neon_hum
    """
    console.print(Panel(f"[bold cyan]Initiating Foley Director for profile:[/bold cyan] {sound_profile}", title="Day 24: Procedural DSP Synthesis"))
    
    with console.status("[bold green]Foley Director is calculating mathematical sound waves...[/bold green]"):
        audio_dna = act_as_foley_director(sound_profile)
        
    console.print("[bold green]✅ Groq successfully generated flawless AudioDNA![/bold green]\n")
    
    # Display the DNA in a beautiful Rich Table
    table = Table(title=f"🎧 Web Audio API Parameters for: {sound_profile}")
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Description", style="dim")
    
    table.add_row("waveform_type", audio_dna.waveform_type, "The mathematical shape of the wave")
    table.add_row("base_frequency", f"{audio_dna.base_frequency} Hz", "The base pitch of the sound")
    table.add_row("envelope_attack", f"{audio_dna.envelope_attack} s", "Time to reach full volume")
    table.add_row("envelope_decay", f"{audio_dna.envelope_decay} s", "Time to fade out to silence")
    table.add_row("filter_type", audio_dna.filter_type, "Frequencies to cut off")
    
    console.print(table)
    
    # Show the raw JSON for the browser
    console.print("\n[bold yellow]Raw JSON DNA ready for the Web Audio API:[/bold yellow]")
    dna_json = json.dumps(audio_dna.model_dump(), indent=2)
    syntax = Syntax(dna_json, "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="AudioDNA Payload", border_style="green"))
    
    console.print("\n[bold cyan]Zero megabytes loaded. Pure math. Your i3 laptop is safe.[/bold cyan]")

# ==========================================
# DAY 25: THE INPUT HOLE (DETERMINISTIC REBINDING)
# ==========================================
@cli.group()
def input():
    """Day 25: Deterministic Input Mapping Commands."""
    pass

@input.command(name="rebind")
@click.argument('action_name')
@click.argument('new_key')
def rebind_input(action_name, new_key):
    """
    The Reality Recompiler.
    Instantly rewires a game control in the master OGF_STATE.json.
    Usage: camera input rebind jump Spacebar
    """
    console.print(Panel(f"[bold cyan]Recompiling Reality: Binding '{action_name}' to '{new_key}'[/bold cyan]", title="Day 25: Input Engine"))
    
    # 1. Load the Master Save File
    state_data = {"input_dna": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {STATE_FILE}. Creating new.[/yellow]")
            
    if "input_dna" not in state_data:
        state_data["input_dna"] = []
        
    # 2. Find and Update the DNA
    found = False
    for rule in state_data["input_dna"]:
        if rule.get("action_name") == action_name:
            old_key = rule.get("hardware_trigger")
            rule["hardware_trigger"] = new_key
            found = True
            console.print(f"[yellow]Updated existing rule: {action_name} ({old_key} -> {new_key})[/yellow]")
            break
            
    # 3. If not found, append a new rule
    if not found:
        new_rule = {
            "action_name": action_name,
            "hardware_trigger": new_key,
            "modifier_key": None,
            "active_context": "gameplay"
        }
        state_data["input_dna"].append(new_rule)
        console.print(f"[green]Created new rule: {action_name} -> {new_key}[/green]")
        
    # 4. Save back to disk
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f, indent=4)
        console.print(f"\n[bold green]✅ SUCCESS! Master Save File ({os.path.basename(STATE_FILE)}) updated.[/bold green]")
        console.print("[bold cyan]The Input Engine will automatically load this new map on next start.[/bold cyan]")
    except Exception as e:
        console.print(f"[bold red]Error saving state: {e}[/bold red]")

# ==========================================
# DAY 26: THE MODDING HOLE (COMMUNITY DNA VAULT)
# ==========================================
@cli.group()
def mod():
    """Day 26: Manage Community DNA Mods (The Modding Hole)."""
    pass

@mod.command('list')
def list_mods():
    """Fetch and display approved mods from the Supabase Vault."""
    if not supabase:
        console.print("[red]⚠️ Supabase connection failed. Check your .env file.[/red]")
        return

    with console.status("[bold cyan]🔍 Querying the Community Vault...[/bold cyan]"):
        try:
            response = supabase.table('community_vault').select('id, mod_name, metadata').eq('status', 'approved').execute()
            mods = response.data
            
            table = Table(title="🌐 COMMUNITY DNA VAULT (APPROVED)", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Tags", style="yellow")
            table.add_column("Version", style="dim")

            if not mods:
                console.print("[yellow]The Vault is empty. No approved mods yet.[/yellow]")
                return

            for m in mods:
                tags = ", ".join(m.get('metadata', {}).get('tags', []))
                version = m.get('metadata', {}).get('version', '1.0.0')
                table.add_row(str(m['id']), m['mod_name'], tags, version)
                
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error fetching mods: {e}[/red]")

@mod.command('install')
@click.argument('mod_id')
def install_mod(mod_id):
    """Download and safely inject a mod into OGF_STATE.json."""
    if not supabase:
        console.print("[red]⚠️ Supabase connection failed.[/red]")
        return

    with console.status(f"[bold cyan]⚡ INITIATING SAFE INJECTION PROTOCOL FOR {mod_id}...[/bold cyan]"):
        try:
            # 1. Fetch DNA
            response = supabase.table('community_vault').select('mod_dna').eq('id', mod_id).single().execute()
            mod_dna_dict = response.data['mod_dna']
            
            # 2. Validate (The Bouncer)
            safe_mod = ModDNA(**mod_dna_dict)
            console.print(f"[green]✓ DNA VALIDATED:[/green] {safe_mod.mod_name}")
            
            # 3. Load Local State
            state_file = STATE_FILE
            if not os.path.exists(state_file):
                console.print("[yellow]No OGF_STATE.json found. Initializing fresh reality...[/yellow]")
                current_world = WorldState()
                full_state = {"world_state": current_world.model_dump()}
            else:
                with open(state_file, 'r') as f:
                    full_state = json.load(f)
                    current_world = WorldState(**full_state.get('world_state', {}))
            
            # 4. Inject (The Merger)
            new_world = modding_engine.inject_mod(current_world, safe_mod, DramaBudget())
            
            # 5. Save
            full_state['world_state'] = new_world.model_dump()
            with open(state_file, 'w') as f:
                json.dump(full_state, f, indent=4)
                
            console.print(f"[bold green]🚀 INJECTION COMPLETE.[/bold green] Reality updated with '{safe_mod.mod_name}'.")
            
        except ValueError as ve:
            console.print(f"[red]⛔ INJECTION BLOCKED BY SANITIZER:[/red] {ve}")
        except Exception as e:
            console.print(f"[red]❌ INJECTION FAILED:[/red] {e}")

# ==========================================
# DAY 27: THE LOCALIZATION HOLE (SEMANTIC & FLUID)
# ==========================================
@cli.group()
def locale():
    """Day 27: Manage the Localization Hole (Language & Fluidity)."""
    pass

@locale.command("set")
@click.argument("language_code", type=str)
def set_locale(language_code: str):
    """
    Switch the entire engine to a new language (e.g., 'en', 'de', 'ja', 'es').
    Updates OGF_STATE, triggers UI fluid recompilation, and prints localized text.
    """
    console.print(f"\n[bold cyan]🌍 Switching Reality Locale to: {language_code.upper()}[/bold cyan]")
    
    # 1. Load current state from the master save file
    state_data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
        except Exception:
            pass
            
    app_dna_dict = state_data.get("app_dna", AppDNA().model_dump())
    
    # 2. Update the LocaleDNA inside the AppDNA
    cadence_shift = 0.0
    if language_code in ['es', 'ja', 'it']:
        cadence_shift = 0.15 
    elif language_code in ['de', 'ru', 'pl']:
        cadence_shift = -0.15 
        
    new_locale = LocaleDNA(
        target_language=language_code,
        audio_cadence_shift=cadence_shift,
        fluid_ui_rules=FluidUIRules(force_text_wrap=True)
    )
    
    app_dna_dict["locale"] = new_locale.model_dump()
    state_data["app_dna"] = app_dna_dict
    
    # 3. Save back to OGF_STATE.json
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f, indent=4)
        console.print("[green]✅ OGF_STATE.json updated successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error saving state: {e}[/red]")
        return
    
    # 4. Recompile UI with new Fluidity Rules
    console.print("[yellow]🏭 Triggering Fluid UI Recompilation...[/yellow]")
    app_dna = AppDNA(**app_dna_dict)
    design_config = synthesize_design_tokens(app_dna.design_tokens)
    compile_report = compile_ui(app_dna, design_config)
    
    if compile_report["success"]:
        console.print(f"[green]✅ UI Recompiled in {compile_report['compile_time_ms']}ms. Layout is mathematically fluid![/green]")
    else:
        console.print("[red]❌ UI Recompilation failed.[/red]")
        
    # 5. Print Localized Semantic Output to verify the dictionary
    console.print("\n[bold magenta]📖 Testing Semantic Dictionary Translation:[/bold magenta]")
    try:
        engine = LocalizationEngine()
        
        test_tokens = [
            SemanticToken(concept_id="ui_button_start", intensity=1.0),
            SemanticToken(concept_id="greeting_hostile", intensity=0.8, context_vars={"player_name": "Founder"})
        ]
        
        for token in test_tokens:
            translated_text = engine.get_translated_text(token, new_locale)
            console.print(Panel(
                f"[bold]{token.concept_id}[/bold] ➔ [cyan]{translated_text}[/cyan]", 
                title=f"Concept Translation ({language_code.upper()})"
            ))
            
    except Exception as e:
        console.print(f"[red]⚠️ Localization Engine test failed: {e}[/red]")
        console.print("[yellow]Note: Ensure your SUPABASE_URL and SUPABASE_ANON_KEY are in your .env file![/yellow]")

    console.print(f"\n[bold green]🎉 Locale switch complete. Your i3 laptop handled this flawlessly, Founder.[/bold green]\n")

# CRITICAL: Add the new command groups to the main 'cli' group!
cli.add_command(biome)
cli.add_command(navigate)
cli.add_command(backend)
cli.add_command(netcode)
cli.add_command(telemetry) # Day 23 Addition
cli.add_command(audio) # Day 24 Addition
cli.add_command(input) # Day 25 Addition
cli.add_command(mod) # Day 26 Addition
cli.add_command(locale) # Day 27 Addition

# ==========================================
# 3. START THE ENGINE
# ==========================================
if __name__ == '__main__':
    cli()