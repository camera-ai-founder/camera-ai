import click
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.tree import Tree
from rich.panel import Panel

# Import our bridge from Step 2
from camera_cli import ask_brain

# Initialize Rich for beautiful terminal colors and formatting
console = Console()

@click.group()
def camera():
    """Camera AI: The Ontological Genesis Fabric CLI."""
    pass

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

# This allows us to run the file directly
if __name__ == '__main__':
    camera()