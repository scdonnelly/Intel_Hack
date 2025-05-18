from pathlib import Path
import cv2
import numpy as np
import pytesseract
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openvino as ov
import sys
from docx import Document

app = Flask(__name__)
CORS(app)

THRESHOLD = 0.1


# Download the model from the OpenVINO Model Zoo if not already downloaded
def download_file(
    url: str,
    filename: str = None,
    directory: str = None,
    show_progress: bool = True,
) -> Path:
    from tqdm.notebook import tqdm_notebook
    import requests
    import urllib.parse

    filename = filename or Path(urllib.parse.urlparse(url).path).name
    chunk_size = 16384  # make chunks bigger so that not too many updates are triggered for Jupyter front-end

    # check if the filename is a valid file name
    filename = Path(filename)
    if len(filename.parts) > 1:
        raise ValueError(
            "`filename` should refer to the name of the file, excluding the directory. "
            "Use the `directory` parameter to specify a target directory for the downloaded file."
        )

    # check if the directory is a valid directory
    filepath = Path(directory) / filename if directory is not None else filename

    # check if the file already exists
    if filepath.exists():
        return filepath.resolve()

    # create the directory if it does not exist, and add the directory to the filename
    if directory is not None:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # download the file
    try:
        response = requests.get(
            url=url, headers={"User-agent": "Mozilla/5.0"}, stream=True
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:  # For error associated with not-200 codes. Will output something like: "404 Client Error: Not Found for url: {url}"
        raise Exception(error) from None
    except requests.exceptions.Timeout:
        raise Exception(
            "Connection timed out. If you access the internet through a proxy server, please "
            "make sure the proxy is set in the shell from where you launched Jupyter."
        ) from None
    except requests.exceptions.RequestException as error:
        raise Exception(f"File downloading failed with error: {error}") from None

    response.close()

    return filepath.resolve()


def detect_text_regions(image):
    # Check if the model directory exists, if not create it
    base_model_dir = Path("./model").expanduser()

    # Define the model name and paths
    model_name = "horizontal-text-detection-0001"
    model_xml_name = f"{model_name}.xml"
    model_bin_name = f"{model_name}.bin"

    # Set the model paths
    model_xml_path = base_model_dir / model_xml_name
    model_bin_path = base_model_dir / model_bin_name

    # Check if the model files exist, if not download them
    if not model_xml_path.exists():
        model_xml_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/horizontal-text-detection-0001/FP32/horizontal-text-detection-0001.xml"
        model_bin_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/horizontal-text-detection-0001/FP32/horizontal-text-detection-0001.bin"

        download_file(model_xml_url, model_xml_name, base_model_dir)
        download_file(model_bin_url, model_bin_name, base_model_dir)
    else:
        print(f"{model_name} already downloaded to {base_model_dir}")

    core = ov.Core()

    # Load the model
    model = core.read_model(model=model_xml_path)
    device = ov.Core().get_available_devices()[0]
    compiled_model = core.compile_model(model=model, device_name=device)

    # Get the input and output layers
    input_layer_ir = compiled_model.input(0)
    output_layer_ir = compiled_model.output("boxes")

    # N,C,H,W = batch size, number of channels, height, width.
    N, C, H, W = input_layer_ir.shape

    # Resize the image to meet network expected input sizes.
    resized_image = cv2.resize(image, (W, H))

    return pytesseract.image_to_string(resized_image)


def populate_docx(full_text: str, output_file="output.docx"):
    doc = Document()
    doc.add_heading("Digitized Document", level=1)
    doc.add_paragraph(full_text)
    doc.save(output_file)
    print(f"Document saved as: {output_file}")
    return output_file


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/process-image", methods=["POST"])
def process_image():
    image = request.files["image"]
    doc_type = request.form.get("values")

    if image.filename == "":
        return jsonify({"error": "Image file is empty"}), 400

    try:
        img_bytes = image.read()
        file_bytes = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({"error": "Image decoding failed"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to decode image: {str(e)}"}), 500

    extracted_text = detect_text_regions(image)
    print(f"Extracted text: {extracted_text}")

    return_doc = populate_docx(extracted_text)

    # Return text for debug
    # Return the DOCX file as an attachment
    return send_file(
        return_doc,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"extracted_text_{doc_type}.docx",
    )
