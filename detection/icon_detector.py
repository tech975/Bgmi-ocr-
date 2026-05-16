import cv2
import numpy as np


def load_templates():
    kill_template = cv2.imread("kill_icon.png")
    knock_template = cv2.imread("knock_icon.png")
    return kill_template, knock_template


def detect_icon(frame, template, threshold=0.6):
    if template is None:
        return []

    # Convert both to grayscale
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(
        frame_gray,
        template_gray,
        cv2.TM_CCOEFF_NORMED
    )

    locations = np.where(result >= threshold)
    matches = list(zip(*locations[::-1]))

    return matches


def count_kills_in_frame(frame, kill_template, knock_template):
    kill_matches = detect_icon(frame, kill_template)
    knock_matches = detect_icon(frame, knock_template)

    return {
        "kills": len(kill_matches),
        "knocks": len(knock_matches),
        "kill_positions": kill_matches,
        "knock_positions": knock_matches
    }