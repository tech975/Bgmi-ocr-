import cv2
import numpy as np


def detect_kill_feed_frame(frame):
    height, width = frame.shape[:2]

    # Crop top-left kill feed area
    kill_feed = frame[
        int(height * 0.10):int(height * 0.35),
        int(width * 0.00):int(width * 0.35)
    ]

    hsv = cv2.cvtColor(kill_feed, cv2.COLOR_BGR2HSV)

    # Cyan range based on your actual BGMI footage (H=100)
    lower_cyan = np.array([85, 50, 50])
    upper_cyan = np.array([115, 255, 255])

    mask = cv2.inRange(hsv, lower_cyan, upper_cyan)
    cyan_pixels = cv2.countNonZero(mask)

    if cyan_pixels > 30:
        return True

    return False


def detect_team_eliminated(frame):
    height, width = frame.shape[:2]

    banner = frame[
        int(height * 0.60):int(height * 0.80),
        int(width * 0.30):int(width * 0.70)
    ]

    gray = cv2.cvtColor(banner, cv2.COLOR_BGR2GRAY)
    bright_pixels = np.sum(gray > 150)

    if bright_pixels > 100:
        return True

    return False


def detect_scoreboard(frame):
    if detect_kill_feed_frame(frame):
        return True
    if detect_team_eliminated(frame):
        return True
    return False