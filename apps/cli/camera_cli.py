import sys
import os
# Camera AI: Fix for running from subfolders - tells Python where the root is
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from packages.core import brain
from packages.core.database import save_project, list_projects

def print_banner():
    print("=" * 60)
    print("  Camera AI - Ontological Genesis Fabric (CLI)")
    print("  Type your prompt, or use /save, /projects, /quit")
    print("=" * 60)

def main():
    print_banner()
    conversation_history = []
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            # Camera AI: Command Handling
            if user_input.lower() == '/quit':
                print("Camera AI: Shutting down CLI. Goodbye!")
                break
                
            elif user_input.lower() == '/projects':
                print("\n--- Camera AI: Saved Projects ---")
                projects = list_projects()
                if projects:
                    for p in projects:
                        print(f"- {p['name']} ({p['created_at'][:10]})")
                else:
                    print("No projects found in the Memory Vault.")
                continue
                
            elif user_input.lower() == '/save':
                print("\n--- Camera AI: Save to Memory Vault ---")
                if not conversation_history:
                    print("No conversation to save yet! Talk to me first.")
                    continue
                    
                project_name = input("Enter a name for this project: ").strip()
                if not project_name:
                    print("Save cancelled.")
                    continue
                    
                description = input("Enter a brief description: ").strip()
                
                # Save the chat history to Supabase
                save_project(
                    name=project_name,
                    description=description,
                    graph_data={"chat_history": conversation_history}
                )
                print(f"Camera AI: Successfully saved '{project_name}'!")
                continue
                
            # Camera AI: Send to the Brain
            print("\nCamera AI: Thinking on the cloud...")
            response = brain.generate(user_input)
            
            # Store in history
            conversation_history.append(f"User: {user_input}")
            conversation_history.append(f"Camera AI: {response}")
            
            # Print response
            print(f"\nCamera AI: {response}")
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nCamera AI: Interrupted. Type /quit to exit.")
            continue
        except Exception as e:
            print(f"\nCamera AI Error: {e}")

if __name__ == '__main__':
    main()