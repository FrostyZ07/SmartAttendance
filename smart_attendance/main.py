import os
import time
from datetime import datetime
from typing import Dict

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import sys
from pathlib import Path

# Ensure project root is on sys.path to allow absolute package imports when running via Streamlit
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smart_attendance.utils import db
from smart_attendance.utils.face_utils import (
    compute_face_encoding_from_image_bytes,
    load_known_encodings,
    match_faces_in_frame,
    save_student_encoding,
)


load_dotenv()

st.set_page_config(page_title="Smart Attendance", page_icon="🧑‍🎓", layout="wide")


def require_auth() -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin")
        if username == admin_user and password == admin_pass:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    return False


if not require_auth():
    st.stop()


st.title("Smart Attendance System")


tab_register, tab_attendance, tab_reports = st.tabs([
    "Register Student",
    "Start Attendance",
    "View Reports",
])


with tab_register:
    st.header("Register Student")
    name = st.text_input("Student Name")
    uploaded = st.file_uploader("Student Image", type=["jpg", "jpeg", "png"])
    if st.button("Register", type="primary"):
        if not name:
            st.error("Please enter a name.")
        elif not uploaded:
            st.error("Please upload an image.")
        else:
            img_bytes = uploaded.read()
            encoding = compute_face_encoding_from_image_bytes(img_bytes)
            if encoding is None:
                st.error("Please upload an image with exactly one clear face.")
            else:
                try:
                    student = db.add_student(name=name, image_bytes=img_bytes, image_filename=uploaded.name)
                    save_student_encoding(student_id=int(student["id"]), name=name, encoding=encoding)
                    st.success(f"Registered {name} (ID: {student['id']}).")
                except Exception as e:
                    st.error(f"Failed to register student: {e}")


with tab_attendance:
    st.header("Real-time Attendance")
    tolerance = st.slider("Match tolerance (lower is stricter)", 0.35, 0.65, 0.45, 0.01)

    if "attendance_running" not in st.session_state:
        st.session_state.attendance_running = False

    if st.button("Load Known Encodings"):
        id_to_encoding, id_to_name = load_known_encodings()
        st.session_state["known_encodings"] = id_to_encoding
        st.session_state["known_names"] = id_to_name
        st.success(f"Loaded {len(id_to_encoding)} known encodings.")

    start = st.button("Start Attendance", disabled=st.session_state.attendance_running)
    stop = st.button("Stop", disabled=not st.session_state.attendance_running)

    if start:
        st.session_state.attendance_running = True
    if stop:
        st.session_state.attendance_running = False

    placeholder = st.empty()
    status_placeholder = st.empty()

    if st.session_state.attendance_running:
        id_to_encoding: Dict[int, np.ndarray] = st.session_state.get("known_encodings", {})
        id_to_name: Dict[int, str] = st.session_state.get("known_names", {})
        if not id_to_encoding:
            id_to_encoding, id_to_name = load_known_encodings()
            st.session_state["known_encodings"] = id_to_encoding
            st.session_state["known_names"] = id_to_name

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Could not access webcam.")
            st.session_state.attendance_running = False
        else:
            already_marked = set()
            try:
                while st.session_state.attendance_running:
                    ok, frame_bgr = cap.read()
                    if not ok:
                        status_placeholder.error("Frame capture failed.")
                        break
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                    matches = match_faces_in_frame(frame_rgb, id_to_encoding, tolerance=tolerance)

                    # Draw boxes and names
                    display = frame_rgb.copy()
                    for (top, right, bottom, left), student_id, distance in matches:
                        color = (0, 255, 0) if student_id is not None else (255, 0, 0)
                        cv2.rectangle(display, (left, top), (right, bottom), color, 2)
                        label = "Unknown"
                        if student_id is not None:
                            label = f"{id_to_name.get(student_id, student_id)} ({distance:.2f})"
                            if (student_id not in already_marked) and (not db.has_marked_today(student_id)):
                                try:
                                    db.mark_attendance(student_id)
                                    already_marked.add(student_id)
                                    status_placeholder.success(f"Marked present for {id_to_name.get(student_id, student_id)}")
                                except Exception as e:
                                    status_placeholder.error(f"Mark failed for {student_id}: {e}")
                        cv2.putText(display, label, (left, top - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    placeholder.image(display, channels="RGB")

                    # small sleep to reduce CPU usage
                    time.sleep(0.02)
            finally:
                cap.release()


with tab_reports:
    st.header("Attendance Reports")
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("Date", value=None, format="YYYY-MM-DD")
    with col2:
        students = db.get_students()
        student_map = {s["name"]: s["id"] for s in students}
        student_names = ["All"] + list(student_map.keys())
        selected_name = st.selectbox("Student", student_names)
        selected_student_id = None if selected_name == "All" else int(student_map[selected_name])

    date_str = date_filter.isoformat() if date_filter else None
    records = db.get_attendance_records(date=date_str, student_id=selected_student_id)

    if records:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Export CSV", data=csv_bytes, file_name=f"attendance_{datetime.now().date().isoformat()}.csv", mime="text/csv")
    else:
        st.info("No records found for selected filters.")
