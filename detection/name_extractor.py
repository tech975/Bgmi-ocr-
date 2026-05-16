import cv2
from ocr.paddle_ocr import extract_text
from ocr.text_cleaner import clean_text


def extract_kill_events_from_frame(frame):
    height, width = frame.shape[:2]

    # Crop kill feed area
    kill_feed = frame[
        int(height * 0.08):int(height * 0.38),
        int(width * 0.00):int(width * 0.38)
    ]

    # Upscale for better OCR
    kill_feed = cv2.resize(kill_feed, None, fx=3, fy=3)

    texts = extract_text(kill_feed)
    cleaned = clean_text(texts)

    return cleaned