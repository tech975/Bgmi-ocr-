import re

def parse_kill_feed(texts):
    """Parse kill feed text into kill/knock events"""
    events = []

    for text in texts:
        text = text.strip()
        if len(text) > 2:
            events.append(text)

    return events


def extract_match_stats(texts):
    stats = {
        "winner": None,
        "total_finishes": None,
        "mvp": None,
        "players": [],
        "kill_events": [],
        "eliminations": 0,
        "remaining_teams": None
    }

    for text in texts:
        lower = text.lower()

        if "victory" in lower or "winner" in lower:
            stats["winner"] = text

        if "mvp" in lower:
            stats["mvp"] = text

        if "eliminat" in lower:
            stats["kill_events"].append(text)

        if "remaining" in lower:
            stats["remaining_teams"] = text

        if text.isdigit():
            val = int(text)
            if val <= 100:
                stats["eliminations"] = val

        if re.search(r'[A-Za-z]', text):
            ignore = ["victory", "finishes", "assists",
                      "mvp", "remaining", "eliminated",
                      "sprint", "auto", "team", "round",
                      "objective", "creation", "code"]
            if text.lower() not in ignore and len(text) >= 3:
                if not any(p["name"] == text for p in stats["players"]):
                    stats["players"].append({"name": text})

        if "finishes" in lower or "finish" in lower:
            for t in texts:
                if t.isdigit():
                    stats["total_finishes"] = int(t)
                    break

    return stats