import easyocr

reader = easyocr.Reader(['en'])

# Test on screenshot that has Kawaiツ - which screenshot number is it?
image_path = "ss/ss8.png"
result = reader.readtext(image_path)

print("=== RAW OCR OUTPUT ===")
for detection in result:
    text = detection[1]
    conf = round(detection[2], 2)
    print(f"{text} | conf: {conf}")