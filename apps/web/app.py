from flask import Flask, request
import os
from dotenv import load_dotenv
from groq import Groq

# Wake up the web engine
app = Flask(__name__)

# Open the secret safe from the main vault to get our VIP password
load_dotenv('/workspaces/camera-ai/.env')
cloud_brain = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route("/", methods=["GET", "POST"])
def home():
    answer = ""
    
    # If the user clicks the "Generate" button, this happens:
    if request.method == "POST":
        user_prompt = request.form.get("prompt")
        if user_prompt:
            # Send the user's prompt to the Groq Cloud Brain
            response = cloud_brain.chat.completions.create(
                messages=[{"role": "user", "content": user_prompt}],
                model="llama-3.1-8b-instant"
            )
            answer = response.choices[0].message.content

    # This is the HTML (the visual design) of our web page
    html = f"""
    <h1>CAMERA AI WEB INTERFACE</h1>
    <p>The Ontological Genesis Fabric (OGF) is online. Ready to destroy the competition.</p>
    
    <form method="POST">
        <input type="text" name="prompt" placeholder="Ask Camera AI to design a game..." style="width:400px; padding:10px;">
        <button type="submit" style="padding:10px;">Generate</button>
    </form>
    
    <h2>Camera AI Response:</h2>
    <p style="white-space: pre-wrap;">{answer}</p>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)