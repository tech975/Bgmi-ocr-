import requests

url = "http://127.0.0.1:5000/analyze-screenshot"

images = []
for i in range(1, 17):
    images.append((
        "image",
        (f"s{i}.png", open(f"ss/ss{i}.png", "rb"), "image/png")
    ))

response = requests.post(url, files=images)
print(response.text)