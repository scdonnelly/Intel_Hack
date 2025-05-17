import cv2
import pytesseract
import os
from main import populate_docx  # Import the doc-writing function

pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"
image_path = "example_form.jpg"

if not os.path.exists(image_path):
    print(f"Error: File '{image_path}' does not exist.")
    exit()

image = cv2.imread(image_path)
if image is None:
    print("Error: Could not read the image.")
    exit()

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
text = pytesseract.image_to_string(gray)

print("Extracted Text:")
print(text)

populate_docx(text)  # Write the text into a Word doc