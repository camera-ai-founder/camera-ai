import click
import os
import json
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
from groq import Groq

# Initialize Rich for beautiful terminal output
console = Console()

# Load environment variables from the .env file
load_dotenv()

def get_supabase_client():
    """Safely connects to the Supabase Memory Vault."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        console.print("[bold red]Error: Supabase URL or Key not found in .env![/bold red]")
        return None
    
    from supabase import create_client
    return create_client(url, key)

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
        table.add_column("ID", style="dim", width=8)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        
        for p in projects:
            p_id = str(p.get("id"))[:8]
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
        table.add_column("ID", style="dim", width=8)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        
        for p in results:
            p_id = str(p.get("id"))[:8]
            p_name = p.get("name") or p.get("title") or "Untitled"
            created_at = p.get("created_at")
            p_date = created_at[:10] if created_at else "N/A"
            table.add_row(p_id, p_name, p_date)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error searching:[/bold red] {e}")

# --- THIS IS THE NEW COMMAND WE ARE ADDING ---
@cli.command()
@click.argument("code_snippet")
def generate(code_snippet):
    """Generate an ontological graph from the provided code snippet."""
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print(json.dumps({"error": "GROQ_API_KEY not found in .env"}))
        return

    client = Groq(api_key=groq_api_key)
    
    prompt = f"""Analyze the following code snippet and extract an ontological graph. 
    Return ONLY a valid JSON object with two arrays: 'nodes' (list of strings) and 'edges' (list of objects with 'source' and 'target' strings). 
    Do not include any markdown formatting, backticks, or text outside the JSON.
    
    Code:
    {code_snippet}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Clean up potential markdown code blocks if the AI adds them
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
            
        # Print ONLY the JSON so the VS Code extension can read it
        print(response_text.strip())
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    cli()