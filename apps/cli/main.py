import sys
import os

# ==========================================
# THE PATH FIX (Crucial for Python to find 'packages')
# ==========================================
# This tells Python: "Look at the folder this file is in, 
# then walk up two levels to find the main project root."
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import click
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.tree import Tree
from rich.panel import Panel

# ==========================================
# IMPORTS (Fixed to point to the correct locations)
# ==========================================
# Fix for ImportError: Get the actual function from the brain
from packages.core.brain import generate as ask_brain

# Day 12 Imports: The Juice Engine
from packages.core.models import ImpactVector, JuiceProfile
from packages.core import juice_engine, brain

# Initialize Rich for beautiful terminal colors and formatting
console = Console()

@click.group()
def camera():
    """Camera AI: The Ontological Genesis Fabric CLI."""
    pass

# ==========================================
# DAY 11 COMMAND: THE FRACTAL GENERATOR
# ==========================================
@camera.command()
@click.argument('prompt')
def generate(prompt):
    """Generate an ontological graph from a prompt."""
    console.print(f"\n[bold cyan]Camera AI[/bold cyan] is thinking about: [italic]'{prompt}'[/italic]\n")
    
    # Create a beautiful spinning animation while Groq thinks in the cloud
    with Live(Spinner("dots", text="[bold yellow]Generating Ontology in the Cloud...[/bold yellow]"), console=console):
        # Call the brain!
        result = ask_brain(prompt)
        
    console.print("\n[bold green]✅ Generation Complete![/bold green]\n")
    
    # Convert Pydantic model to a standard Python dictionary
    if hasattr(result, 'model_dump'):
        data = result.model_dump()
    elif hasattr(result, 'dict'):
        data = result.dict()
    else:
        data = result
        
    # Build a beautiful visual tree of the data
    tree = Tree("🧠 [bold]Camera AI: Ontological Graph[/bold]")
    
    if 'nodes' in data:
        node_branch = tree.add("[bold cyan]Nodes (Concepts)[/bold cyan]")
        for node in data['nodes']:
            # Safely grab the name/label and description
            label = node.get('label', node.get('name', node.get('id', 'Unknown')))
            desc = node.get('description', node.get('type', ''))
            node_branch.add(f"🟢 [bold]{label}[/bold]: {desc}")
            
    if 'edges' in data:
        edge_branch = tree.add("[bold magenta]Edges (Connections)[/bold magenta]")
        for edge in data['edges']:
            source = edge.get('source', '?')
            target = edge.get('target', '?')
            rel = edge.get('relationship', edge.get('type', 'connects to'))
            edge_branch.add(f"🔗 {source} ➡️ {target} [dim]({rel})[/dim]")
            
    # Print the final masterpiece in a nice blue box
    console.print(Panel(tree, title="[bold]Camera AI Output[/bold]", border_style="blue"))

# ==========================================
# DAY 12 COMMANDS: THE JUICE ENGINE
# ==========================================
@camera.group()
def juice():
    """Commands for the Juice Engine (Physics & Narrative)."""
    pass

@juice.command()
def test():
    """Test the Juice Engine with a default, low-impact collision."""
    console.print("\n[bold cyan]🧪 Testing Juice Engine...[/bold cyan]")
    
    # 1. Calculate a gentle push
    vector = juice_engine.calculate_impact_vector(force=20.0)
    juice_profile = JuiceProfile(impact_type="light_bounce", ragdoll_decay=0.3, impact_vector=vector)
    
    # 2. Get the AI narrative
    narrative = brain.generate_narrative_impact(juice_profile, "the test box")
    
    console.print(f"[green]📖 Narrative:[/green] {narrative}")
    console.print(f"[yellow]📐 Vector:[/yellow] {vector.model_dump()}")

@juice.command()
@click.argument('force', type=float)
def impact(force):
    """Trigger a custom, high-velocity impact with a specific force."""
    console.print(f"\n[bold red]💥 Triggering massive impact with force: {force}![/bold red]")
    
    # 1. Calculate a heavy smash
    vector = juice_engine.calculate_impact_vector(force=force)
    juice_profile = JuiceProfile(impact_type="heavy_smash", ragdoll_decay=0.9, impact_vector=vector)
    
    # 2. Get the AI narrative
    narrative = brain.generate_narrative_impact(juice_profile, "the target")
    
    console.print(f"[green]📖 Narrative:[/green] {narrative}")
    console.print(f"[yellow]📐 Vector:[/yellow] {vector.model_dump()}")

# This allows us to run the file directly
if __name__ == '__main__':
    camera()