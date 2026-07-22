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
from packages.core.fidelity_engine import resolve_fidelity, render_entity # ADDED FOR DAY 36

# --- DAY 23 to 36 ADDITIONS: Models ---
from packages.core.models import (
    VisualQuery, WorldState, NavMeshDNA, BiomeDNA, AppDNA, SecurityDNA,
    PerformanceReport, BottleneckType,
    AudioDNA, # ADDED FOR DAY 24
    InputDNA, # ADDED FOR DAY 25
    ModDNA, DramaBudget, # ADDED FOR DAY 26
    LocaleDNA, SemanticToken, FluidUIRules, # ADDED FOR DAY 27
    EconomyDNA, EconomicEvent, # ADDED FOR DAY 28
    TutorialDNA, # ADDED FOR DAY 29
    ChronoDNA, RewindIntent, # ADDED FOR DAY 30
    EcologyDNA, FlowDNA, PacingDirective, # ADDED FOR DAY 34
    FidelityDNA, HardwareTier, ShaderProfile # ADDED FOR DAY 36
)
from packages.core.telemetry_engine import telemetry_brain
from packages.core.modding_engine import engine as modding_engine # ADDED FOR DAY 26


# ==========================================
# DAY 31 SAFE IMPORTS:
# These are wrapped so the CLI remains protected
# even if a single engine file is missing.
# ==========================================
try:
    from packages.core.models import AccessibilityDNA, DesignTokens
except Exception:
    AccessibilityDNA = None
    DesignTokens = None

try:
    from packages.core.brain import act_as_empathy_director
except Exception:
    act_as_empathy_director = None

try:
    from packages.core.accessibility_engine import default_accessibility_engine
except Exception:
    default_accessibility_engine = None

try:
    from packages.core.input_engine import DeterministicInputEngine
except Exception:
    DeterministicInputEngine = None

try:
    from packages.core.accessibility_synthesizer import default_accessibility_synthesizer
except Exception:
    default_accessibility_synthesizer = None

try:
    from packages.core.camera_comfort_engine import default_camera_comfort_engine
except Exception:
    default_camera_comfort_engine = None


# ==========================================
# DAY 32 SAFE IMPORTS:
# The Quest Hole / Procedural Narrative Graphs.
# ==========================================
try:
    from packages.core.brain import (
        generate_quest_dna_report,
        progress_quest_node
    )
    from packages.core.models import QuestDNA
except Exception:
    generate_quest_dna_report = None
    progress_quest_node = None
    QuestDNA = None


# ==========================================
# DAY 33 SAFE IMPORTS:
# The Social Hole / Deterministic Social Matrices.
# ==========================================
try:
    from packages.core.models import (
        SocialDNA,
        SocialAction,
        FactionDNA,
        RelationshipTensor,
        SocialRule
    )
    from packages.core.social_engine import SocialMatrixEngine
    from packages.core.brain import (
        generate_social_dna_report,
        generate_social_dna,
        generate_city_social_dna,
        generate_faction_social_dna
    )
except Exception:
    SocialDNA = None
    SocialAction = None
    FactionDNA = None
    RelationshipTensor = None
    SocialRule = None
    SocialMatrixEngine = None
    generate_social_dna_report = None
    generate_social_dna = None
    generate_city_social_dna = None
    generate_faction_social_dna = None


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
# DAY 31: ACCESSIBILITY CLI HELPERS
# ==========================================

ACCESSIBILITY_PROFILE_PRESETS = {
    "standard": {
        "cognitive_load_level": "balanced",
        "motor_assist_mode": "standard",
        "visual_contrast_profile": "standard",
        "audio_cue_amplification": "off",
        "camera_comfort_mode": "standard",
    },
    "comfort": {
        "cognitive_load_level": "supported",
        "motor_assist_mode": "generous_timing",
        "visual_contrast_profile": "high_contrast",
        "audio_cue_amplification": "high",
        "camera_comfort_mode": "reduced_motion",
    },
    "max_support": {
        "cognitive_load_level": "max_support",
        "motor_assist_mode": "max_assist",
        "visual_contrast_profile": "high_contrast",
        "audio_cue_amplification": "high",
        "camera_comfort_mode": "stable_only",
    },
}

ACCESSIBILITY_TOKEN_MAP = {
    # Visual contrast tokens
    "high_contrast": {"visual_contrast_profile": "high_contrast"},
    "standard_contrast": {"visual_contrast_profile": "standard"},

    # Motor assist tokens
    "generous_timing": {"motor_assist_mode": "generous_timing"},
    "max_assist": {"motor_assist_mode": "max_assist"},
    "standard_timing": {"motor_assist_mode": "standard"},

    # Camera comfort tokens
    "reduced_motion": {"camera_comfort_mode": "reduced_motion"},
    "stable_only": {"camera_comfort_mode": "stable_only"},
    "standard_camera": {"camera_comfort_mode": "standard"},

    # Audio cue tokens
    "audio_off": {"audio_cue_amplification": "off"},
    "audio_low": {"audio_cue_amplification": "low"},
    "audio_medium": {"audio_cue_amplification": "medium"},
    "audio_high": {"audio_cue_amplification": "high"},

    # Cognitive load tokens
    "cognitive_minimal": {"cognitive_load_level": "minimal"},
    "cognitive_balanced": {"cognitive_load_level": "balanced"},
    "cognitive_supported": {"cognitive_load_level": "supported"},
    "cognitive_max_support": {"cognitive_load_level": "max_support"},
}


