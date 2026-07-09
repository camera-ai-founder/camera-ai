import click
import os
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Initialize Rich for beautiful terminal output
console = Console()

# Load environment variables from the .env file
load_dotenv()

def get_supabase_client():
    """Safely connects to the Supabase Memory Vault."""
    url = os.environ.get("SUPABASE_URL")
    # Checks for standard Supabase key names
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
        # Query the 'projects' table created on Day 2, ordered by newest first
        response = supabase.table("projects").select("*").order("created_at", desc=True).execute()
        projects = response.data
        
        if not projects:
            console.print("[yellow]No projects found in the vault. Generate some first![/yellow]")
            return

        # Create a beautiful Rich Table
        table = Table(title="Camera AI - Saved Projects", show_lines=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("Name", style="magenta")
        table.add_column("Created", style="green")
        
        for p in projects:
            # Note: Adjust "id", "name", and "created_at" if your DB columns have different names!
            p_id = str(p.get("id"))[:8] # Truncate ID for clean UI
            p_name = p.get("name") or p.get("title") or "Untitled"
            
            # Safely grab just the date part (YYYY-MM-DD)
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
    console.print(f"[bold cyan]Searching Memory Vault for:[/bold cyan] [magenta]'{query_string}'[/magenta]")
    
    supabase = get_supabase_client()
    if not supabase: return

    try:
        # 'ilike' performs a case-insensitive search in Postgres
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

if __name__ == "__main__":
    cli()