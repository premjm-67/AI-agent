import os
import requests
from requests.exceptions import RequestException
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json

# Load the .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
CORS(app)

def safe_parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "run_code": False,
            "file_name": "invalid.json",
            "location": ".",
            "editor": "",
            "install_cmd": "",
            "code": "# ❌ Failed to parse Gemini JSON response"
        }

def call_gemini(prompt: str) -> dict:
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }

    system_instruction = (
        "You are an assistant that decides if the user wants to run code. "
        "Respond only in JSON format with keys: run_code (true/false), "
        "file_name, location, editor (optional), install_cmd (optional), and code. "
        "Do not wrap JSON in markdown. Escape all backslashes properly for valid JSON."
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": system_instruction}]},
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generation_config": {
            "response_mime_type": "application/json"
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return safe_parse_json(raw)
    except RequestException as e:
        print(f"❌ Gemini API request failed: {e}", flush=True)
        return {
            "run_code": True,
            "file_name": "script.py",
            "location": ".",
            "editor": "",
            "install_cmd": "",
            "code": "# Fallback code – Gemini is unreachable.\nprint('Hello from fallback!')\n"
        }

@app.route('/generate', methods=['POST'])
def generate():
    print("🟢 /generate POST request received", flush=True)
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is missing"}), 400

    print(f"📨 Prompt received: {prompt}", flush=True)
    gemini_response = call_gemini(prompt)
    print(gemini_response)
    print("✅ Responding to UI with Gemini result", flush=True)
    return jsonify(gemini_response)

if __name__ == '__main__':
    print("🚀 Flask server running on port 5000...", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