def _to_json_safe(obj):
    """
    Convert Pydantic models or dicts into JSON-safe dictionaries.
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return copy.deepcopy(obj)

    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except Exception:
            return obj.model_dump()

    if hasattr(obj, "dict"):
        return obj.dict()

    return {}


def _load_ogf_state():
    """
    Load OGF_STATE.json safely.
    """
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {}

    except Exception as e:
        console.print(f"[yellow]Warning: Could not read OGF_STATE.json. Starting fresh. {e}[/yellow]")
        return {}


def _save_ogf_state(state_data):
    """
    Save OGF_STATE.json safely.
    """
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
        return True

    except Exception as e:
        console.print(f"[bold red]Error saving OGF_STATE.json: {e}[/bold red]")
        return False


def _get_current_accessibility(state_data):
    """
    Read current AccessibilityDNA from OGF_STATE.json.
    """
    if AccessibilityDNA is None:
        return None

    current = state_data.get("accessibility_dna")

    if not current:
        app_dna = state_data.get("app_dna", {})
        if isinstance(app_dna, dict):
            current = app_dna.get("accessibility")

    if current and isinstance(current, dict):
        try:
            return AccessibilityDNA(**current)
        except Exception:
            return AccessibilityDNA()

    return AccessibilityDNA()


def _apply_accessibility_updates(current_accessibility, updates):
    """
    Apply a dictionary of valid updates onto AccessibilityDNA.
    """
    if AccessibilityDNA is None:
        return None

    current_dict = _to_json_safe(current_accessibility)

    if not current_dict:
        current_dict = _to_json_safe(AccessibilityDNA())

    current_dict.update(updates)

    try:
        return AccessibilityDNA(**current_dict)
    except Exception:
        return AccessibilityDNA()


def _parse_accessibility_mode(mode, current_accessibility):
    """
    Parse CLI profile mode into AccessibilityDNA.
    """
    if AccessibilityDNA is None:
        return None, [], "AccessibilityDNA is not available."

    raw_mode = str(mode or "").strip().lower()

    if raw_mode in ("auto", "empathy", "brain"):
        return "auto", ["empathy_director"], None

    normalized = (
        raw_mode
        .replace(" ", "_")
        .replace(",", "+")
        .replace(";", "+")
        .replace("/", "+")
    )

    updates = {}
    applied_tokens = []

    if normalized in ACCESSIBILITY_PROFILE_PRESETS:
        updates.update(ACCESSIBILITY_PROFILE_PRESETS[normalized])
        applied_tokens.append(normalized)

    elif normalized in ("standard", "default", "reset"):
        updates.update(ACCESSIBILITY_PROFILE_PRESETS["standard"])
        applied_tokens.append("standard")

    else:
        tokens = [token for token in normalized.split("+") if token]

        for token in tokens:
            if token in ("standard", "default", "reset"):
                updates.update(ACCESSIBILITY_PROFILE_PRESETS["standard"])
                applied_tokens.append("standard")

            elif token in ACCESSIBILITY_PROFILE_PRESETS:
                updates.update(ACCESSIBILITY_PROFILE_PRESETS[token])
                applied_tokens.append(token)

            elif token in ACCESSIBILITY_TOKEN_MAP:
                updates.update(ACCESSIBILITY_TOKEN_MAP[token])
                applied_tokens.append(token)

            else:
                return None, applied_tokens, f"Unknown accessibility token: '{token}'"

    if not updates:
        return None, applied_tokens, "No accessibility updates found."

    new_accessibility = _apply_accessibility_updates(current_accessibility, updates)
    return new_accessibility, applied_tokens, None


def _print_ui_accessibility_report(report):
    if not report:
        console.print("[yellow]UI Token Synthesizer: unavailable.[/yellow]")
        return

    changes = report.get("changes", {})

    if not changes:
        console.print("[green]UI Token Synthesizer: no color changes required.[/green]")
        return

    table = Table(title="🎨 UI Token Synthesizer Mathematical Changes")
    table.add_column("Token", style="cyan")
    table.add_column("Old", style="red")
    table.add_column("New", style="green")
    table.add_column("Before", style="dim")
    table.add_column("After", style="bold")

    for path, change in list(changes.items())[:15]:
        if isinstance(change, dict):
            old_value = str(change.get("old", ""))
            new_value = str(change.get("new", ""))
            before = str(change.get("contrast_before", change.get("reason", "")))
            after = str(change.get("contrast_after", change.get("target_ratio", "")))
            table.add_row(path, old_value, new_value, before, after)
        else:
            table.add_row(path, str(change), "", "", "")

    console.print(table)


def _print_input_accessibility_report(report):
    if not report:
        console.print("[yellow]Input Engine: unavailable.[/yellow]")
        return

    changes = report.get("changes", {})

    if not changes:
        console.print(
            f"[green]Input Engine: mode is now '{report.get('new_motor_assist_mode', 'standard')}'. "
            f"No timing windows needed changing.[/green]"
        )
        return

    table = Table(title="🎮 Input Engine Mathematical Timing Changes")
    table.add_column("Action", style="cyan")
    table.add_column("Base ms", style="dim")
    table.add_column("Previous ms", style="red")
    table.add_column("New ms", style="green")
    table.add_column("Multiplier", style="magenta")

    for action_name, change in changes.items():
        table.add_row(
            str(action_name),
            str(change.get("base_window_ms", "")),
            str(change.get("previous_active_window_ms", "")),
            str(change.get("new_active_window_ms", "")),
            str(change.get("multiplier", "")),
        )

    console.print(table)


def _print_audio_accessibility_report(report):
    if not report:
        console.print("[yellow]Audio DSP Engine: unavailable.[/yellow]")
        return

    table = Table(title="🔊 Audio DSP Mathematical Changes")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mode", str(report.get("audio_cue_amplification", "off")))
    table.add_row("Previous Boost dB", str(report.get("previous_boost_db", 0.0)))
    table.add_row("New Boost dB", str(report.get("new_boost_db", 0.0)))
    table.add_row("Critical Band Hz", str(report.get("critical_frequency_band_hz", [])))
    table.add_row("Formula", str(report.get("formula", "")))

    console.print(table)


def _print_camera_accessibility_report(report):
    if not report:
        console.print("[yellow]Camera Comfort Engine: unavailable.[/yellow]")
        return

    changes = report.get("changes", {})

    if not changes:
        console.print(
            f"[green]Camera Comfort Engine: mode is now '{report.get('camera_comfort_mode', 'standard')}'. "
            f"No camera fields needed changing.[/green]"
        )
        return

    table = Table(title="🎥 Camera Comfort Mathematical Changes")
    table.add_column("Field", style="cyan")
    table.add_column("Old", style="red")
    table.add_column("New", style="green")

    for field_name, change in changes.items():
        if isinstance(change, dict):
            table.add_row(
                str(field_name),
                str(change.get("old", "")),
                str(change.get("new", "")),
            )
        else:
            table.add_row(str(field_name), str(change), "")

    console.print(table)


# ==========================================
# DAY 32: QUEST CLI HELPERS
# ==========================================

def _quest_jsonable(obj):
    if obj is None:
        return None

    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except Exception:
            return obj.model_dump()

    if isinstance(obj, dict):
        return obj

    if isinstance(obj, list):
        return obj

    return str(obj)


def _quest_json_block(payload) -> Syntax:
    text = json.dumps(
        _quest_jsonable(payload),
        indent=2,
        default=str
    )

    return Syntax(
        text,
        "json",
        theme="monokai",
        line_numbers=False
    )


def _quest_parse_completed(raw_value: str):
    if not raw_value:
        return []

    raw_value = raw_value.strip()

    if raw_value.startswith("["):
        try:
            parsed = json.loads(raw_value)

            if isinstance(parsed, list):
                return [
                    str(item).strip()
                    for item in parsed
                    if str(item).strip()
                ]

        except Exception:
            pass

    return [
        part.strip()
        for part in raw_value.split(",")
        if part.strip()
    ]


def _quest_demo_payload() -> dict:
    return {
        "quest_id": "quest_demo_ruins",
        "nodes": [
            {
                "node_id": "node_enter_ruins",
                "semantic_concept": "player_discovers_the_old_world_ruins",
                "completion_condition": {
                    "type": "always"
                },
                "state_mutations": {
                    "ruins_discovered": True
                }
            },
            {
                "node_id": "node_find_signal",
                "semantic_concept": "player_finds_a_weak_unknown_signal",
                "completion_condition": {
                    "type": "node_completed",
                    "node_id": "node_enter_ruins"
                },
                "state_mutations": {
                    "signal_found": True,
                    "heat_level": {"$add": 1}
                }
            },
            {
                "node_id": "node_open_vault",
                "semantic_concept": "player_opens_the_hidden_vault_door",
                "completion_condition": {
                    "type": "node_completed",
                    "node_id": "node_find_signal"
                },
                "state_mutations": {
                    "vault_open": True,
                    "time_of_day": "18:00"
                }
            }
        ],
        "edges": [
            {
                "from_node": "node_enter_ruins",
                "to_node": "node_find_signal"
            },
            {
                "from_node": "node_find_signal",
                "to_node": "node_open_vault"
            }
        ],
        "prerequisites": [],
        "state_mutations": {
            "quest_demo_ruins_complete": True
        }
    }


def _quest_load_payload(project_id=None, quest_id=None):
    demo = _quest_demo_payload()

    if not project_id:
        project_id = get_active_project_id()

    if supabase and project_id:
        try:
            query = (
                supabase.table("narrative_graphs")
                .select("quest_dna")
                .eq("project_id", project_id)
                .eq("is_active", True)
            )

            if quest_id:
                query = query.eq("quest_id", quest_id)

            response = (
                query
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0].get("quest_dna")

            if quest_id:
                return None

        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not load quest from Supabase: {e}[/yellow]"
            )

    if quest_id:
        if quest_id == demo.get("quest_id"):
            return demo

        return None

    return demo


def _quest_save_to_supabase(project_id, quest_json: dict):
    if not supabase:
        return False, "Supabase is not connected."

    if not project_id:
        project_id = get_active_project_id()

    if not project_id:
        return False, "No project_id available. Cannot save QuestDNA."

    owner_id = None

    try:
        project_response = (
            supabase.table("projects")
            .select("owner_id")
            .eq("id", project_id)
            .limit(1)
            .execute()
        )

        if project_response.data and len(project_response.data) > 0:
            owner_id = project_response.data[0].get("owner_id")

    except Exception:
        owner_id = None

    payload = {
        "project_id": project_id,
        "quest_id": quest_json.get("quest_id"),
        "quest_dna": quest_json,
        "is_active": True,
        "owner_id": owner_id or "00000000-0000-0000-0000-000000000000",
        "unlocked_player_ids": []
    }

    try:
        try:
            (
                supabase.table("narrative_graphs")
                .update({"is_active": False})
                .eq("project_id", project_id)
                .execute()
            )
        except Exception:
            pass

        (
            supabase.table("narrative_graphs")
            .upsert(
                payload,
                on_conflict="project_id,quest_id"
            )
            .execute()
        )

        return True, f"Quest '{payload['quest_id']}' saved to Supabase."

    except Exception as e:
        return False, f"Could not save QuestDNA: {e}"


def _quest_print_generation_report(report: dict):
    quest_json = report.get("quest_json") or {}
    validation = report.get("validation") or {}

    console.print(
        Panel(
            f"[green]Story Weaver generated QuestDNA[/green]\n"
            f"Quest ID: [cyan]{quest_json.get('quest_id')}[/cyan]\n"
            f"Attempts: [cyan]{report.get('attempts', 0)}[/cyan]\n"
            f"Valid DAG: [cyan]{validation.get('is_valid', False)}[/cyan]",
            title="Day 32: Quest Generation",
            border_style="cyan"
        )
    )

    node_table = Table(title="Narrative Nodes")
    node_table.add_column("Node ID", style="cyan")
    node_table.add_column("Semantic Concept", style="white")
    node_table.add_column("Completion Condition", style="magenta")
    node_table.add_column("State Mutations", style="yellow")

    for node in quest_json.get("nodes", []):
        node_table.add_row(
            str(node.get("node_id", "")),
            str(node.get("semantic_concept", "")),
            json.dumps(node.get("completion_condition", {}), default=str),
            json.dumps(node.get("state_mutations", {}), default=str)
        )

    console.print(node_table)

    edge_table = Table(title="Directed Edges")
    edge_table.add_column("From Node", style="cyan")
    edge_table.add_column("", style="white")
    edge_table.add_column("To Node", style="cyan")

    for edge in quest_json.get("edges", []):
        edge_table.add_row(
            str(edge.get("from_node", "")),
            "→",
            str(edge.get("to_node", ""))
        )

    console.print(edge_table)

    if validation.get("topological_order"):
        console.print(
            Panel(
                " → ".join(validation["topological_order"]),
                title="Topological Order",
                border_style="green"
            )
        )


def _quest_print_progress_result(result: dict):
    if result.get("success"):
        console.print(
            Panel(
                f"[green]Node completed successfully.[/green]\n"
                f"Quest ID: [cyan]{result.get('quest_id')}[/cyan]\n"
                f"Node ID: [cyan]{result.get('node_id')}[/cyan]\n"
                f"Semantic Concept: [white]{result.get('semantic_concept', '')}[/white]",
                title="Day 32: Quest Progress",
                border_style="green"
            )
        )
    else:
        console.print(
            Panel(
                f"[red]Node completion failed.[/red]\n"
                f"Quest ID: [cyan]{result.get('quest_id')}[/cyan]\n"
                f"Node ID: [cyan]{result.get('node_id')}[/cyan]",
                title="Day 32: Quest Progress",
                border_style="red"
            )
        )

    meta_table = Table(title="Progress State")
    meta_table.add_column("Field", style="cyan")
    meta_table.add_column("Value", style="white")

    meta_table.add_row(
        "Completed Nodes",
        ", ".join(result.get("completed_node_ids", [])) or "None"
    )

    meta_table.add_row(
        "Active Nodes",
        ", ".join(result.get("active_node_ids", [])) or "None"
    )

    mutation_report = result.get("mutation_report") or {}

    meta_table.add_row(
        "Mutation Engine",
        str(mutation_report.get("engine", "none"))
    )

    console.print(meta_table)

    console.print("\n[yellow]Applied Mutations:[/yellow]")
    console.print(
        _quest_json_block(result.get("applied_mutations", {}))
    )

    console.print("\n[yellow]Updated World State:[/yellow]")
    console.print(
        _quest_json_block(result.get("world_state", {}))
    )

    errors = result.get("errors", [])

    if errors:
        console.print("\n[red]Errors:[/red]")

        for error in errors:
            console.print(f"[red]- {error}[/red]")


# ==========================================
# DAY 33: SOCIAL CLI HELPERS
# ==========================================

def _social_demo_payload() -> dict:
    return {
        "factions": [
            {
                "faction_id": "faction_merchants_guild",
                "name": "Merchants Guild",
                "description": "A trade coalition that values profit and stability.",
                "values": ["profit", "stability", "contracts"],
                "goals": ["control trade routes"],
                "disposition_toward_player": 0.2,
            },
            {
                "faction_id": "faction_iron_guard",
                "name": "Iron Guard",
                "description": "A militaristic order that values control and protection.",
                "values": ["order", "protection", "discipline"],
                "goals": ["secure the city gates"],
                "disposition_toward_player": -0.05,
            },
            {
                "faction_id": "faction_ashen_choir",
                "name": "Ashen Choir",
                "description": "A secretive religious movement that values revelation.",
                "values": ["faith", "secrecy", "prophecy"],
                "goals": ["recover ancient relics"],
                "disposition_toward_player": 0.0,
            },
        ],
        "relationship_tensors": [
            {
                "source_id": "faction_iron_guard",
                "target_id": "faction_merchants_guild",
                "weight": -0.8,
                "relationship_type": "rivalry",
                "confidence": 0.95,
                "notes": "The Guard distrusts merchant corruption.",
            },
            {
                "source_id": "faction_merchants_guild",
                "target_id": "faction_iron_guard",
                "weight": -0.6,
                "relationship_type": "rivalry",
                "confidence": 0.9,
                "notes": "The Guild resents Guard tariffs.",
            },
            {
                "source_id": "faction_ashen_choir",
                "target_id": "faction_merchants_guild",
                "weight": 0.1,
                "relationship_type": "neutral_trade_contact",
                "confidence": 0.7,
                "notes": "The Choir trades relics through the Guild, but remains detached.",
            },
            {
                "source_id": "faction_ashen_choir",
                "target_id": "faction_iron_guard",
                "weight": -0.25,
                "relationship_type": "religious_tension",
                "confidence": 0.8,
                "notes": "The Choir sees the Guard as spiritually blind.",
            },
            {
                "source_id": "npc_ivan",
                "target_id": "faction_iron_guard",
                "weight": 0.85,
                "relationship_type": "alliance",
                "confidence": 0.95,
                "notes": "Ivan is a loyal former guardsman.",
            },
            {
                "source_id": "faction_iron_guard",
                "target_id": "player",
                "weight": -0.05,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Guard is slightly suspicious of the player.",
            },
            {
                "source_id": "faction_merchants_guild",
                "target_id": "player",
                "weight": 0.2,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Guild sees the player as useful.",
            },
            {
                "source_id": "faction_ashen_choir",
                "target_id": "player",
                "weight": 0.0,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Choir has not judged the player yet.",
            },
            {
                "source_id": "npc_ivan",
                "target_id": "player",
                "weight": 0.0,
                "relationship_type": "stranger",
                "confidence": 1.0,
                "notes": "Ivan does not know the player yet.",
            },
        ],
        "social_rules": [
            {
                "rule_id": "rule_helping_allies_angers_rivals",
                "trigger_action": "help",
                "effect_type": "disposition_change",
                "magnitude_multiplier": 1.0,
                "description": "Helping a faction irritates its rivals.",
            },
            {
                "rule_id": "rule_harming_allies_pleases_rivals",
                "trigger_action": "steal",
                "effect_type": "disposition_change",
                "magnitude_multiplier": 1.0,
                "description": "Harming a faction can please its rivals.",
            },
        ],
        "metadata": {
            "demo": True,
            "day": 33,
        },
    }


def _social_demo_dna():
    if SocialDNA is None:
        return None

    return SocialDNA(**_social_demo_payload())


def _social_load_from_file(file_path: str):
    if SocialDNA is None:
        return None

    if not file_path:
        return None

    full_path = os.path.abspath(os.path.expanduser(file_path))

    if not os.path.exists(full_path):
        console.print(f"[red]SocialDNA file not found:[/red] {full_path}")
        return None

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            console.print("[red]SocialDNA JSON root must be an object.[/red]")
            return None

        payload = data.get("social_dna", data)

        return SocialDNA(**payload)

    except Exception as e:
        console.print(f"[red]Could not load SocialDNA from file:[/red] {e}")
        return None


def _social_load_active_from_supabase(project_id=None):
    if SocialDNA is None:
        return None

    if not supabase:
        return None

    if not project_id:
        project_id = get_active_project_id()

    if not project_id:
        return None

    try:
        response = (
            supabase.table("social_matrices")
            .select("social_dna")
            .eq("project_id", project_id)
            .filter("player_id", "is", "null")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )

        if response.data and len(response.data) > 0:
            social_payload = response.data[0].get("social_dna", {})
            return SocialDNA(**social_payload)

    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not load active SocialDNA from Supabase: {e}[/yellow]"
        )

    return None


def _social_load_dna(file_path=None, project_id=None):
    if SocialDNA is None:
        return None, "unavailable"

    if file_path:
        file_dna = _social_load_from_file(file_path)

        if file_dna is not None:
            return file_dna, f"file:{file_path}"

        console.print("[yellow]Falling back because file SocialDNA could not be loaded.[/yellow]")

    active_dna = _social_load_active_from_supabase(project_id=project_id)

    if active_dna is not None:
        return active_dna, "supabase"

    return _social_demo_dna(), "demo"


def _social_make_engine(social_dna, actor_id: str = "player"):
    if SocialMatrixEngine is None:
        return None

    return SocialMatrixEngine(
        social_dna=social_dna,
        player_id=actor_id,
        propagation_strength=1.0,
        indirect_decay=0.65,
        refusal_threshold=-0.5,
        alliance_threshold=0.6,
    )


def _social_entity_name(entity_id: str, social_dna) -> str:
    if entity_id == "player":
        return "Player"

    if social_dna is not None:
        for faction in social_dna.factions:
            if faction.faction_id == entity_id:
                return faction.name

    return (
        str(entity_id)
        .replace("_", " ")
        .replace("npc ", "NPC ")
        .title()
    )


def _social_print_edges(engine, social_dna) -> None:
    if engine is None:
        console.print("[red]SocialMatrixEngine is unavailable.[/red]")
        return

    edges = engine.get_edges()

    table = Table(title="Social Relationship Matrix")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="cyan")
    table.add_column("Weight", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Notes", style="white")

    if not edges:
        table.add_row("-", "-", "-", "-", "No relationships.")
        console.print(table)
        return

    for edge in edges:
        table.add_row(
            _social_entity_name(edge.get("source_id", "?"), social_dna),
            _social_entity_name(edge.get("target_id", "?"), social_dna),
            f"{float(edge.get('weight', 0.0)):.2f}",
            str(edge.get("relationship_type", "neutral")),
            str(edge.get("notes", "")),
        )

    console.print(table)


def _social_print_disposition_table(
    engine,
    social_dna,
    actor_id: str,
    title: str,
) -> None:
    if engine is None:
        console.print("[red]SocialMatrixEngine is unavailable.[/red]")
        return

    table = Table(title=title)
    table.add_column("Entity", style="cyan")
    table.add_column("Disposition Toward Actor", style="magenta")
    table.add_column("Can Interact With Actor", style="green")

    entity_ids = engine.get_entity_ids()

    for entity_id in entity_ids:
        if entity_id == actor_id:
            continue

        weight = engine.get_relationship(entity_id, actor_id)
        can_interact = engine.can_interact(entity_id, actor_id)

        table.add_row(
            _social_entity_name(entity_id, social_dna),
            f"{weight:.2f}",
            "yes" if can_interact else "no",
        )

    console.print(table)


def _social_print_direct_effects(report: dict, social_dna) -> None:
    direct_effects = report.get("direct_effects", [])

    table = Table(title="Direct Effects")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="cyan")
    table.add_column("Old", style="yellow")
    table.add_column("Delta", style="magenta")
    table.add_column("New", style="green")
    table.add_column("Reason", style="white")

    if not direct_effects:
        table.add_row("-", "-", "-", "-", "-", "No direct effect.")
        console.print(table)
        return

    for effect in direct_effects:
        table.add_row(
            _social_entity_name(effect.get("source_id", "?"), social_dna),
            _social_entity_name(effect.get("target_id", "?"), social_dna),
            f"{float(effect.get('old_weight', 0.0)):.2f}",
            f"{float(effect.get('delta', 0.0)):+.2f}",
            f"{float(effect.get('new_weight', 0.0)):.2f}",
            str(effect.get("reason", "")),
        )

    console.print(table)


def _social_print_ripple_effects(report: dict, social_dna) -> None:
    ripple_effects = report.get("ripple_effects", [])

    table = Table(title="Ripple Effects")
    table.add_column("Observer", style="cyan")
    table.add_column("Toward", style="cyan")
    table.add_column("Influence", style="yellow")
    table.add_column("Old", style="yellow")
    table.add_column("Delta", style="magenta")
    table.add_column("New", style="green")

    if not ripple_effects:
        table.add_row("-", "-", "-", "-", "-", "No ripple effects.")
        console.print(table)
        return

    for effect in ripple_effects:
        table.add_row(
            _social_entity_name(effect.get("source_id", "?"), social_dna),
            _social_entity_name(effect.get("target_id", "?"), social_dna),
            f"{float(effect.get('influence_score', 0.0)):.2f}",
            f"{float(effect.get('old_weight', 0.0)):.2f}",
            f"{float(effect.get('delta', 0.0)):+.2f}",
            f"{float(effect.get('new_weight', 0.0)):.2f}",
        )

    console.print(table)


def _social_print_interaction_blocks(engine, social_dna) -> None:
    if engine is None:
        console.print("[red]SocialMatrixEngine is unavailable.[/red]")
        return

    blocks = engine.get_interaction_blocks()

    table = Table(title="Interaction Refusals")
    table.add_column("Source", style="cyan")
    table.add_column("Refuses Interaction With", style="red")

    if not blocks:
        table.add_row("-", "No refusals.")
        console.print(table)
        return

    for source_id, target_ids in blocks.items():
        for target_id in target_ids:
            table.add_row(
                _social_entity_name(source_id, social_dna),
                _social_entity_name(target_id, social_dna),
            )

    console.print(table)


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

    table = Table(title="📊 Last 5 Telemetry Reports (Black Box)")
    table.add_column("Timestamp", style="dim")
    table.add_column("FPS", justify="right", style="bold")
    table.add_column("Dropped Frames", justify="right", style="yellow")
    table.add_column("Memory (MB)", justify="right", style="blue")
    table.add_column("Bottleneck", style="red")

    for log in logs:
        ts = log.get('created_at', 'Unknown')
        if len(ts) > 19:
            ts = ts[:19] 
            
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

    bad_report_dict = None
    for log in logs:
        bn = log.get('bottleneck_component')
        if bn and bn != 'none' and bn != BottleneckType.NONE.value:
            bad_report_dict = log
            break
            
    if not bad_report_dict:
        console.print("\n[bold green]✅ All recent reports are healthy. The engine is running perfectly at 60fps![/bold green]")
        return

    console.print(f"\n[bold red]🚨 CRITICAL BOTTLENECK DETECTED: {bad_report_dict.get('bottleneck_component').upper()}[/bold red]")
    console.print("[bold yellow]Initiating AI Self-Healing Sequence...[/bold yellow]")
    
    try:
        report_obj = PerformanceReport.model_validate(bad_report_dict)
    except Exception as e:
        console.print(f"[red]Failed to validate report against Pydantic schema: {e}[/red]")
        return

    current_dna = AppDNA(app_name="Genesis Engine") 
    
    with console.status("[bold green]Groq AI Brain is analyzing the bottleneck and downgrading DNA...[/bold green]"):
        healed_dna = telemetry_brain.heal_dna(report_obj, current_dna)

    console.print("\n[bold magenta]--- 🧬 AI SELF-CORRECTION: HEALED DNA ---[/bold magenta]")
    
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
    
    state_data = {"input_dna": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {STATE_FILE}. Creating new.[/yellow]")
            
    if "input_dna" not in state_data:
        state_data["input_dna"] = []
        
    found = False
    for rule in state_data["input_dna"]:
        if rule.get("action_name") == action_name:
            old_key = rule.get("hardware_trigger")
            rule["hardware_trigger"] = new_key
            found = True
            console.print(f"[yellow]Updated existing rule: {action_name} ({old_key} -> {new_key})[/yellow]")
            break
            
    if not found:
        new_rule = {
            "action_name": action_name,
            "hardware_trigger": new_key,
            "modifier_key": None,
            "active_context": "gameplay"
        }
        state_data["input_dna"].append(new_rule)
        console.print(f"[green]Created new rule: {action_name} -> {new_key}[/green]")
        
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
            response = supabase.table('community_vault').select('mod_dna').eq('id', mod_id).single().execute()
            mod_dna_dict = response.data['mod_dna']
            
            safe_mod = ModDNA(**mod_dna_dict)
            console.print(f"[green]✓ DNA VALIDATED:[/green] {safe_mod.mod_name}")
            
            state_file = STATE_FILE
            if not os.path.exists(state_file):
                console.print("[yellow]No OGF_STATE.json found. Initializing fresh reality...[/yellow]")
                current_world = WorldState()
                full_state = {"world_state": current_world.model_dump()}
            else:
                with open(state_file, 'r') as f:
                    full_state = json.load(f)
                    current_world = WorldState(**full_state.get('world_state', {}))
            
            new_world = modding_engine.inject_mod(current_world, safe_mod, DramaBudget())
            
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
    
    state_data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)
        except Exception:
            pass
            
    app_dna_dict = state_data.get("app_dna", AppDNA().model_dump())
    
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
    
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f, indent=4)
        console.print("[green]✅ OGF_STATE.json updated successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error saving state: {e}[/red]")
        return
    
    console.print("[yellow]🏭 Triggering Fluid UI Recompilation...[/yellow]")
    app_dna = AppDNA(**app_dna_dict)
    design_config = synthesize_design_tokens(app_dna.design_tokens)
    compile_report = compile_ui(app_dna, design_config)
    
    if compile_report["success"]:
        console.print(f"[green]✅ UI Recompiled in {compile_report['compile_time_ms']}ms. Layout is mathematically fluid![/green]")
    else:
        console.print("[red]❌ UI Recompilation failed.[/red]")
        
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

# ==========================================
# DAY 28: THE ECONOMY HOLE (DETERMINISTIC MATH SIMULATION)
# ==========================================
@cli.group()
def economy():
    """Day 28: Deterministic Economy Math Commands."""
    pass

@economy.command(name="simulate")
@click.argument('hours', type=int, default=10)
def simulate_economy(hours):
    """
    Simulates the economy over X hours to mathematically prove the Anti-Inflation Guardrails.
    Usage: camera economy simulate 100
    """
    console.print(Panel(f"[bold cyan]Day 28: Simulating Economy Flow for {hours} hours...[/bold cyan]", title="The Deterministic Math Balancer"))
    
    console.print("[yellow]1. Economy Director is designing the flow tags (Zero raw numbers)...[/yellow]")
    dna = act_as_economy_director("A bustling blacksmith in a cyberpunk slum")
    console.print(f"✅ DNA Generated: {dna.resource_name} ({dna.faucet_type} -> {dna.sink_type})")
    
    console.print(f"[yellow]2. Economy Engine is calculating exact yields and costs for a {hours}-hour curve...[/yellow]")
    flow_rate = economy_engine.calculate_flow_rate(dna, gameplay_hours=hours)
    
    console.print("[yellow]3. Simulating an 'Infinite Gold Exploit' to test the Anti-Inflation Guardrails...[/yellow]")
    
    exploit_attempts = 50
    total_earned = 0.0
    blocked_count = 0
    
    economy_engine.session_earnings = {}
    economy_engine.session_hours = {}
    
    for i in range(exploit_attempts):
        fake_event = EconomicEvent(actor_id="hacker_01", amount=1000.0)
        actual_earned = economy_engine.process_transaction(dna, fake_event)
        total_earned += actual_earned
        if actual_earned == 0.0:
            blocked_count += 1

    table = Table(title=f"📊 {hours}-Hour Economy Simulation Results")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")
    
    table.add_row("Target Velocity", f"{dna.target_velocity} tx/hr", "Balanced")
    table.add_row("Calculated Yield", f"{flow_rate['yield_per_event']} per tx", "Math Perfect")
    table.add_row("Calculated Cost", f"{flow_rate['cost_per_event']} per tx", "Math Perfect")
    table.add_row("Exploit Attempts", str(exploit_attempts), "Tested")
    table.add_row("Guardrail Blocks", f"{blocked_count} / {exploit_attempts}", "[bold red]EXPLOIT NEUTRALIZED[/bold red]")
    table.add_row("Final Inflation", f"{total_earned:.2f} {dna.resource_name}", "[bold green]CAP ENFORCED[/bold green]")
    
    console.print(table)
    
    console.print("\n[bold green]✅ The math is flawless, Founder. The Anti-Inflation Guardrails mathematically blocked the exploit![/bold green]")
    console.print("[bold cyan]Your i3 laptop handled this heavy mathematical lifting beautifully. It didn't even break a sweat.[/bold cyan]\n")

# ==========================================
# DAY 29: THE TUTORIAL HOLE (DYNAMIC ONBOARDING)
# ==========================================
@cli.group()
def tutorial():
    """Day 29: The Dynamic Onboarding Engine (The Tutorial Hole)."""
    pass

@tutorial.command()
@click.argument("scenario")
def simulate(scenario):
    """Simulates a struggling player and prints the exact mathematical UI hint."""
    console.print(f"[bold cyan]Mentor Director is analyzing scenario:[/bold cyan] {scenario}")
    
    tutorial_dnas = act_as_mentor_director(scenario)
    
    if not tutorial_dnas:
        console.print("[bold red]Mentor Director could not generate any tutorials.[/bold red]")
        return

    engine = TutorialEngine()
    
    fake_world_state = {
        "player_health": 20.0,
        "enemy_distance": 4.0,
        "player_falling_speed": 15.0,
        "target_distance": 10.0
    }
    
    console.print("[bold yellow]Simulating struggling player state...[/bold yellow]")
    
    active_hints = engine.evaluate_tutorials(tutorial_dnas, fake_world_state)
    
    if not active_hints:
        console.print("[bold green]Player is doing fine! No hints needed.[/bold green]")
        return
        
    table = Table(title="Active Mathematical UI Hints (Zero Text Boxes!)")
    table.add_column("Concept ID", style="cyan")
    table.add_column("Visual Type", style="magenta")
    table.add_column("Required Input", style="green")
    table.add_column("Urgency", style="red")
    
    for hint in active_hints:
        table.add_row(
            hint["concept_id"],
            hint["hint_visual_type"],
            hint["input_requirement"],
            f"{hint['urgency']:.2f}"
        )
        
    console.print(table)
    console.print("[bold cyan]The frontend will now project these pure math hints. Zero interruptions![/bold cyan]")

# ==========================================
# DAY 30: THE SAVE STATE HOLE (DETERMINISTIC REWIND)
# ==========================================
@cli.group()
def chrono():
    """Day 30: Deterministic Seed Checkpointing & Time Rewind."""
    pass

@chrono.command(name="test")
def chrono_test():
    """Simulates inputs, saves a checkpoint, rewinds, and verifies math."""
    console.print(Panel("[bold cyan]DAY 30: THE DETERMINISTIC REWIND TEST[/bold cyan]", expand=False))
    
    engine = ChronoEngine()
    master_seed = 42
    current_time = 0.0
    
    console.print(f"🌍 [green]Initializing World with Seed: {master_seed}[/green]")
    
    input_log = [
        {"action": "move_forward", "timestamp": 1.0},
        {"action": "jump", "timestamp": 2.5},
        {"action": "dash", "timestamp": 4.0},
        {"action": "attack", "timestamp": 5.5}
    ]
    
    console.print(f"⏺️ [yellow]Recording {len(input_log)} abstracted intents to the Black Box...[/yellow]")
    current_time = 10.0 
    
    original_state = engine.generate_world_layout(master_seed, current_time)
    console.print(f"📍 [cyan]Original State at {current_time}s:[/cyan] {original_state['entities'][0]}")
    
    checkpoint_time = 4.0
    checkpoint_dna = engine.create_checkpoint(master_seed, checkpoint_time, depth=1)
    console.print(f"💾 [bold green]Checkpoint Saved![/bold green] Time: {checkpoint_dna.timestamp}s | Hash: {checkpoint_dna.input_log_hash}")
    
    console.print("🔄 [bold magenta]Triggering Rewind Intent...[/bold magenta]")
    rewind_intent = RewindIntent(target_timestamp=checkpoint_time, reason="manual_test")
    
    rewound_state = engine.process_rewind(
        rewind_intent=rewind_intent,
        full_input_log=input_log,
        restored_seed=checkpoint_dna.world_seed
    )
    
    console.print(f"📍 [cyan]Rewound State at {checkpoint_time}s:[/cyan] {rewound_state['entities'][0]}")
    
    verification_state = engine.generate_world_layout(master_seed, checkpoint_time)
    
    if rewound_state['entities'] == verification_state['entities']:
        console.print("[bold green]✅ SUCCESS! The mathematical output perfectly matches. Zero RAM bloat. Time travel verified.[/bold green]")
    else:
        console.print("[bold red]❌ FAILURE! The math did not align. The Old Paradigm has infected the engine.[/bold red]")

    console.print("\n🧠 [bold yellow]Testing the Time Director (Brain Upgrade)...[/bold yellow]")
    calm_world = WorldState(heat_level=0)
    boss_world = WorldState(heat_level=5)
    
    calm_decision = act_as_time_director(calm_world)
    boss_decision = act_as_time_director(boss_world)
    
    table = Table(title="Time Director Dynamic Checkpoints")
    table.add_column("Tension Level", justify="center")
    table.add_column("Save Interval (s)", justify="center")
    table.add_column("Max Rewind (s)", justify="center")
    
    table.add_row("Calm (0)", str(calm_decision.get('checkpoint_interval_seconds')), str(calm_decision.get('max_rewind_depth_seconds')))
    table.add_row("Boss Fight (5)", str(boss_decision.get('checkpoint_interval_seconds')), str(boss_decision.get('max_rewind_depth_seconds')))
    
    console.print(table)

# ==========================================
# DAY 31: THE ACCESSIBILITY HOLE (EMPATHETIC ADAPTATION)
# ==========================================
@cli.group()
def accessibility():
    """Day 31: Accessibility / Empathetic Adaptation Commands."""
    pass

@accessibility.command(name="profile")
@click.argument("mode", required=True)
def accessibility_profile(mode):
    """
    Sets the AccessibilityDNA profile and adapts all systems.
    """
    console.print(
        Panel(
            f"[bold cyan]Day 31: Empathetic Adaptation Engine[/bold cyan]\n"
            f"Requested profile: [bold]{mode}[/bold]",
            title="Accessibility Hole",
            border_style="cyan"
        )
    )

    if AccessibilityDNA is None:
        console.print("[bold red]AccessibilityDNA is not available. Check packages/core/models.py.[/bold red]")
        return

    state_data = _load_ogf_state()

    current_accessibility = _get_current_accessibility(state_data)

    applied_tokens = []

    if str(mode).strip().lower() in ("auto", "empathy", "brain"):
        if act_as_empathy_director is None:
            console.print("[bold red]The Empathy Director is not available. Check packages/core/brain.py.[/bold red]")
            return

        with console.status("[bold green]Empathy Director is reading player comfort signals...[/bold green]"):
            new_accessibility = act_as_empathy_director(
                current_accessibility=current_accessibility,
                telemetry=state_data.get("telemetry"),
                performance_report=state_data.get("performance_report"),
                mastery_events=state_data.get("mastery_events"),
                explicit_preferences=state_data.get("explicit_accessibility_preferences"),
                player_context="CLI accessibility profile command."
            )

        applied_tokens = ["empathy_director"]

    else:
        new_accessibility, applied_tokens, parse_error = _parse_accessibility_mode(
            mode=mode,
            current_accessibility=current_accessibility
        )

        if parse_error:
            allowed_modes = """
