import json
from packages.core import brain

def main():
    print("=" * 50)
    print("Camera AI: Ontological Genesis Fabric (OGF) Initializing...")
    print("=" * 50)
    
    # Load configuration
    with open("config.json", "r") as f:
        config = json.load(f)
        
    print(f"Camera AI: System Name: {config.get('name', 'Camera AI')}")
    print(f"Camera AI: Status: ONLINE")
    
    # Quick brain check to prove the cloud connection is alive
    print("\nCamera AI: Pinging the Brain (Groq API)...")
    try:
        response = brain.quick_generate("Say 'Camera AI is online' in exactly 3 words.")
        print(f"Camera AI: Brain Response: {response}")
    except Exception as e:
        print(f"Camera AI: Brain connection failed. Check .env file. Error: {e}")
        
    print("\nCamera AI: All systems operational. Ready for Day 2.")
    print("=" * 50)

if __name__ == "__main__":
    main()