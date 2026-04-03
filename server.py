from flask import Flask, request
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime

app = Flask(__name__)

# Load Known Faces into Memory on Startup
KNOWN_FACES_DIR = "known_faces"
known_encodings = []
known_names = []

print("Loading known faces...")
for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        # The file name (without extension) becomes the user's name
        name = os.path.splitext(filename)[0].capitalize() 
        filepath = os.path.join(KNOWN_FACES_DIR, filename)
        
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(name)
            print(f"Loaded: {name}")
        else:
            print(f"Warning: No face found in {filename}")

@app.route('/clock_in', methods=['POST'])
def process_clock_in():
    raw_data = request.data
    if not raw_data:
        return "Err\nNo Image", 400
        
    nparr = np.frombuffer(raw_data, np.uint8)
    original_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if original_bgr is None:
        return "Err\nDecode Fail", 400

    # The 4 possible camera orientations
    rotations = [
        ("0 Deg", None),
        ("90 Deg Clockwise", cv2.ROTATE_90_CLOCKWISE),
        ("180 Deg Upside Down", cv2.ROTATE_180),
        ("90 Deg Counter-Clockwise", cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]

    face_locations = []
    active_rgb = None
    active_bgr = None

    # Try every rotation until we find a face
    for rot_name, rot_code in rotations:
        if rot_code is not None:
            test_bgr = cv2.rotate(original_bgr, rot_code)
        else:
            test_bgr = original_bgr.copy()
            
        test_rgb = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2RGB)
        
        # Look for faces in this specific rotation
        face_locations = face_recognition.face_locations(test_rgb)
        
        if len(face_locations) > 0:
            print(f"Face locked at {rot_name} orientation!")
            active_rgb = test_rgb
            active_bgr = test_bgr
            break # Stop rotating, we got one!

    # Default to original if NO face is found in ANY rotation
    if len(face_locations) == 0:
        active_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
        active_bgr = original_bgr.copy()

    name = "UNKNOWN"
    lcd_line1 = "ACCESS DENIED"
    lcd_line2 = "Unknown User"
    box_color = (0, 0, 255) 

    if len(face_locations) > 0:
        # Generate the encoding from the successfully rotated image
        face_encodings = face_recognition.face_encodings(active_rgb, face_locations)
        encoding = face_encodings[0]
        
        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, encoding)
        
        if True in matches:
            best_match_index = np.argmin(face_distances)
            name = known_names[best_match_index]
            
            lcd_line1 = f"Welcome, {name[:7]}!" 
            time_str = datetime.now().strftime("%I:%M %p")
            lcd_line2 = f"In: {time_str}"
            box_color = (0, 255, 0) 

        # Draw the box on the correctly rotated image
        top, right, bottom, left = face_locations[0]
        cv2.rectangle(active_bgr, (left, top), (right, bottom), box_color, 2)
        cv2.putText(active_bgr, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
    else:
        lcd_line1 = "SCAN FAILED"
        lcd_line2 = "No Face Detected"

    # Save the rotated/annotated image for Streamlit
    cv2.imwrite("debug_latest_photo.jpg", active_bgr)
    
    print(f"Result: {lcd_line1} | {lcd_line2}")
    return f"{lcd_line1}\n{lcd_line2}", 200
    
if __name__ == '__main__':
    print("Biometric Server Active on Port 5050...")
    app.run(host='0.0.0.0', port=5050)