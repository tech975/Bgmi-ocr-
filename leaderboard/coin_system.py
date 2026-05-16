def calculate_points(stats):

    total_points = 0

    # -----------------------------
    # FINISH POINTS
    # -----------------------------
    finishes = stats.get("total_finishes", 0)

    finish_points = finishes * 10

    total_points += finish_points

    # -----------------------------
    # MVP BONUS
    # -----------------------------
    if stats.get("mvp"):

        total_points += 50

    # -----------------------------
    # WINNER BONUS
    # -----------------------------
    if stats.get("winner"):

        total_points += 100

    return {
        "finish_points": finish_points,
        "mvp_bonus": 50 if stats.get("mvp") else 0,
        "winner_bonus": 100 if stats.get("winner") else 0,
        "total_points": total_points
    }