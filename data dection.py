import cv2
import pytesseract
import sqlite3
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, Toplevel, Canvas
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

def insert_vehicle_info(conn, number_plate, owner_name, traffic_violations, emission_expiry_date):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Vehicle VALUES (?, ?, ?, ?)", (number_plate, owner_name, traffic_violations, emission_expiry_date))
    conn.commit()

def browse_and_detect():
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg;.jpeg;*.png")])
    if image_path:
        image = cv2.imread(image_path)
        number_plate, highlighted_image = detect_number_plate(image)

        if number_plate:
            result = fetch_vehicle_info(conn, number_plate)
            if result:
                show_result_window(highlighted_image, number_plate, result)
            else:
                messagebox.showinfo("Info", "Number plate not found in database. Add new vehicle.")
                add_new_vehicle(number_plate)
        else:
            messagebox.showerror("Error", "Number plate could not be detected.")

def show_result_window(image, number_plate, info):
    result_window = Toplevel(app)
    result_window.title("Detection Result and Vehicle Information")

    # Display detected image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)

    canvas = Canvas(result_window, width=image.width(), height=image.height())
    canvas.grid(row=0, column=0, rowspan=4, padx=10, pady=10)
    canvas.create_image(0, 0, anchor="nw", image=image)
    canvas.image = image

    # Display vehicle information
    Label(result_window, text="Vehicle Information", font=("Arial", 16)).grid(row=0, column=1, pady=1, sticky="w")
    Label(result_window, text=f"Number Plate: {info[0]}", font=("Arial", 12)).grid(row=1, column=1, pady=5, sticky="w")
    Label(result_window, text=f"Owner Name: {info[1]}", font=("Arial", 12)).grid(row=2, column=1, pady=5, sticky="w")
    Label(result_window, text=f"Traffic Violations: {info[2]}", font=("Arial", 12)).grid(row=3, column=1, pady=5, sticky="w")
    Label(result_window, text=f"Emission Expiry Date: {info[3]}", font=("Arial", 12)).grid(row=4, column=1, pady=5, sticky="w")

def add_new_vehicle(number_plate):
    def save_new_vehicle():
        owner_name = owner_name_entry.get()
        traffic_violations = traffic_violations_entry.get()
        emission_expiry_date = emission_expiry_date_entry.get()

        if owner_name and traffic_violations and emission_expiry_date:
            insert_vehicle_info(conn, number_plate, owner_name, traffic_violations, emission_expiry_date)
            messagebox.showinfo("Success", "Vehicle information saved successfully.")
            new_vehicle_window.destroy()
        else:
            messagebox.showerror("Error", "All fields are required.")

    new_vehicle_window = Toplevel(app)
    new_vehicle_window.title("Add New Vehicle")

    Label(new_vehicle_window, text="Number Plate:").grid(row=0, column=0, padx=10, pady=5)
    Label(new_vehicle_window, text=number_plate).grid(row=0, column=1, padx=10, pady=5)

    Label(new_vehicle_window, text="Owner Name:").grid(row=1, column=0, padx=10, pady=5)
    owner_name_entry = Entry(new_vehicle_window)
    owner_name_entry.grid(row=1, column=1, padx=10, pady=5)

    Label(new_vehicle_window, text="Traffic Violations:").grid(row=2, column=0, padx=10, pady=5)
    traffic_violations_entry = Entry(new_vehicle_window)
    traffic_violations_entry.grid(row=2, column=1, padx=10, pady=5)

    Label(new_vehicle_window, text="Emission Expiry Date:").grid(row=3, column=0, padx=10, pady=5)
    emission_expiry_date_entry = Entry(new_vehicle_window)
    emission_expiry_date_entry.grid(row=3, column=1, padx=10, pady=5)

    Button(new_vehicle_window, text="Save", command=save_new_vehicle).grid(row=4, column=0, columnspan=2, pady=20)

# Main window setup
conn = initialize_db()
app = Tk()
app.title("Automatic Number Plate Detection")

Label(app, text="Automatic Number Plate Detection", font=("Arial", 16)).pack(pady=10)
Button(app, text="Upload Image and Detect", command=browse_and_detect).pack(pady=5)
Button(app, text="Exit", command=app.destroy).pack(pady=5)

app.mainloop()

conn.close()