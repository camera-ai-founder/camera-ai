import os
from groq import Groq
from dotenv import load_dotenv

# Camera AI: Load environment variables
load_dotenv()

# Camera AI: Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate(prompt: str, model: str = "llama-3.1-8b-instant"):
    """Camera AI: Generate text using Groq API"""
    print(f"Camera AI Brain: Processing with {model}...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are Camera AI, the Ontological Genesis Fabric. You generate AAA games, apps, and revolutionary software. Think big. Build bigger."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def quick_generate(prompt: str):
    """Camera AI: Quick generation without verbose output"""
    return generate(prompt)