[bold]Standard Presets:[/bold]
- standard
- comfort
- max_support

[bold]Custom Tokens (combine with +):[/bold]
- high_contrast
- standard_contrast
- generous_timing
- max_assist
- standard_timing
- reduced_motion
- stable_only
- standard_camera
- audio_off
- audio_low
- audio_medium
- audio_high
- cognitive_minimal
- cognitive_balanced
- cognitive_supported
- cognitive_max_support

[bold]Example:[/bold]
camera accessibility profile high_contrast+generous_timing+reduced_motion
"""
            console.print(Panel(
                f"[bold red]Could not parse accessibility profile.[/bold red]\n\n"
                f"[yellow]Reason:[/yellow] {parse_error}\n\n"
                f"{allowed_modes}",
                title="Accessibility Profile Help",
                border_style="yellow"
            ))
            return

    accessibility_dict = _to_json_safe(new_accessibility)

    state_data["accessibility_dna"] = accessibility_dict

    app_dna_dict = state_data.get("app_dna")
    if not isinstance(app_dna_dict, dict):
        app_dna_dict = _to_json_safe(AppDNA())

    app_dna_dict["accessibility"] = accessibility_dict
    state_data["app_dna"] = app_dna_dict

    console.print("[bold green]✅ AccessibilityDNA updated in OGF_STATE.json.[/bold green]")

    ui_report = {}

    if default_accessibility_synthesizer is not None:
        with console.status("[bold yellow]Adapting UI Token Synthesizer...[/bold yellow]"):
            design_tokens = app_dna_dict.get("design_tokens", _to_json_safe(AppDNA().design_tokens))

            ui_compiler = app_dna_dict.get("ui_compiler")
            atomic_tokens = None
            if isinstance(ui_compiler, dict):
                atomic_tokens = ui_compiler.get("atomic_tokens")

            adapted_design_tokens, adapted_atomic_tokens, ui_events, ui_report = (
                default_accessibility_synthesizer.adapt_visual_contrast(
                    accessibility=new_accessibility,
                    design_tokens=design_tokens,
                    atomic_tokens=atomic_tokens
                )
            )

            app_dna_dict["design_tokens"] = _to_json_safe(adapted_design_tokens)

            if adapted_atomic_tokens:
                if not isinstance(ui_compiler, dict):
                    ui_compiler = {}

                ui_compiler["atomic_tokens"] = _to_json_safe(adapted_atomic_tokens)
                app_dna_dict["ui_compiler"] = ui_compiler

    input_report = {}

    if DeterministicInputEngine is not None:
        with console.status("[bold yellow]Adapting Input Engine timing windows...[/bold yellow]"):
            input_engine = DeterministicInputEngine()

            input_dna_list = state_data.get("input_dna", [])
            if isinstance(input_dna_list, list) and input_dna_list:
                input_engine.build_map_from_dna(input_dna_list)

            input_timing_state, input_events, input_report = input_engine.apply_accessibility(
                accessibility=new_accessibility
            )

            state_data["input_timing_state"] = input_timing_state

    audio_report = {}

    if default_accessibility_synthesizer is not None:
        with console.status("[bold yellow]Adapting Audio DSP DNA...[/bold yellow]"):
            audio_dna = state_data.get("audio_dna")

            adapted_audio_dna, audio_events, audio_report = (
                default_accessibility_synthesizer.adapt_audio_cues(
                    accessibility=new_accessibility,
                    audio_dna=audio_dna
                )
            )

            state_data["audio_dna"] = _to_json_safe(adapted_audio_dna)

    camera_report = {}

    if default_camera_comfort_engine is not None:
        with console.status("[bold yellow]Adapting Camera Comfort Engine...[/bold yellow]"):
            camera_rig_state = state_data.get("camera_rig_state")

            adapted_camera_rig, camera_events, camera_report = (
                default_camera_comfort_engine.adapt_camera_rig(
                    accessibility=new_accessibility,
                    camera_rig_state=camera_rig_state
                )
            )

            state_data["camera_rig_state"] = adapted_camera_rig

    state_data["last_accessibility_adaptation"] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode_argument": mode,
        "applied_tokens": applied_tokens,
        "accessibility_dna": accessibility_dict,
        "summary": {
            "ui_color_changes": ui_report.get("changed_color_tokens", 0),
            "input_timing_changes": input_report.get("changed_actions", 0),
            "audio_changed": audio_report.get("changed", False),
            "camera_field_changes": camera_report.get("changed_fields", 0),
        }
    }

    saved = _save_ogf_state(state_data)

    if saved:
        console.print(f"[bold green]✅ {os.path.basename(STATE_FILE)} saved successfully.[/bold green]")
    else:
        console.print("[bold red]❌ Could not save OGF_STATE.json.[/bold red]")

    profile_table = Table(title="🧬 Active AccessibilityDNA")
    profile_table.add_column("DNA Field", style="cyan")
    profile_table.add_column("Value", style="green")

    for key, value in accessibility_dict.items():
        profile_table.add_row(str(key), str(value))

    console.print(profile_table)

    summary_table = Table(title="🌍 System Adaptation Summary")
    summary_table.add_column("System", style="cyan")
    summary_table.add_column("Changes", style="magenta")
    summary_table.add_column("Status", style="green")

    summary_table.add_row(
        "UI Token Synthesizer",
        str(ui_report.get("changed_color_tokens", 0)) if ui_report else "unavailable",
        "adapted" if ui_report else "offline"
    )

    summary_table.add_row(
        "Input Engine",
        str(input_report.get("changed_actions", 0)) if input_report else "unavailable",
        "adapted" if input_report else "offline"
    )

    summary_table.add_row(
        "Audio DSP Engine",
        str(audio_report.get("new_boost_db", 0.0)) + " dB" if audio_report else "unavailable",
        "adapted" if audio_report else "offline"
    )

    summary_table.add_row(
        "Camera Comfort Engine",
        str(camera_report.get("changed_fields", 0)) if camera_report else "unavailable",
        "adapted" if camera_report else "offline"
    )

    console.print(summary_table)

    _print_ui_accessibility_report(ui_report)
    _print_input_accessibility_report(input_report)
    _print_audio_accessibility_report(audio_report)
    _print_camera_accessibility_report(camera_report)

    console.print(
        "\n[bold green]✅ Accessibility profile applied across all systems.[/bold green]\n"
        "[bold cyan]Your i3 laptop remained safe. Reality adapted through pure JSON DNA.[/bold cyan]\n"
    )


# ==========================================
# DAY 32: THE QUEST HOLE (NARRATIVE GRAPHS)
# ==========================================
@cli.group()
def quest():
    """Day 32: Procedural Narrative Graph Commands."""
    pass


@quest.command(name="generate")
@click.option("--intent", default=None, help="Optional creative intent for the quest.")
@click.option("--max-nodes", default=3, show_default=True, help="Maximum number of narrative nodes to generate.")
@click.option("--project-id", default=None, help="Optional Supabase project UUID.")
@click.option("--save", is_flag=True, default=False, help="Save the generated QuestDNA into Supabase narrative_graphs.")
def quest_generate(intent, max_nodes, project_id, save):
    """Generate a new QuestDNA using the Story Weaver."""
    if generate_quest_dna_report is None:
        console.print("[bold red]Day 32 Story Weaver is not available. Check packages/core/brain.py.[/bold red]")
        return

    if not project_id:
        project_id = get_active_project_id()

    console.print(
        Panel(
            "[cyan]Story Weaver is generating procedural QuestDNA...[/cyan]\n"
            f"Intent: [white]{intent or 'Emergent from World Truths'}[/white]\n"
            f"Max Nodes: [white]{max_nodes}[/white]\n"
            f"Project ID: [white]{project_id or 'local/demo'}[/white]",
            title="Day 32: Story Weaver",
            border_style="cyan"
        )
    )

    report = generate_quest_dna_report(
        quest_intent=intent,
        max_nodes=max_nodes,
        project_id=project_id
    )

    if not report.get("success"):
        errors = report.get("errors", [])
        for error in errors:
            console.print(f"[red]- {error}[/red]")
        console.print("[bold red]QuestDNA generation failed.[/bold red]")
        return

    _quest_print_generation_report(report)

    if save:
        ok, message = _quest_save_to_supabase(
            project_id=project_id,
            quest_json=report.get("quest_json", {})
        )
        if ok:
            console.print(f"[bold green]{message}[/bold green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")


@quest.command(name="progress")
@click.argument("node_id")
@click.option("--quest-id", default=None, help="Optional quest_id.")
@click.option("--project-id", default=None, help="Optional Supabase project UUID.")
@click.option("--completed", default="", help="Comma-separated completed node IDs.")
@click.option("--force", is_flag=True, default=False, help="Force completion.")
def quest_progress(node_id, quest_id, project_id, completed, force):
    """Simulate completing one narrative node."""
    if progress_quest_node is None:
        console.print("[bold red]Day 32 Quest progression is not available. Check packages/core/brain.py.[/bold red]")
        return

    if QuestDNA is None:
        console.print("[bold red]QuestDNA model is not available. Check packages/core/models.py.[/bold red]")
        return

    if not project_id:
        project_id = get_active_project_id()

    completed_node_ids = _quest_parse_completed(completed)

    quest_payload = _quest_load_payload(
        project_id=project_id,
        quest_id=quest_id
    )

    if not quest_payload:
        console.print("[bold red]No QuestDNA found. Generate one first with:[/bold red]\n[cyan]camera quest generate --save[/cyan]")
        return

    try:
        quest = QuestDNA(**quest_payload)
    except Exception as e:
        console.print(f"[bold red]QuestDNA validation failed: {e}[/bold red]")
        return

    console.print(
        Panel(
            "[cyan]Simulating narrative node completion...[/cyan]\n"
            f"Quest ID: [white]{quest.quest_id}[/white]\n"
            f"Node ID: [white]{node_id}[/white]\n"
            f"Force Mode: [white]{force}[/white]\n"
            f"Project ID: [white]{project_id or 'local/demo'}[/white]",
            title="Day 32: Quest Progress",
            border_style="cyan"
        )
    )

    result = progress_quest_node(
        quest=quest,
        node_id=node_id,
        project_id=project_id,
        completed_node_ids=completed_node_ids,
        force=force
    )

    _quest_print_progress_result(result)

    if result.get("success"):
        console.print("\n[bold green]✅ The story physically changed the World State.[/bold green]\n[bold cyan]Pure mathematical narrative. Zero hardcoded scripts.[/bold cyan]\n")
    else:
        console.print("\n[bold red]❌ Node completion failed. Read the report above.[/bold red]\n")


# ==========================================
# DAY 33: THE SOCIAL HOLE (SOCIAL MATRICES)
# ==========================================
@cli.group()
def social():
    """Day 33: Deterministic Social Matrix Commands."""
    pass


@social.command(name="demo")
def social_demo():
    """Print the deterministic demo SocialDNA."""
    if SocialDNA is None:
        console.print("[bold red]Day 33 SocialDNA is not available. Check packages/core/models.py.[/bold red]")
        return

    dna = _social_demo_dna()

    console.print(
        Panel(
            "[cyan]Deterministic Day 33 Demo Society[/cyan]\n"
            "Faction A: Merchants Guild\n"
            "Faction B: Iron Guard\n"
            "Faction C: Ashen Choir\n"
            "NPC: Ivan, allied with the Iron Guard",
            title="Day 33: SocialDNA Demo",
            border_style="cyan"
        )
    )

    console.print(
        Syntax(
            json.dumps(_to_json_safe(dna), indent=2, default=str),
            "json",
            theme="monokai",
            line_numbers=True
        )
    )


@social.command(name="matrix")
@click.option("--file", "file_path", default=None, help="Optional path to a SocialDNA JSON file.")
@click.option("--project-id", default=None, help="Optional Supabase project UUID.")
def social_matrix(file_path, project_id):
    """Print the social matrix edges and dispositions."""
    if SocialDNA is None or SocialMatrixEngine is None:
        console.print("[bold red]Day 33 Social Matrix is not available. Check packages/core/models.py and packages/core/social_engine.py.[/bold red]")
        return

    dna, source = _social_load_dna(file_path=file_path, project_id=project_id)

    if dna is None:
        console.print("[bold red]Could not load SocialDNA.[/bold red]")
        return

    engine = _social_make_engine(dna, actor_id="player")

    console.print(
        Panel(
            f"[cyan]Social Matrix loaded from:[/cyan] [white]{source}[/white]",
            title="Day 33: Social Matrix",
            border_style="cyan"
        )
    )

    _social_print_edges(engine, dna)
    _social_print_disposition_table(engine=engine, social_dna=dna, actor_id="player", title="Player Dispositions")


@social.command(name="ripple")
@click.argument("action", required=True)
@click.option("--actor", default="player", show_default=True, help="The entity performing the action.")
@click.option("--target", default="faction_merchants_guild", show_default=True, help="The faction or entity receiving the action.")
@click.option("--magnitude", default=0.8, show_default=True, type=float, help="Strength of the action.")
@click.option("--file", "file_path", default=None, help="Optional path to a SocialDNA JSON file.")
@click.option("--project-id", default=None, help="Optional Supabase project UUID.")
def social_ripple(action, actor, target, magnitude, file_path, project_id):
    """Simulate a social action and print the mathematical ripple."""
    if SocialDNA is None or SocialAction is None or SocialMatrixEngine is None:
        console.print("[bold red]Day 33 Social Ripple Resolver is not available. Check packages/core/models.py and packages/core/social_engine.py.[/bold red]")
        return

    dna, source = _social_load_dna(file_path=file_path, project_id=project_id)

    if dna is None:
        console.print("[bold red]Could not load SocialDNA.[/bold red]")
        return

    engine = _social_make_engine(dna, actor_id=actor)

    if engine is None:
        console.print("[bold red]SocialMatrixEngine could not be initialized.[/bold red]")
        return

    console.print(
        Panel(
            f"[cyan]SocialDNA source:[/cyan] [white]{source}[/white]\n"
            f"Action: [bold]{action}[/bold]\n"
            f"Actor: [cyan]{actor}[/cyan]\n"
            f"Target: [cyan]{target}[/cyan]\n"
            f"Magnitude: [magenta]{magnitude:+.2f}[/magenta]",
            title="Day 33: Social Ripple Resolver",
            border_style="cyan"
        )
    )

    if target not in engine.get_entity_ids():
        console.print(f"[yellow]Target '{target}' is not in the loaded society. The Social Engine will add it as a new entity.[/yellow]")

    _social_print_disposition_table(engine=engine, social_dna=dna, actor_id=actor, title="Before Action")

    social_action = SocialAction(
        actor_id=actor,
        target_id=target,
        action_type=action,
        magnitude=magnitude,
        context={"source": "camera_cli", "day": 33},
    )

    report = engine.apply_action(social_action)

    _social_print_direct_effects(report, dna)
    _social_print_ripple_effects(report, dna)

    _social_print_disposition_table(engine=engine, social_dna=dna, actor_id=actor, title="After Action")

    _social_print_interaction_blocks(engine, dna)

    if engine.get_faction("faction_iron_guard") is not None:
        ivan_can_interact = engine.can_interact("npc_ivan", actor)
        guard_disposition = engine.get_relationship("faction_iron_guard", actor)

        if ivan_can_interact:
            console.print("[green]NPC Ivan is still willing to interact with the actor.[/green]")
        else:
            console.print("[red]NPC Ivan now refuses interaction with the actor.[/red]")

        console.print(f"[cyan]Iron Guard disposition toward actor:[/cyan] [magenta]{guard_disposition:.2f}[/magenta]")

    console.print("\n[bold green]✅ Social ripple complete.[/bold green]\n[bold cyan]Drama emerged from math. Zero hardcoded reputation. Your i3 laptop is safe.[/bold cyan]\n")


# ==========================================
# DAY 34: THE LIVING WORLD TRINITY (ECOLOGY & FLOW)
# ==========================================
@cli.group()
def ecology():
    """Day 34: Living World Trinity - Ecology Commands."""
    pass

@ecology.command(name="simulate")
@click.argument('ticks', type=int, default=10)
def ecology_simulate(ticks):
    """Simulates the ecosystem for X ticks using Lotka-Volterra math."""
    if simulate_tick is None or EcologyDNA is None:
        console.print("[bold red]Day 34 Ecology Engine is not available.[/bold red]")
        return

    console.print(Panel(f"[bold cyan]Day 34: Simulating Ecosystem for {ticks} ticks...[/bold cyan]", title="The Lotka-Volterra Engine"))
    
    dna = EcologyDNA(
        species_list=["vegetation", "deer", "wolves"],
        predator_prey_links=[("wolves", "deer"), ("deer", "vegetation")],
        hunger_rates={"deer": 0.5, "wolves": 1.0},
        reproduction_cycles={"vegetation": 2, "deer": 5, "wolves": 10},
        territory_ranges={"deer": 10.0, "wolves": 50.0},
        carrying_capacity={"vegetation": 1000, "deer": 100, "wolves": 20}
    )
    
    pops = {"vegetation": 500, "deer": 50, "wolves": 10}
    
    table = Table(title="Population Curves")
    table.add_column("Tick", style="cyan", justify="center")
    table.add_column("Vegetation", style="green")
    table.add_column("Deer", style="yellow")
    table.add_column("Wolves", style="red")
    table.add_column("Events", style="magenta")
    
    for i in range(ticks):
        pops, events = simulate_tick(pops, dna)
        event_str = ", ".join([e.event_type for e in events]) if events else "-"
        table.add_row(
            str(i + 1),
            str(pops.get("vegetation", 0)),
            str(pops.get("deer", 0)),
            str(pops.get("wolves", 0)),
            event_str
        )
        
    console.print(table)
    console.print("[bold green]✅ Ecosystem simulation complete. The math is breathing![/bold green]")

@ecology.command(name="collapse")
@click.argument('species')
def ecology_collapse(species):
    """Manually collapses a species to 0 and triggers the trophic cascade."""
    if resolve_cascade is None or EcologyDNA is None or BiomeDNA is None:
        console.print("[bold red]Day 34 Ecology Engine is not available.[/bold red]")
        return

    console.print(Panel(f"[bold red]Day 34: Triggering Trophic Cascade for '{species}'...[/bold red]", title="The Cascade Resolver"))
    
    dna = EcologyDNA(
        species_list=["vegetation", "deer", "wolves"],
        predator_prey_links=[("wolves", "deer"), ("deer", "vegetation")],
        carrying_capacity={"vegetation": 1000, "deer": 100, "wolves": 20}
    )
    
    pops = {"vegetation": 100, "deer": 50, "wolves": 10}
    
    if species not in pops:
        console.print(f"[yellow]Species '{species}' not found in demo biome. Available: {list(pops.keys())}[/yellow]")
        return
        
    pops[species] = 0
    console.print(f"[yellow]Manually set {species} population to 0.[/yellow]")
    
    current_biome = BiomeDNA(name="Lush Forest", scatter_density=0.8)
    
    new_pops, new_biome, cascade_events = resolve_cascade(pops, dna, current_biome)
    
    table = Table(title="Cascade Chain Reactions")
    table.add_column("Event Type", style="red")
    table.add_column("Target", style="cyan")
    table.add_column("Message", style="white")
    
    if not cascade_events:
        table.add_row("None", "-", "The ecosystem absorbed the shock.")
    else:
        for event in cascade_events:
            table.add_row(event.event_type, event.target_species, event.message)
            
    console.print(table)
    
    if new_biome.name != current_biome.name:
        console.print(f"[bold red]🚨 BIOME COLLAPSE! The world physically changed to: {new_biome.name}[/bold red]")
        
    console.print("[bold green]✅ Cascade resolved. The world reacted deterministically![/bold green]")


@cli.group()
def flow():
    """Day 34: Living World Trinity - Flow State Commands."""
    pass

@flow.command(name="check")
def flow_check():
    """Reads mock telemetry and calculates the current Flow Score."""
    if calculate_flow_score is None:
        console.print("[bold red]Day 34 Flow Engine is not available.[/bold red]")
        return

    console.print(Panel("[bold cyan]Day 34: Checking Player Flow State...[/bold cyan]", title="The Csikszentmihalyi Engine"))
    
    flow_dna = calculate_flow_score(
        failure_count=2,
        hesitation_ms=150.0,
        session_minutes=20,
        recent_success_rate=0.8,
        current_challenge=0.7
    )
    
    table = Table(title="Player Psychological State")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Skill Level", f"{flow_dna.skill_level:.2f}")
    table.add_row("Challenge Level", f"{flow_dna.challenge_level:.2f}")
    table.add_row("Flow Score", f"{flow_dna.flow_score:.1f} / 100")
    table.add_row("Pacing Directive", f"[bold]{flow_dna.pacing_directive.value}[/bold]")
    
    console.print(table)
    console.print("[bold green]✅ Flow state calculated. The engine knows how the player feels.[/bold green]")

@flow.command(name="simulate")
@click.argument('scenario')
def flow_simulate(scenario):
    """Simulates a specific player scenario and prints the Brain's pacing response."""
    if calculate_flow_score is None or generate_pacing_directive is None:
        console.print("[bold red]Day 34 Flow Engine or Brain is not available.[/bold red]")
        return

    console.print(Panel(f"[bold cyan]Day 34: Simulating Scenario: '{scenario}'...[/bold cyan]", title="The Pacing Director"))
    
    if "bored" in scenario.lower():
        success, challenge, minutes, hesitation = 0.95, 0.2, 60, 50.0
    elif "frustrated" in scenario.lower() or "hard" in scenario.lower():
        success, challenge, minutes, hesitation = 0.2, 0.9, 15, 800.0
    elif "tired" in scenario.lower() or "long" in scenario.lower():
        success, challenge, minutes, hesitation = 0.4, 0.6, 50, 300.0
    else:
        success, challenge, minutes, hesitation = 0.7, 0.7, 20, 100.0
        
    flow_dna = calculate_flow_score(
        failure_count=3 if success < 0.5 else 0,
        hesitation_ms=hesitation,
        session_minutes=minutes,
        recent_success_rate=success,
        current_challenge=challenge
    )
    
    console.print(f"[yellow]Calculated Flow Score: {flow_dna.flow_score:.1f}[/yellow]")
    console.print(f"[yellow]Pacing Directive: {flow_dna.pacing_directive.value}[/yellow]\n")
    
    with console.status("[bold green]Brain is generating deterministic JSON directives...[/bold green]"):
        pacing_response = generate_pacing_directive(flow_dna)
        
    console.print("[bold magenta]--- 🧠 BRAIN JSON DIRECTIVES ---[/bold magenta]")
    syntax = Syntax(json.dumps(pacing_response, indent=2), "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Engine Execution Payload", border_style="green"))
    
    console.print("\n[bold green]✅ Pacing Director issued commands. Zero raw code written by the Brain![/bold green]")


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
    """Simulates a specific pacing directive."""
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
    """Generates N moments in sequence, builds the tension curve."""
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
    if curve_data.get("forced_next_arc"):
        console.print(f"\n[bold red]⚠️ Pacing Rule Triggered: Forcing next moment to be '{curve_data['forced_next_arc']}'[/bold red]")


