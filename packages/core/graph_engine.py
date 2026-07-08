from packages.core.database import save_project, get_project, list_projects
from packages.core import brain
import json
import os

class GraphEngine:
    """Camera AI: The Graph Engine - Core Intelligence of the OGF"""
    
    def __init__(self):
        self.current_project = None
        print("Camera AI: Graph Engine initialized and ready!")
    
    def generate_and_save(self, prompt: str, project_name: str, description: str = ""):
        """
        Camera AI: Generate content using Groq AI and automatically save it to Memory Vault
        """
        print(f"Camera AI: Generating '{project_name}'...")
        
        # Step 1: Use the brain to generate content
        ai_response = brain.generate(prompt)
        
        # Step 2: Structure the graph data
        graph_data = {
            "prompt": prompt,
            "output": ai_response,
            "type": "generated_content",
            "model": "llama-3.1-8b-instant"
        }
        
        # Step 3: Save to Supabase Memory Vault
        saved_data = save_project(
            name=project_name,
            description=description if description else f"Auto-generated project: {project_name}",
            graph_data=graph_data
        )
        
        self.current_project = project_name
        print(f"Camera AI: '{project_name}' saved to Memory Vault!")
        
        return {
            "project_name": project_name,
            "ai_response": ai_response,
            "saved_data": saved_data
        }
    
    def retrieve_project(self, project_name: str):
        """Camera AI: Retrieve a project from Memory Vault by name"""
        print(f"Camera AI: Retrieving '{project_name}' from Memory Vault...")
        project = get_project(project_name)
        
        if project and len(project) > 0:
            print(f"Camera AI: Found '{project_name}'!")
            return project[0]
        else:
            print(f"Camera AI: Project '{project_name}' not found in Memory Vault.")
            return None
    
    def get_all_projects(self):
        """Camera AI: List all projects in Memory Vault"""
        print("Camera AI: Fetching all projects from Memory Vault...")
        projects = list_projects()
        
        if projects and len(projects) > 0:
            print(f"Camera AI: Found {len(projects)} project(s) in Memory Vault:")
            for p in projects:
                print(f"  - {p['name']} (Created: {p['created_at'][:10]})")
        else:
            print("Camera AI: No projects found in Memory Vault.")
        
        return projects
    
    def get_project_graph(self, project_name: str):
        """Camera AI: Get the full graph data for a project"""
        project = self.retrieve_project(project_name)
        
        if project:
            return project.get('graph_data', {})
        return None

# Camera AI: Create a global instance for easy access
graph_engine = GraphEngine()