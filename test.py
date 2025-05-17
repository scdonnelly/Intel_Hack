print("Hello, World!")
import cv2
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image_path = image_path = r"C:\Users\sara\Documents\Intel_Hack\test2.jpg"
if not os.path.exists(image_path):
    print(f"Error: File '{image_path}' does not exist.")
    exit()
image = cv2.imread(image_path)
if image is None:
    print("Error: Could not read the image.")
    exit()

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
text = pytesseract.image_to_string(gray)
print(text)