# Title: Automatic Number Plate Detection System
# Copyright: 2025 by [Your Name or Organization]

import cv2
import pytesseract
import sqlite3
from tkinter import Tk, Label, Entry, Button, filedialog, Canvas, Frame, messagebox
from PIL import Image, ImageTk

# Initialize Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Database connection setup
def initialize_db():
    conn = sqlite3.connect("vehicle_info.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Vehicle (
                        NumberPlate TEXT PRIMARY KEY,
                        OwnerName TEXT,
                        TrafficViolations TEXT,
                        EmissionExpiryDate TEXT
                      )''')
    conn.commit()
    return conn

def detect_number_plate(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 170, 200)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    number_plate = None
    highlighted_image = image.copy()

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            roi = gray[y:y+h, x:x+w]

            number_plate = pytesseract.image_to_string(roi, config='--psm 8').strip()

            cv2.rectangle(highlighted_image, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(highlighted_image, number_plate, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            break

    return number_plate, highlighted_image

def fetch_vehicle_info(conn, number_plate):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vehicle WHERE NumberPlate = ?", (number_plate,))
    return cursor.fetchone()

def upload_and_detect():
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg;.jpeg;*.png")])
    if image_path:
        image = cv2.imread(image_path)
        number_plate, highlighted_image = detect_number_plate(image)

        if number_plate:
            display_image(highlighted_image)
            display_vehicle_info(number_plate)
        else:
            messagebox.showerror("Error", "Number plate could not be detected.")

def display_image(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)

    canvas_left.image = image
    canvas_left.create_image(0, 0, anchor="nw", image=image)

def display_vehicle_info(number_plate):
    for widget in info_frame.winfo_children():
        widget.destroy()

    result = fetch_vehicle_info(conn, number_plate)

    if result:
        Label(info_frame, text=f"Number Plate: {result[0]}", font=("Arial", 14)).pack(anchor="w", pady=5)
        Label(info_frame, text=f"Owner Name: {result[1]}", font=("Arial", 14)).pack(anchor="w", pady=5)
        Label(info_frame, text=f"Traffic Violations: {result[2]}", font=("Arial", 14)).pack(anchor="w", pady=5)
        Label(info_frame, text=f"Emission Expiry Date: {result[3]}", font=("Arial", 14)).pack(anchor="w", pady=5)
    else:
        Label(info_frame, text="Vehicle information not found.", font=("Arial", 14), fg="red").pack(anchor="w", pady=5)

# Main window setup
conn = initialize_db()
app = Tk()
app.title("Automatic Number Plate Detection")
app.geometry("1520x700")
app.configure(bg="#f0f0f0")
Label(app, text="Team-MACHINE MAVERICKS", font=("Arial", 32)).pack(pady=10)
Label(app, text="AutoID Insight: License Plate Detection with Database Integration", font=("Arial", 28)).pack(pady=10)

# Frames
left_frame = Frame(app, width=800, height=1000, bg="#ffffff")
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
right_frame = Frame(app, width=500, height=600, bg="#f8f8f8")
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

Label(left_frame, text="Detected Image", font=("Arial", 16), bg="#ffffff").pack(pady=10)
canvas_left = Canvas(left_frame, width=500, height=300, bg="#d9d9d9")
canvas_left.pack(pady=10)

Label(right_frame, text="Vehicle Information", font=("Arial", 16), bg="#f8f8f8").pack(pady=10)
info_frame = Frame(right_frame, bg="#f8f8f8")
info_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Buttons
Button(app, text="Exit", command=app.destroy, bg="#f44336", fg="white", font=("Arial", 12)).pack(side="bottom", pady=10)
Button(app, text="Upload Image and Detect", command=upload_and_detect, bg="#4CAF50", fg="white", font=("Arial", 12)).pack(side="bottom", pady=10)


app.mainloop()

conn.close()