# 🔒 Biometric Time Clock (ESP32-CAM + Python AI)

A hardware-software hybrid biometric security system designed for enterprise clock-in simulation. This project bridges a low-cost microcontroller with a heavy-duty Python Computer Vision backend to achieve real-time, highly reliable facial recognition.

## ⚙️ Architecture & Process Workflow

This system operates on a client-server architecture, offloading heavy neural network tensor math from the MCU to a local server.

1. **Hardware Interrupt:** A physical push-button acts as the trigger. To conserve GPIO pins, it is wired to `GPIO 1` (U0T/Serial TX), gracefully commandeering the serial pin after boot.
2. **Double-Grab Capture:** Upon interrupt, the ESP32-CAM flushes the PSRAM frame buffer (discarding stale frames) and captures a fresh JPEG using the OV3660 sensor.
3. **HTTP Transmission:** The image is POSTed over a local Wi-Fi Hotspot to a Python Flask REST API on port 5050.
4. **Pre-Processing (Auto-Rotation):** The Python server decodes the JPEG using `OpenCV`. It employs a brute-force rotation matrix loop (0°, 90°, 180°, 270°) to guarantee the face is upright regardless of camera mounting orientation.
5. **Biometric Inference:** The image is passed to the `face_recognition` library (built on `dlib`'s state-of-the-art C++ deep learning toolkit). It maps the geometric facial landmarks and compares the 128-dimension face encoding against known encodings in RAM.
6. **Hardware/Software Feedback:** * The server responds to the ESP32 with a formatted string, which is instantly parsed and printed to a 16x2 LCD display.
    * Simultaneously, the server saves an annotated debug frame, which is picked up by a reactive `Streamlit` dashboard for real-time monitoring.

## 🛠️ Hardware Requirements
* **ESP32-CAM** (with OV2640 or OV3660 sensor)
* **16x2 LCD Display** (Parallel configuration)
* **Tactile Push Button** (Modified to 2 diagonal pins to prevent dead-shorts)
* **Breadboard & Jumper Wires**

## 💻 Software Stack
* **C++ / Arduino IDE:** ESP32 hardware logic, Wi-Fi stack, and HTTP client.
* **Python 3.x:** Primary backend server and computer vision logic.
* **Flask:** REST API endpoint handling.
* **OpenCV (`cv2`):** Image decoding, rotation, and bounding box drawing.
* **face_recognition (`dlib`):** Facial landmark detection and matching.
* **Streamlit:** Live-updating UI dashboard.

## 🚀 How to Run

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```
2. **Add Known Faces:**
Place a clear, well-lit photo of authorized users in the known_faces/ directory. Name the file with their name (e.g., Om.jpg).

3. **Start the Backend:**
```bash
python server.py
```

4. **Start the Dashboard:**
Open a second terminal and run:
```bash
streamlit run dashboard.py
```

5. **Power the Hardware:**
Provide 5V power to the ESP32-CAM. Wait 5 seconds for boot, then hot-plug the LCD power line. Press the hardware button to trigger the pipeline!
