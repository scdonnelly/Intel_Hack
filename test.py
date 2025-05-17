import cv2
import base64
import numpy as np
import pytesseract
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from openvino.runtime import Core

app = Flask(__name__)
CORS(app)


# Load OpenVINO model
core = Core()
model = core.read_model("text-detection-0004.xml")
compiled_model = core.compile_model(model, "CPU")
input_layer = compiled_model.input(0)

def detect_text_regions(image):
    orig_h, orig_w = image.shape[:2]
    resized_image = cv2.resize(image, (1280, 768))
    input_image = np.expand_dims(np.transpose(resized_image, (2, 0, 1)), axis=0)
    input_image = np.expand_dims(input_image, axis=0).astype(np.float32)
    
    results = compiled_model([input_image])[compiled_model.output(0)]
    boxes = []

    for prediction in results[0, 0]:
        conf = prediction[2]
        if conf > 0.6:
            xmin = int(prediction[3] * orig_w)
            ymin = int(prediction[4] * orig_h)
            xmax = int(prediction[5] * orig_w)
            ymax = int(prediction[6] * orig_h)
            boxes.append((xmin, ymin, xmax, ymax))

    return boxes


def run_ocr_on_boxes(image, boxes):
    results = []
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            continue  # skip invalid crops
        text = pytesseract.image_to_string(roi, config="--psm 6")
        if text.strip():
            results.append(text.strip())
    return "\n".join(results)



@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"




@app.route("/process-image", methods=["POST"])
def process_image():
    image_file = request.form.get("file")
    doc_type = request.form.get("values")

    if not image_file:
        return jsonify({"error": "Image file is empty"}), 400

    
    if "," in image_file:
        image_file = image_file.split(",")[1]

    try:
        img_bytes = base64.b64decode(image_file)
        file_bytes = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({"error": f"Failed to decode image: {str(e)}"}), 500

    if image is None:
        return jsonify({"error": "Image decoding failed"}), 400

    
    boxes = detect_text_regions(image)
    print(f"Detected {len(boxes)} text regions.")

    
    extracted_text = run_ocr_on_boxes(image, boxes)
    print("Extracted text:")
    print(extracted_text)


    subprocess.run(["python3", "main.py"], input=extracted_text.encode())
    # Return text for debug
    response = jsonify({
        "docType": doc_type,
        "extractedText": extracted_text
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


