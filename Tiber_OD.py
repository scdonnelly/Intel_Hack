import cv2
import matplotlib.pyplot as plt
import numpy as np
import openvino as ov
import os
from pathlib import Path

image_path = r"C:\Users\sara\Documents\Intel_Hack\test4.jpg"

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

    filename = Path(filename)
    if len(filename.parts) > 1:
        raise ValueError(
            "`filename` should refer to the name of the file, excluding the directory. "
            "Use the `directory` parameter to specify a target directory for the downloaded file."
        )

    filepath = Path(directory) / filename if directory is not None else filename
    if filepath.exists():
        return filepath.resolve()

    # create the directory if it does not exist, and add the directory to the filename
    if directory is not None:
        Path(directory).mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url=url, headers={"User-agent": "Mozilla/5.0"}, stream=True)
        response.raise_for_status()
    except (
        requests.exceptions.HTTPError
    ) as error:  # For error associated with not-200 codes. Will output something like: "404 Client Error: Not Found for url: {url}"
        raise Exception(error) from None
    except requests.exceptions.Timeout:
        raise Exception(
            "Connection timed out. If you access the internet through a proxy server, please "
            "make sure the proxy is set in the shell from where you launched Jupyter."
        ) from None
    except requests.exceptions.RequestException as error:
        raise Exception(f"File downloading failed with error: {error}") from None

    # download the file if it does not exist
    filesize = int(response.headers.get("Content-length", 0))
    if not filepath.exists():
        with tqdm_notebook(
            total=filesize,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=str(filename),
            disable=not show_progress,
        ) as progress_bar:
            with open(filepath, "wb") as file_object:
                for chunk in response.iter_content(chunk_size):
                    file_object.write(chunk)
                    progress_bar.update(len(chunk))
                    progress_bar.refresh()
    else:
        print(f"'{filepath}' already exists.")

    response.close()

    return filepath.resolve()




base_model_dir = Path("./model").expanduser()

model_name = "horizontal-text-detection-0001"
model_xml_name = f"{model_name}.xml"
model_bin_name = f"{model_name}.bin"

model_xml_path = base_model_dir / model_xml_name
model_bin_path = base_model_dir / model_bin_name

if not model_xml_path.exists():
    model_xml_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/horizontal-text-detection-0001/FP32/horizontal-text-detection-0001.xml"
    model_bin_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.3/models_bin/1/horizontal-text-detection-0001/FP32/horizontal-text-detection-0001.bin"

    download_file(model_xml_url, model_xml_name, base_model_dir)
    download_file(model_bin_url, model_bin_name, base_model_dir)
else:
    print(f"{model_name} already downloaded to {base_model_dir}")

    core = ov.Core()

model = core.read_model(model=model_xml_path)
device = ov.Core().get_available_devices()[0]
compiled_model = core.compile_model(model=model, device_name=device)

input_layer_ir = compiled_model.input(0)
output_layer_ir = compiled_model.output("boxes")

# Download the image from the openvino_notebooks storage

image_filename = download_file(
    image_path, os.path.basename(image_path)
)

# Text detection models expect an image in BGR format.
image = cv2.imread(str(image_filename))

# N,C,H,W = batch size, number of channels, height, width.
N, C, H, W = input_layer_ir.shape

# Resize the image to meet network expected input sizes.
resized_image = cv2.resize(image, (W, H))

# Reshape to the network input shape.
input_image = np.expand_dims(resized_image.transpose(2, 0, 1), 0)

#plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB));

# Create an inference request.
boxes = compiled_model([input_image])[output_layer_ir]

# Remove zero only boxes.
boxes = boxes[~np.all(boxes == 0, axis=1)]

total_boxes = len(boxes)
print("Total boxes: ", total_boxes)
i=1 
min_x=boxes[0][0]
max_x=boxes[0][2]
min_y=boxes[0][1]
max_y=boxes[0][3]

while(i<total_boxes):
    if boxes[i][0] < min_x:
        min_x = boxes[i][0]
    if boxes[i][2] > max_x:
        max_x = boxes[i][2]
    if boxes[i][1] < min_y:
        min_y = boxes[i][1]
    if boxes[i][3] > max_y:
        max_y = boxes[i][3]
    i+=1

original_height, original_width = image.shape[:2]

Width_multiplier = original_width/W
Height_multiplier = original_height/H

# Ensure bounding box coordinates are integers
min_x = int(min_x*Width_multiplier - 1)
max_x = int(max_x*Width_multiplier + 1)
min_y = int(min_y*Height_multiplier - 1)
max_y = int(max_y*Height_multiplier + 1)

print(f"min_x: {min_x}, max_x: {max_x}, min_y: {min_y}, max_y: {max_y}")

# Validate bounding box
if min_x >= max_x or min_y >= max_y:
    print("Error: Invalid bounding box coordinates.")
    print(f"min_x: {min_x}, max_x: {max_x}, min_y: {min_y}, max_y: {max_y}")
    exit()

# Crop the image using integer coordinates
image = image[min_y:max_y, min_x:max_x]

# Draw bounding boxes on the original image
for box in boxes:
    x_min, y_min, x_max, y_max = map(int, box[:4])  # Convert box coordinates to integers
    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)  # Green box with thickness 2


# Display the image with bounding boxes
plt.figure(figsize=(10, 6))
plt.axis("off")
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))  # Convert BGR to RGB for Matplotlib
plt.show()