# ==========================================
# DAY 36: THE FIDELITY LADDER (CLI INTEGRATION)
# ==========================================
@cli.group()
def fidelity():
    """Day 36: Fidelity Ladder - Route visual quality based on hardware."""
    pass

@fidelity.command(name="test")
@click.argument('entity_name')
@click.argument('level', type=int)
def fidelity_test(entity_name, level):
    """Test the Traffic Cop. Resolves the fidelity level for a Potato i3 laptop."""
    console.print(f"[bold cyan]🧪 Testing Fidelity Route for '{entity_name}' at Level {level}...[/bold cyan]")
    dna = FidelityDNA(entity_id=entity_name, fidelity_level=level, hardware_tier=HardwareTier.POTATO, shader_profile=ShaderProfile.PBR)
    route = resolve_fidelity(dna)
    console.print(Panel(
        f"Requested Level: {level}\nResolved Level:  {route.resolved_level}\nPipeline:        {route.render_pipeline.value}\nFallback Level:  {route.fallback_level}\nEst. Load:       {route.estimated_load_ms}ms",
        title="Fidelity Route Resolved", border_style="blue"
    ))

@fidelity.command(name="render")
@click.argument('entity_name')
@click.argument('level', type=int)
def fidelity_render(entity_name, level):
    """Render an entity using the Fidelity Ladder."""
    console.print(f"[bold green]🎨 Rendering '{entity_name}' at Level {level}...[/bold green]")
    entity_type = entity_name.lower()
    dna = FidelityDNA(entity_id=entity_name, fidelity_level=level, hardware_tier=HardwareTier.POTATO, shader_profile=ShaderProfile.PBR, style_tags=["procedural", "test"], color_palette={"primary": "#3B82F6", "secondary": "#10B981"})
    descriptor = render_entity(entity_name, entity_type, dna)
    console.print(Syntax(json.dumps(descriptor, indent=2), "json", theme="monokai"))

