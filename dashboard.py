import streamlit as st
from PIL import Image
import time
import os

st.set_page_config(page_title="Biometric Security", layout="centered")

st.markdown("<h1 style='text-align: center; color: #4fc3f7;'>🔒 Biometric Time Clock Monitor</h1>", unsafe_allow_html=True)
st.markdown("---")

image_placeholder = st.empty()

if os.path.exists("debug_latest_photo.jpg"):
    try:
        with Image.open("debug_latest_photo.jpg") as img:
            img_copy = img.copy()
        image_placeholder.image(img_copy, width='stretch', caption="Latest Verification Attempt")
    except:
        pass
else:
    image_placeholder.info("Awaiting first scan from ESP32...")

# Refresh every 1.5 seconds
time.sleep(1.5)
st.rerun()