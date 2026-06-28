import cv2
import face_recognition
import numpy as np
import os
import csv
from datetime import datetime
from supabase import create_client, Client

import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://dwunumnikuafvlgcgrnw.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

known_encodings = []
known_names = []

dataset_path = "dataset"

for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)

        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(person)

print("Dataset Loaded")

# ==========================
# Attendance Function
# ==========================
def mark_attendance(person_identifier):
    if not supabase:
        print("Supabase client not initialized")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    entry_time_str = datetime.now().strftime("%H:%M:%S")

    try:
        # Parse roll_no and name from dataset folder name
        parts = person_identifier.split('_', 1)
        if len(parts) == 2:
            extracted_roll_no = parts[0]
            extracted_name = parts[1]
        else:
            extracted_roll_no = person_identifier
            extracted_name = person_identifier

        # Find the student in the database
        res = supabase.table("students").select("*").eq("roll_no", extracted_roll_no).execute()
        student_id = None
        
        if res.data and len(res.data) > 0:
            student_id = res.data[0]["id"]
            db_name = res.data[0]["name"]
            db_roll = res.data[0]["roll_no"]
        else:
            # Auto-register student in the students table if they are in the dataset
            insert_res = supabase.table("students").insert({
                "roll_no": extracted_roll_no,
                "name": extracted_name
            }).execute()
            
            if insert_res.data and len(insert_res.data) > 0:
                student_id = insert_res.data[0]["id"]
                db_name = extracted_name
                db_roll = extracted_roll_no
                print(f"Auto-registered {db_name} ({db_roll}) into students database.")
            else:
                print(f"Failed to auto-register {person_identifier}.")
                return

        # Check if attendance already marked today
        existing = (
            supabase.table("attendance")
            .select("*")
            .eq("student_id", student_id)
            .eq("date", today_str)
            .execute()
        )

        if not existing.data or len(existing.data) == 0:
            # We attempt to insert into attendance.
            # NOTE: For this to succeed, your Supabase 'attendance' table MUST have
            # the 'name', 'roll_no', and 'entry_time' columns added!
            supabase.table("attendance").insert({
                "student_id": student_id,
                "date": today_str,
                "status": "Present",
                "name": db_name,
                "roll_no": db_roll,
                "entry_time": entry_time_str
            }).execute()

            print(f"{db_roll} {db_name} Attendance Marked as Present at {entry_time_str}")
    except Exception as e:
        print(f"Error marking attendance: {e}")

# ==========================
# Webcam Recognition
# ==========================
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)

    for face_encoding, (top, right, bottom, left) in zip(encodings, locations):

        matches = face_recognition.compare_faces(
            known_encodings,
            face_encoding
        )

        name = "Unknown"

        distances = face_recognition.face_distance(
            known_encodings,
            face_encoding
        )

        if len(distances) > 0:
            best_match = np.argmin(distances)

            if matches[best_match]:
                name = known_names[best_match]
                mark_attendance(name)

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            name,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()