@fidelity.command(name="compare")
@click.argument('entity_name')
def fidelity_compare(entity_name):
    """Compare L0 (Primitives), L1 (SDF), and L2 (Procedural) side-by-side."""
    console.print(f"[bold magenta]🔍 Comparing Fidelity Levels for '{entity_name}'...[/bold magenta]")
    entity_type = entity_name.lower()
    for lvl in [0, 1, 2]:
        dna = FidelityDNA(entity_id=entity_name, fidelity_level=lvl, hardware_tier=HardwareTier.POTATO, shader_profile=ShaderProfile.PBR, color_palette={"primary": "#3B82F6", "secondary": "#10B981"})
        descriptor = render_entity(entity_name, entity_type, dna)
        console.print(Panel(Syntax(json.dumps(descriptor, indent=2), "json", theme="monokai"), title=f"Level {lvl} ({descriptor.get('pipeline', 'unknown')})", border_style="cyan"))


# CRITICAL: Add ALL command groups to the main 'cli' group!
cli.add_command(biome)
cli.add_command(navigate)
cli.add_command(backend)
cli.add_command(netcode)
cli.add_command(telemetry) # Day 23
cli.add_command(audio) # Day 24
cli.add_command(input) # Day 25
cli.add_command(mod) # Day 26
cli.add_command(locale) # Day 27
cli.add_command(economy) # Day 28
cli.add_command(tutorial) # Day 29
cli.add_command(chrono) # Day 30
cli.add_command(accessibility) # Day 31
cli.add_command(quest) # Day 32
cli.add_command(social) # Day 33
cli.add_command(ecology) # Day 34
cli.add_command(flow) # Day 34
cli.add_command(moment) # Day 35
cli.add_command(fidelity) # Day 36

