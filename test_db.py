from packages.core.database import save_project, list_projects

print("Camera AI: Initializing Memory Vault test...")

# Save a test project
save_project("Test Project", "Testing the OGF Memory Vault", {"status": "active"})

# List projects to prove it saved
projects = list_projects()
print("Camera AI: Retrieved projects from the Memory Vault:")
for p in projects:
    print(f"- {p['name']} (Created: {p['created_at']})")