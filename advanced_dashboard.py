import streamlit as st
import pandas as pd
from PIL import Image
import os
import time

st.set_page_config(page_title="Enterprise Biometrics", layout="wide")

# Custom CSS for a clean, modern look
st.markdown("""
    <style>
    .main-header { font-family: 'Segoe UI', sans-serif; color: #1E88E5; font-weight: bold; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #333; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🏢 Enterprise Biometric Security Dashboard</h1>", unsafe_allow_html=True)

LOG_FILE = "security_log.csv"
IMAGE_PATH = "debug_latest_photo.jpg"

# Safely load the CSV database into a Pandas Dataframe
@st.cache_data(ttl=1) # Cache clears every 1 second to fetch new data
def load_data():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["Timestamp", "Name", "Status", "Message"])

df = load_data()

# Create 3 modern tabs for UI navigation
tab_live, tab_analytics, tab_admin = st.tabs(["🔴 Live Viewfinder", "📊 Analytics & Logs", "⚙️ Admin Settings"])

with tab_live:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Latest Security Feed")
        if os.path.exists(IMAGE_PATH):
            try:
                with Image.open(IMAGE_PATH) as img:
                    st.image(img.copy(), width='stretch', channels="BGR")
            except Exception:
                pass
        else:
            st.info("Awaiting first camera trigger...")

    with col2:
        st.markdown("### Instant Status")
        # Display an alert animation based on the very last entry in the database
        if not df.empty:
            last_entry = df.iloc[-1]
            if last_entry["Status"] == "SUCCESS":
                st.success(f"✅ {last_entry['Message']} ({last_entry['Name']})")
                #st.balloons() # Subtle celebration animation
            elif last_entry["Status"] == "DENIED":
                st.error(f"🚨 INTRUDER ALERT: Access Denied at {last_entry['Timestamp']}")
            else:
                st.warning("⚠️ Scan failed. No face detected.")
        else:
            st.write("No scans recorded yet.")

with tab_analytics:
    st.markdown("### System Telemetry")
    
    # Calculate live metrics directly from the dataframe
    total_scans = len(df)
    success_count = len(df[df["Status"] == "SUCCESS"])
    denied_count = len(df[df["Status"] == "DENIED"])
    success_rate = round((success_count / total_scans * 100), 1) if total_scans > 0 else 0

    # Display Metrics in a modern 4-column layout
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Clock-Ins", total_scans)
    m2.metric("Authorized Access", success_count)
    m3.metric("Security Breaches", denied_count, delta_color="inverse")
    m4.metric("Verification Rate", f"{success_rate}%")

    st.markdown("---")
    st.markdown("### Detailed Audit Log")
    # Display the full database table, newest records first
    st.dataframe(df.sort_values(by="Timestamp", ascending=False), width='stretch')

with tab_admin:
    st.markdown("### Database Management")
    st.warning("Warning: This action is permanent and cannot be undone.")
    
    # Button to physically delete the CSV file
    if st.button("🗑️ Erase All Security Logs"):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            st.success("Logs successfully wiped. A new database will be created on the next scan.")
            time.sleep(1) # Brief pause so the user sees the success message
            st.rerun()

# Auto-refresh loop (Placed at the bottom so it loops the whole UI)
time.sleep(1.5)
st.rerun()