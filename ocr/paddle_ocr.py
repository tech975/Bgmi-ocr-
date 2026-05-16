import cv2
from paddleocr import PaddleOCR

ocr_engine = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    show_log=False
)

def extract_text(image):
    result = ocr_engine.ocr(image, cls=True)

    extracted_text = []

    if result is None:
        return extracted_text

    for line in result:
        if line is None:
            continue
        for word in line:
            text = word[1][0]
            extracted_text.append(text)

    return extracted_text


def extract_kill_feed_text(frame):
    """OCR only the kill feed region (top left red box)"""
    height, width = frame.shape[:2]

    kill_feed = frame[
        int(height * 0.10):int(height * 0.35),
        int(width * 0.00):int(width * 0.35)
    ]

    # Enhance for OCR
    gray = cv2.cvtColor(kill_feed, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2)
    gray = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]

    return extract_text(gray)


def extract_eliminated_banner_text(frame):
    """OCR the Team Eliminated banner at bottom center"""
    height, width = frame.shape[:2]

    banner = frame[
        int(height * 0.60):int(height * 0.80),
        int(width * 0.30):int(width * 0.70)
    ]

    gray = cv2.cvtColor(banner, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2)

    return extract_text(gray)


def extract_top_hud_text(frame):
    """OCR top HUD - Remaining teams and Eliminations count"""
    height, width = frame.shape[:2]

    hud = frame[
        int(height * 0.00):int(height * 0.10),
        int(width * 0.00):int(width * 0.25)
    ]

    gray = cv2.cvtColor(hud, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2)

    return extract_text(gray)