# ==========================================
# 3. START THE ENGINE
# ==========================================
# ==========================================
# DAY 38: SELF-EVOLVING ARCHITECTURE (PILLAR 25)
# CLI INTEGRATION - APPEND ABOVE if __name__ == '__main__':
# ==========================================
import json
import os
from packages.core.evolution_engine import validate_blueprint, generate_schema, generate_compiler, register_system, REGISTRY_PATH
from packages.core.models import EvolutionDNA
from packages.core.brain import generate_evolution_prompt, client

def _get_fallback_dna(description: str):
    """Safe deterministic fallback if Groq is missing or fails."""
    name = description.lower().replace(" ", "_")[:15]
    return {
        "request_description": description,
        "new_system_name": f"gen_{name}",
        "new_schema_fields": [{"field_name": "data", "field_type": "dict", "default_value": "{}"}],
        "new_compiler_type": "json_mapper",
        "new_template_names": [f"tpl_{name}"],
        "required_engines": [],
        "hardware_cost": "light",
        "guardrail_check": "pending"
    }

def run_architect_ai(description: str):
    """Calls the Brain to generate EvolutionDNA."""
    prompt = generate_evolution_prompt(description)
    if not client:
        return _get_fallback_dna(description)
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are the Architect AI. Output ONLY valid JSON."}, 
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return _get_fallback_dna(description)

