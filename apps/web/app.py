import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import Flask, render_template_string, request, jsonify
from packages.core.graph_engine import graph_engine

app = Flask(__name__)

# Camera AI: Upgraded HTML interface with Project Name input
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Camera AI - Web Interface</title>
    <style>
        body { font-family: 'Courier New', monospace; background-color: #0d1117; color: #c9d1d9; padding: 40px; }
        h1 { color: #58a6ff; }
        input, textarea { width: 100%; background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; padding: 15px; font-size: 16px; border-radius: 6px; box-sizing: border-box; margin-bottom: 10px; }
        input { height: 40px; }
        textarea { height: 120px; }
        button { background-color: #238636; color: #ffffff; padding: 12px 24px; border: none; cursor: pointer; font-weight: bold; font-size: 16px; border-radius: 6px; margin-top: 10px; }
        button:hover { background-color: #2ea043; }
        #response { margin-top: 30px; white-space: pre-wrap; background-color: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; min-height: 100px; }
    </style>
</head>
<body>
    <h1>Camera AI - Ontological Genesis Fabric</h1>
    <p>Project Name:</p>
    <input type="text" id="projectName" placeholder="e.g., Aurora Protocol GDD">
    <p>Prompt:</p>
    <textarea id="prompt" placeholder="e.g., Generate a AAA Game Design Document..."></textarea>
    <br>
    <button onclick="generate()">Generate & Save to Memory Vault</button>
    <div id="response"></div>

    <script>
        async function generate() {
            const projectName = document.getElementById('projectName').value;
            const prompt = document.getElementById('prompt').value;
            document.getElementById('response').innerText = "Camera AI is thinking and saving to the cloud...";
            
            const res = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_name: projectName, prompt: prompt })
            });
            const data = await res.json();
            document.getElementById('response').innerText = data.response;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    project_name = data.get('project_name', 'Untitled Web Project')
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"response": "Error: Prompt is empty."})
        
    # Camera AI: Use the Graph Engine to generate AND save automatically!
    try:
        result = graph_engine.generate_and_save(
            prompt=prompt,
            project_name=project_name,
            description=f"Generated via Web Interface"
        )
        return jsonify({"response": result['ai_response']})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)