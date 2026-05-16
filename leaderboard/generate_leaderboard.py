from leaderboard.points_system import calculate_points


def generate_leaderboard(stats):

    points = calculate_points(stats)

    leaderboard = {
        "winner": stats.get("winner"),
        "mvp": stats.get("mvp"),
        "players": stats.get("players"),
        "total_finishes": stats.get("total_finishes"),
        "points": points
    }

    return leaderboard