from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='en')

# Test on one screenshot
image_path = "ss/ss1.png"
result = ocr.predict(image_path)

print("=== RAW OCR OUTPUT ===")
for res in result:
    for line in res['rec_texts']:
        print(line)