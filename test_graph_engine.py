from packages.core.graph_engine import graph_engine

print("=" * 60)
print("Camera AI: GRAPH ENGINE TEST")
print("=" * 60)

# Test 1: Generate and Save a new project
print("\n[TEST 1] Generate and Save a Game Design Document")
print("-" * 60)

prompt = """
Create a detailed game design document for a cyberpunk racing game called "Neon Velocity".
Include: game concept, core mechanics, art style, target audience, and unique features.
"""

result = graph_engine.generate_and_save(
    prompt=prompt,
    project_name="Neon Velocity GDD",
    description="Cyberpunk racing game design document"
)

print("\nAI Generated Preview (first 200 chars):")
print(result['ai_response'][:200] + "...")

# Test 2: Retrieve the project
print("\n[TEST 2] Retrieve Project from Memory Vault")
print("-" * 60)

retrieved = graph_engine.retrieve_project("Neon Velocity GDD")
if retrieved:
    print(f"✓ Project Name: {retrieved['name']}")
    print(f"✓ Description: {retrieved['description']}")
    print(f"✓ Has Graph Data: {'graph_data' in retrieved}")

# Test 3: List all projects
print("\n[TEST 3] List All Projects")
print("-" * 60)

all_projects = graph_engine.get_all_projects()

print("\n" + "=" * 60)
print("Camera AI: GRAPH ENGINE TEST COMPLETE!")
print("=" * 60)