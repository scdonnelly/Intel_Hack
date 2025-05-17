import cv2
import base64
import numpy as np
import pytesseract

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/process-image", methods=["POST"])
def process_image():
    print("HAIDPUFHJHISHODHF")
    image_file = request.form.get("file")
    doc_type = request.form.get("values")
    print(f"Image: {image_file}")
    print(f"Doc Type: {doc_type}")

    if not image_file:
        print("Error 1:")
        return jsonify({"error": "Image file is empty"}), 400

    # If the string contains a data URL prefix (e.g., "data:image/jpeg;base64,"), remove it
    if "," in image_file:
        image_file = image_file.split(",")[1]

    # Decode base64 string to bytes
    img_bytes = base64.b64decode(image_file)

    # Convert bytes to numpy array
    file_bytes = np.frombuffer(img_bytes, np.uint8)

    # Decode the image using OpenCV
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        print("Error 2:")
        print("Error: Could not read the image.")
        exit()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    print(text)

    response = jsonify({"docType": doc_type, "extractedText": text})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
