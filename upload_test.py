import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("LOCAL_HOST", "RENDER_URL", "http://127.0.0.1:5000") + "/analyze-screenshot"

print(f"Sending to: {url}")

images = []
for i in range(1, 17):
    images.append((
        "image",
        (f"s{i}.png", open(f"ss/ss{i}.png", "rb"), "image/png")
    ))

response = requests.post(url, files=images)
print(response.text)