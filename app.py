from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import json
import requests as req
from difflib import get_close_matches
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────
# GEMINI API KEY
# ─────────────────────────────────────────
# Load from environment variables only. Example:
# GEMINI_API_KEY=your_key_here
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError(
        "No Gemini API key configured. Set GEMINI_API_KEY in your environment or .env file."
    )

GEMINI_MODEL = "gemini-2.5-flash"


def get_gemini_url():
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"


def call_gemini(payload):
    """Call Gemini with the configured API key."""
    try:
        print("Using Gemini API key...")
        response = req.post(
            get_gemini_url(),
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            return response

        print(f"Gemini request failed with status {response.status_code}")
        return response

    except Exception as e:
        print(f"Gemini request exception: {e}")
        return None


# ─────────────────────────────────────────
# REGISTERED PLAYERS
# ─────────────────────────────────────────

def load_registered_players():
    try:
        with open("teams_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        all_players = []
        player_to_team = {}
        for team in data["teams"]:
            for player in team["players"]:
                all_players.append(player)
                player_to_team[player] = team["team_name"]
        return all_players, player_to_team
    except Exception as e:
        print(f"Could not load teams_data.json: {e}")
        return [], {}


def fuzzy_match_name(ocr_name, registered_players):
    if not registered_players:
        return ocr_name
    clean_ocr = ocr_name.replace(" ", "").lower()
    clean_registered = {
        p.replace(" ", "").lower(): p
        for p in registered_players
    }
    matches = get_close_matches(
        clean_ocr,
        clean_registered.keys(),
        n=1,
        cutoff=0.5
    )
    if matches:
        return clean_registered[matches[0]]
    return ocr_name


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route("/")
def home():
    return "Esports AI Backend Running"


@app.route("/analyze-screenshot", methods=["POST"])
def analyze_screenshot():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"})

    files = request.files.getlist("image")

    if not files:
        return jsonify({"error": "No images found"})

    registered_players, player_to_team = load_registered_players()

    players_list = ""
    if registered_players:
        players_list = "\n\nREGISTERED PLAYERS LIST (match OCR names to these exact names):\n"
        players_list += "\n".join(registered_players)

    images_parts = []
    for file in files:
        img_bytes = file.read()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_parts.append({
            "inline_data": {
                "mime_type": file.content_type or "image/png",
                "data": b64
            }
        })

    prompt = f"""You are analyzing BGMI tournament result screenshots.

CRITICAL READING RULES:
1. Numbers: Read VERY carefully. "11" is eleven not one. "4" is four not "1". Double check every number.
2. Player names: Preserve EXACTLY including unicode symbols like ツ ♡ é Ñ 🔱 ☆ → ★ メ ソ. NEVER split one name into two.
3. Special characters must be preserved exactly.
4. These screenshots show different scroll positions of the SAME result screen. Combine ALL data across ALL images into ONE unified result.
5. Do NOT duplicate teams. If same team appears in multiple screenshots merge them.
6. Left panel (positions 1 and 2) appears in ALL screenshots - read it only ONCE.
7. Right panel shows different teams per screenshot - read ALL of them.
8. Total finishes = sum of all individual player finishes in that team.
9. MOST IMPORTANT: Match player names from screenshots to the registered players list below. Use the exact registered name spelling always.
{players_list}

LAYOUT:
- Left side: position 1 (winner with crown icon) and position 2
- Right side: 3 teams per screenshot at different positions
- Each player row format: "PlayerName    X finishes" or "PlayerName    X finish"
- Team name: use the team from registered players list

Return ONLY compact minified JSON on a single line, no spaces, no indentation, no markdown, no explanation:
{{"match_results":[{{"position":1,"team_name":"BB","total_finishes":19,"players":[{{"player_name":"BBxRYZOR","finishes":4}}]}}]}}

STRICT RULES:
- Output ONLY valid JSON nothing else
- All finish values must be integers
- Never hallucinate players or teams not visible
- Never skip any player or team that IS visible
- Use exact registered player name spelling from the list above
- Process ALL screenshots and combine into one complete result
- Do not duplicate position 1 and 2 teams"""

    parts = images_parts + [{"text": prompt}]

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 16384
        }
    }

    try:
        response = call_gemini(payload)

        if response is None:
            return jsonify({"error": "All Gemini API keys failed"})

        if response.status_code != 200:
            return jsonify({
                "error": "Gemini API failed",
                "status": response.status_code,
                "details": response.text
            })

        result = response.json()
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]

        clean = raw_text.strip()
        clean = clean.replace("```json", "").replace("```", "").strip()

        if not clean.endswith("}"):
            last_bracket = clean.rfind("}]}")
            if last_bracket != -1:
                clean = clean[:last_bracket + 3]

        parsed = json.loads(clean)

        if registered_players:
            for team in parsed["match_results"]:
                for player in team["players"]:
                    original = player["player_name"]
                    matched = fuzzy_match_name(original, registered_players)
                    player["player_name"] = matched
                    if matched in player_to_team:
                        team["team_name"] = player_to_team[matched]

        return app.response_class(
            response=json.dumps(parsed, ensure_ascii=False, indent=2),
            status=200,
            mimetype="application/json"
        )

    except json.JSONDecodeError:
        return jsonify({
            "error": "JSON parse failed",
            "raw": raw_text
        })
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)