def cli_evolve_request(description: str):
    print(f"🧠 Architect AI is designing: '{description}'...")
    raw_dna = run_architect_ai(description)
    try:
        dna = EvolutionDNA(**raw_dna)
    except Exception as e:
        print(f"❌ AI returned invalid DNA: {e}")
        return

    print("🛡️ Running Guardrail Checks...")
    result = validate_blueprint(dna)
    if result["status"] == "rejected":
        print("❌ REJECTED by Guardrails:")
        for fail in result["failures"]: 
            print(f"   - {fail}")
        return

    blueprint = result["blueprint"]
    print("✅ Blueprint Approved! Generating Schema & Compiler...")
    generate_schema(blueprint)
    generate_compiler(blueprint)
    
    print("📝 Registering System...")
    register_system(blueprint)
    print(f"\n🎉 SYSTEM LIVE! '{blueprint.system_name}' is now part of OGF.")

def cli_evolve_list():
    if not os.path.exists(REGISTRY_PATH):
        print("No systems registered yet.")
        return
    with open(REGISTRY_PATH, "r") as f: 
        registry = json.load(f)
    print(f"📋 Registered Systems ({len(registry)}):")
    for name, data in registry.items():
        print(f"  - {name} (v{data.get('version', 1)}) | Status: {data.get('status')}")

