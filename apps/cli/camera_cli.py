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

# Existing Day 1-22 Imports + Day 24 Audio Director + Day 25 InputDNA + Day 26 ModDNA + Day 27 + Day 28 + Day 29 + Day 30
from packages.core.brain import (
    get_world_state, update_world_state, generate, 
    summarize_state, get_ui_blueprint, act_as_ecosystem_director,
    act_as_backend_architect,
    generate_deployment_topology,
    act_as_foley_director, # ADDED FOR DAY 24
    act_as_control_director, # ADDED FOR DAY 25
    act_as_translation_director, # ADDED FOR DAY 27
    act_as_economy_director, # ADDED FOR DAY 28
    act_as_mentor_director, # ADDED FOR DAY 29
    act_as_time_director, # ADDED FOR DAY 30
    generate_pacing_directive # ADDED FOR DAY 34
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
from packages.core.economy_engine import economy_engine # ADDED FOR DAY 28
from packages.core.tutorial_engine import TutorialEngine # ADDED FOR DAY 29
from packages.core.chrono_engine import ChronoEngine # ADDED FOR DAY 30
from packages.core.ecology_engine import simulate_tick, resolve_cascade # ADDED FOR DAY 34
from packages.core.flow_engine import calculate_flow_score # ADDED FOR DAY 34
from packages.core.content_weaver import ContentWeaver # ADDED FOR DAY 35

# --- DAY 23 to 35 ADDITIONS: Models ---
from packages.core.models import (
    VisualQuery, WorldState, NavMeshDNA, BiomeDNA, AppDNA, SecurityDNA,
    PerformanceReport, BottleneckType,
    AudioDNA, InputDNA, ModDNA, DramaBudget, LocaleDNA, SemanticToken, FluidUIRules,
    EconomyDNA, EconomicEvent, TutorialDNA, ChronoDNA, RewindIntent,
    EcologyDNA, FlowDNA, PacingDirective # Day 34 & 35 Models
)
from packages.core.telemetry_engine import telemetry_brain
from packages.core.modding_engine import engine as modding_engine 

# ==========================================
# SAFE IMPORTS (Days 31-33)
# ==========================================
try:
    from packages.core.models import AccessibilityDNA, DesignTokens
    from packages.core.brain import act_as_empathy_director
    from packages.core.accessibility_engine import default_accessibility_engine
    from packages.core.input_engine import DeterministicInputEngine
    from packages.core.accessibility_synthesizer import default_accessibility_synthesizer
    from packages.core.camera_comfort_engine import default_camera_comfort_engine
    from packages.core.social_engine import SocialMatrixEngine
    from packages.core.models import SocialDNA, SocialAction, FactionDNA, RelationshipTensor, SocialRule
    from packages.core.brain import generate_quest_dna_report, progress_quest_node
    from packages.core.models import QuestDNA
except Exception:
    # Fallbacks if engines are missing
    AccessibilityDNA = DesignTokens = act_as_empathy_director = default_accessibility_engine = None
    DeterministicInputEngine = default_accessibility_synthesizer = default_camera_comfort_engine = None
    SocialDNA = SocialAction = FactionDNA = RelationshipTensor = SocialRule = SocialMatrixEngine = None
    generate_quest_dna_report = progress_quest_node = QuestDNA = None

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../OGF_STATE.json'))

def get_active_project_id():
    if not supabase: return None
    try:
        response = supabase.table("projects").select("id").order("created_at", desc=True).limit(1).execute()
        if response.data: return response.data[0]["id"]
    except: pass
    return None

# ==========================================
# 2. THE CLI BUTTONS (Click Library)
# ==========================================
@click.group()
def cli():
    """Camera AI: The Ontological Genesis Fabric CLI."""
    pass

# ... (Days 1-34 Commands Preserved) ...
# (I have omitted the massive block of Days 1-34 commands here for brevity, 
# but they remain EXACTLY as they were in your file. 
# We are inserting Day 35 below.)

# ==========================================
# DAY 35: THE INFINITE CONTENT WEAVER (AAA MOMENTS)
# ==========================================
weaver_day35 = ContentWeaver()

def _get_mock_states_day35(pacing_str: str = "maintain_flow"):
    pacing_map = {
        "increase_tension": PacingDirective.INCREASE_TENSION,
        "reduce_difficulty": PacingDirective.REDUCE_DIFFICULTY,
        "maintain_flow": PacingDirective.MAINTAIN_FLOW,
        "quiet_moment": PacingDirective.QUIET_MOMENT
    }
    pacing_enum = pacing_map.get(pacing_str, PacingDirective.MAINTAIN_FLOW)
    # Low flow_score (45.0) triggers the Tutorial empathy engine in orchestrate_moment
    flow = FlowDNA(pacing_directive=pacing_enum, flow_score=45.0)
    return flow, {}, {}, {}, {}, {}

@cli.group()
def moment():
    """Day 35: Infinite Content Weaver - Orchestrate AAA Moments."""
    pass

@moment.command(name="generate")
def moment_generate():
    """Reads current engine states (mocked) and prints the full AAAMoment JSON."""
    console.print("[bold green]🎬 Generating AAA Moment from current world state...[/bold green]")
    flow, eco, soc, nar, econ, world = _get_mock_states_day35()
    
    dna = weaver_day35.generate_moment(flow, eco, soc, nar, econ, world)
    actual_moment = weaver_day35.orchestrate_moment(dna, flow)
    
    console.print(Panel(json.dumps(actual_moment.model_dump(mode='json'), indent=2, default=str), title="AAA Moment Orchestrated", border_style="green"))

@moment.command(name="test")
@click.argument('pacing')
def moment_test(pacing):
    """Simulates a specific pacing directive (increase_tension, reduce_difficulty, etc.)."""
    valid_pacings = ["increase_tension", "reduce_difficulty", "maintain_flow", "quiet_moment"]
    if pacing not in valid_pacings:
        console.print(f"[bold red]Invalid pacing directive. Choose from: {', '.join(valid_pacings)}[/bold red]")
        return

    console.print(f"[bold cyan]🧪 Testing pacing directive: {pacing}[/bold cyan]")
    flow, eco, soc, nar, econ, world = _get_mock_states_day35(pacing)
    
    dna = weaver_day35.generate_moment(flow, eco, soc, nar, econ, world)
    actual_moment = weaver_day35.orchestrate_moment(dna, flow)
    
    console.print(Panel(json.dumps(actual_moment.model_dump(mode='json'), indent=2, default=str), title=f"Test Result: {pacing}", border_style="cyan"))

@moment.command(name="curve")
@click.argument('count', type=int, default=10)
def moment_curve(count):
    """Generates N moments in sequence, builds the tension curve, and prints a text graph."""
    console.print(f"[bold magenta]📈 Building tension curve for {count} moments...[/bold magenta]")
    moments = []
    flow, eco, soc, nar, econ, world = _get_mock_states_day35()
    
    for i in range(count):
        dna = weaver_day35.generate_moment(flow, eco, soc, nar, econ, world)
        actual_moment = weaver_day35.orchestrate_moment(dna, flow)
        moments.append(actual_moment)
        
    curve_data = weaver_day35.build_tension_curve(moments)
    curve = curve_data["tension_curve"]
    
    for i, val in enumerate(curve):
        bar_len = int(val * 40)
        bar = "█" * bar_len
        console.print(f"Tick {i+1:02d} | [cyan]{bar}[/cyan] ({val})")
        
    if curve_data["forced_next_arc"]:
        console.print(f"\n[bold red]⚠️ Pacing Rule Triggered: Forcing next moment to be '{curve_data['forced_next_arc']}'[/bold red]")

# CRITICAL: Add the new command groups to the main 'cli' group!
# (Ensure all your previous add_command calls are here)
cli.add_command(moment) # Day 35 Addition

# ==========================================
# 3. START THE ENGINE
# ==========================================
if __name__ == '__main__':
    cli()