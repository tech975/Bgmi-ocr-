from flask import Flask, request, jsonify
import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
from difflib import get_close_matches
import base64
import json
import requests as req

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

GEMINI_API_KEY = "AIzaSyBfiArPSTCDw7eJJB4i0dhS1BCzxDk0TPw"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"


# ─────────────────────────────────────────
# REGISTERED PLAYERS LOADER
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
# VIDEO HELPER FUNCTIONS
# ─────────────────────────────────────────

def match_player(text, players):
    if not text or not players:
        return text
    clean = text.replace(" ", "").lower()
    clean_players = {p.replace(" ", "").lower(): p for p in players}
    matches = get_close_matches(clean, clean_players.keys(), n=1, cutoff=0.4)
    if matches:
        return clean_players[matches[0]]
    return text


def has_kill_feed(frame):
    height, width = frame.shape[:2]
    region = frame[
        int(height * 0.05):int(height * 0.45),
        int(width * 0.00):int(width * 0.40)
    ]
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    lower = np.array([85, 50, 50])
    upper = np.array([115, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    return cv2.countNonZero(mask) > 300


def process_region(region):
    if region.size == 0:
        return None
    region = cv2.resize(region, None, fx=4, fy=4)
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    _, thresh = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return cv2.bitwise_not(thresh)


def run_ocr(img):
    if img is None:
        return []
    result = ocr.ocr(img, cls=True)
    texts = []
    if result:
        for line in result:
            if line:
                for word in line:
                    text = word[1][0].strip()
                    conf = round(word[1][1], 2)
                    if conf > 0.45 and len(text) >= 2:
                        texts.append((text, conf))
    return texts


garbage = [
    "sprint", "fpp", "spp", "app", "lpp", "bpp",
    "auto", "round", "bgmi", "mode", "rint",
    "respawn", "countdown", "creation", "code", "team",
    "remaining", "elimination", "objective", "independent",
    "content", "feedback", "questions", "player", "this",
    "=", "p", "b", "e", "f", "i", "l", "if", "r"
]


def best_text(texts):
    clean = [
        (t, c) for t, c in texts
        if t.lower().strip() not in garbage
        and len(t) >= 3
        and not t.lower().strip().startswith("this")
        and not t.lower().strip().startswith("creation")
    ]
    if not clean:
        return None
    return max(clean, key=lambda x: x[1])[0]


def extract_events_from_frame(frame, players):
    height, width = frame.shape[:2]

    kf_top = int(height * 0.05)
    kf_bottom = int(height * 0.45)
    kf_left = 0
    kf_right = int(width * 0.40)

    kill_feed = frame[kf_top:kf_bottom, kf_left:kf_right]
    kh, kw = kill_feed.shape[:2]

    events = []
    seen_in_frame = set()

    num_rows = 4
    row_h = kh // num_rows

    for i in range(num_rows):
        row_top = i * row_h
        row_bottom = min((i + 1) * row_h, kh)

        if row_bottom - row_top < 8:
            continue

        row = kill_feed[row_top:row_bottom, 0:kw]
        rh, rw = row.shape[:2]

        left = row[0:rh, 0:int(rw * 0.40)]
        right = row[0:rh, int(rw * 0.55):rw]

        left_texts = run_ocr(process_region(left))
        right_texts = run_ocr(process_region(right))

        killer = best_text(left_texts)
        victim = best_text(right_texts)

        if not killer or not victim:
            continue

        killer = match_player(killer, players)
        victim = match_player(victim, players)

        key = f"{killer}-{victim}"
        if key not in seen_in_frame:
            seen_in_frame.add(key)
            events.append({
                "killer": killer,
                "victim": victim
            })

    return events


def process_video(video_path, players):
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    sample_every = max(int(fps * 2), 1)

    print(f"Video: {duration:.1f}s | FPS: {fps:.1f} | Every {sample_every} frames")

    all_events = []
    seen_events = set()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % sample_every == 0:
            second = frame_count / fps

            if has_kill_feed(frame):
                print(f"Kill feed at {second:.1f}s - running OCR...")
                events = extract_events_from_frame(frame, players)

                for event in events:
                    key = f"{event['killer']}-{event['victim']}"
                    if key not in seen_events:
                        seen_events.add(key)
                        all_events.append(event)
                        print(f"  {event['killer']} --> {event['victim']}")

        frame_count += 1

    cap.release()
    print(f"Total events: {len(all_events)}")
    return all_events


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route("/")
def home():
    return "Esports AI Backend Running"


@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"})

    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No selected file"})

    players_param = request.form.get("players", "")
    players = [p.strip() for p in players_param.split(",")] if players_param else []

    save_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(save_path)
    print(f"Saved: {save_path}")
    print(f"Players: {players}")

    kill_events = process_video(save_path, players)

    if not kill_events:
        return jsonify({
            "message": "No kill events detected",
            "tip": "Make sure kill feed visible in top left"
        })

    return jsonify({
        "message": "Match processed successfully",
        "total_events": len(kill_events),
        "kill_feed": kill_events
    })


@app.route("/analyze-screenshot", methods=["POST"])
def analyze_screenshot():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"})

    files = request.files.getlist("image")

    if not files:
        return jsonify({"error": "No images found"})

    # Load registered players
    registered_players, player_to_team = load_registered_players()

    # Build registered players list for prompt
    players_list = ""
    if registered_players:
        players_list = "\n\nREGISTERED PLAYERS LIST (match OCR names to these exact names):\n"
        players_list += "\n".join(registered_players)

    # Convert all images to base64
    images_parts = []
    for file in files:
        img_bytes = file.read()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_parts.append({
            "inline_data": {
                "mime_type": file.content_type or "image/jpeg",
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
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 16384
        }
    }

    try:
        response = req.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120
        )

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

        # Fuzzy match player names to registered names
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
        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)