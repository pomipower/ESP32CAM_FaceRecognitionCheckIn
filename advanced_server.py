from flask import Flask, request
import cv2
import numpy as np
import face_recognition
import os
import csv
from datetime import datetime

app = Flask(__name__)

KNOWN_FACES_DIR = "known_faces"
LOG_FILE = "security_log.csv"
known_encodings = []
known_names = []

# Initialize the CSV database if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Name", "Status", "Message"]) # Headers

print("Loading known faces...")
for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        name = os.path.splitext(filename)[0].capitalize() 
        filepath = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(name)
            print(f"Loaded: {name}")

def log_event(name, status, message):
    """Writes a single clock-in event to the CSV database."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, name, status, message])

@app.route('/clock_in', methods=['POST'])
def process_clock_in():
    raw_data = request.data
    if not raw_data:
        return "Err\nNo Image", 400
        
    nparr = np.frombuffer(raw_data, np.uint8)
    original_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if original_bgr is None:
        return "Err\nDecode Fail", 400

    # Auto-rotation logic to find the face
    rotations = [(None), (cv2.ROTATE_90_CLOCKWISE), (cv2.ROTATE_180), (cv2.ROTATE_90_COUNTERCLOCKWISE)]
    face_locations = []
    active_rgb = None
    active_bgr = None

    for rot_code in rotations:
        test_bgr = cv2.rotate(original_bgr, rot_code) if rot_code is not None else original_bgr.copy()
        test_rgb = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(test_rgb)
        if len(face_locations) > 0:
            active_rgb = test_rgb
            active_bgr = test_bgr
            break 

    if len(face_locations) == 0:
        active_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
        active_bgr = original_bgr.copy()

    # Default states for an unknown scan
    name = "UNKNOWN"
    lcd_line1 = "ACCESS DENIED"
    lcd_line2 = "Unknown User"
    status = "DENIED"
    box_color = (0, 0, 255) 

    if len(face_locations) > 0:
        encoding = face_recognition.face_encodings(active_rgb, face_locations)[0]
        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, encoding)
        
        if True in matches:
            best_match_index = np.argmin(face_distances)
            name = known_names[best_match_index]
            time_str = datetime.now().strftime("%I:%M %p")
            
            lcd_line1 = f"Welcome, {name[:7]}!" 
            lcd_line2 = f"In: {time_str}"
            status = "SUCCESS"
            box_color = (0, 255, 0) 

        # Annotate the image
        top, right, bottom, left = face_locations[0]
        cv2.rectangle(active_bgr, (left, top), (right, bottom), box_color, 2)
        cv2.putText(active_bgr, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
    else:
        lcd_line1 = "SCAN FAILED"
        lcd_line2 = "No Face Detected"
        status = "FAILED"

    # Save image and write to database
    cv2.imwrite("debug_latest_photo.jpg", active_bgr)
    log_event(name, status, lcd_line1)
    
    print(f"Logged: {name} | {status}")
    return f"{lcd_line1}\n{lcd_line2}", 200

if __name__ == '__main__':
    print("Advanced Biometric Server Active on Port 5050...")
    app.run(host='0.0.0.0', port=5050)