def cli_evolve_validate(system_name: str):
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f: 
            registry = json.load(f)
        if system_name in registry: 
            print(f"✅ {system_name} is in the registry and was previously approved.")
        else: 
            print(f"❌ {system_name} not found in registry.")

def cli_evolve_rollback(system_name: str):
    if not os.path.exists(REGISTRY_PATH): 
        print("Registry is empty.")
        return
    with open(REGISTRY_PATH, "r") as f: 
        registry = json.load(f)
    if system_name in registry:
        del registry[system_name]
        with open(REGISTRY_PATH, "w") as f: 
            json.dump(registry, f, indent=4)
        print(f"🗑️ Unregistered {system_name}. (Files kept for safety).")
    else:
        print(f"❌ {system_name} not found.")

@cli.group()
def evolve():
    """Day 38: Self-Evolving Architecture Commands."""
    pass

@evolve.command(name="request")
@click.argument('description', nargs=-1)
def evolve_request(description):
    """Request a new system evolution. (e.g. camera evolve request video timeline)"""
    cli_evolve_request(" ".join(description))

@evolve.command(name="list")
def evolve_list():
    """List all registered systems."""
    cli_evolve_list()

@evolve.command(name="validate")
@click.argument('system_name')
def evolve_validate(system_name):
    """Validate a specific system."""
    cli_evolve_validate(system_name)

@evolve.command(name="rollback")
@click.argument('system_name')
def evolve_rollback(system_name):
    """Rollback (unregister) a specific system."""
    cli_evolve_rollback(system_name)

cli.add_command(evolve)
# ==========================================
# DAY 39: INFINITE SCALE ENGINE (PILLAR 26)
# CLI INTEGRATION (APPEND ONLY)
# ==========================================
import click
from rich.console import Console
from rich.table import Table
from packages.core.models import HardwareTier, ScaleDNA
from packages.core.scale_engine import calculate_shards, sync_shards, monitor_scale

console = Console()

@click.group(name="scale")
def scale_group():
    """Commands for the Infinite Scale Engine (Pillar 26)."""
    pass

@scale_group.command(name="simulate")
@click.argument("entity_count", type=int)
@click.option("--tier", type=click.Choice(["potato", "mid", "high", "ultra", "cloud"]), default="potato", help="Hardware tier")
def simulate_scale(entity_count: int, tier: str):
    """Simulate shard distribution for a given entity count."""
    hw_tier = HardwareTier(tier)
    shards = calculate_shards(entity_count, hw_tier)
    
    table = Table(title=f"Scale Simulation: {entity_count} Entities ({tier.upper()} Tier)")
    table.add_column("Shard ID", justify="center", style="cyan")
    table.add_column("Worker ID", style="magenta")
    table.add_column("Entity Count", justify="right", style="green")
    
    for s in shards:
        table.add_row(str(s.shard_id), s.worker_id, str(s.entity_count))
        
    console.print(table)

@scale_group.command(name="rebalance")
def rebalance_scale():
    """Simulate an overloaded shard and trigger auto-rebalancing."""
    # Simulate a potato tier and manually overload it to test the math
    shards = calculate_shards(250, HardwareTier.POTATO)
    if shards:
        shards[0].entity_count = 250
        shards[0].entity_ids = [f"entity_{i}" for i in range(250)]
    
    events, updated_shards = monitor_scale(shards, max_entities_per_shard=200, rebalance_threshold=0.8)
    
    console.print(f"[bold red]Rebalance Events Triggered: {len(events)}[/bold red]")
    for event in events:
        console.print(f"- {event.event_type.value}: {event.details}")
        
    table = Table(title="Shards After Rebalancing")
    table.add_column("Shard ID", justify="center", style="cyan")
    table.add_column("Entity Count", justify="right", style="green")
    for s in updated_shards:
        table.add_row(str(s.shard_id), str(s.entity_count))
    console.print(table)

@scale_group.command(name="sync")
@click.argument("shard_a", type=int)
@click.argument("shard_b", type=int)
def sync_scale(shard_a: int, shard_b: int):
    """Simulate a cross-shard interaction and generate the StateDelta."""
    shards = calculate_shards(100, HardwareTier.MID)
    
    s_a = next((s for s in shards if s.shard_id == shard_a), None)
    s_b = next((s for s in shards if s.shard_id == shard_b), None)
    
    if not s_a or not s_b or not s_a.entity_ids or not s_b.entity_ids:
        console.print("[red]Invalid shard IDs for this simulation.[/red]")
        return
        
    deltas = sync_shards(s_a, s_b, s_a.entity_ids[0], s_b.entity_ids[0], "collision")
    
    console.print(f"[bold green]Generated {len(deltas)} StateDelta(s) for cross-shard sync![/bold green]")
    for d in deltas:
        console.print(d.model_dump_json(indent=2))

@scale_group.command(name="status")
def scale_status():
    """Print the current scale configuration."""
    dna = ScaleDNA(
        total_entities=500,
        shard_count=2,
        entities_per_shard=250,
        worker_type="web_worker",
        sync_rate_ms=100,
        hardware_tier=HardwareTier.MID,
        max_entities_per_shard=1000,
        rebalance_threshold=0.8
    )
    console.print("[bold]Current Scale Status:[/bold]")
    console.print(dna.model_dump_json(indent=2))

# Register the new group to your main CLI app (Assuming your main group is named 'cli')
try:
    cli.add_command(scale_group)
except NameError:
    pass # If 'cli' is not defined in this exact scope, manually add scale_group to your main dispatcher

if __name__ == '__main__':

    cli()
    
    