import base64
from io import BytesIO
from PIL import Image
import requests


path = "image.png"
url = "http://localhost:7071/api/transform_image"

# Image.open(path).show()

with open(path, "rb") as image:
    encoded = base64.b64encode(image.read()).decode('utf-8')

r = requests.post(url, json={"image": encoded})
data = r.json().get("image")

decoded = base64.b64decode(data)
image = Image.open(BytesIO(decoded))
image.show()
