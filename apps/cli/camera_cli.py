import sys
import os

# THE MAGIC PATH TRICK: 
# This tells Python to look up two levels to the root folder so it can find 'packages'.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# IMPORT THE BRAIN:
from packages.core.brain import generate_ontology 

def ask_brain(prompt: str):
    """This function calls the core Camera AI brain and returns the result."""
    print("Connecting to Camera AI Core...")
    result = generate_ontology(prompt)
    return result