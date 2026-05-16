def calculate_points(stats):

    total_points = 0

    # Finish points - convert None to 0 safely
    finishes = stats.get("total_finishes") or 0
    finishes = int(finishes) if finishes else 0

    finish_points = finishes * 10
    total_points += finish_points

    # MVP bonus
    if stats.get("mvp"):
        total_points += 50

    # Winner bonus
    if stats.get("winner"):
        total_points += 100

    return {
        "finish_points": finish_points,
        "mvp_bonus": 50 if stats.get("mvp") else 0,
        "winner_bonus": 100 if stats.get("winner") else 0,
        "total_points": total_points
    }