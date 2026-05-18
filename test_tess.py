import pytesseract
from PIL import Image
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load image
img = cv2.imread("ss/s1.png")

# Preprocessing
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.resize(gray, None, fx=2, fy=2)
gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

# OCR with config
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(gray, config=custom_config)

print("=== OCR OUTPUT ===")
print(text)