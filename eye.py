import cv2
import mediapipe as mp
import time
import csv
import os
import math
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

csv_filename = "C:/Users/R Nishanth Reddy/Desktop/eye_tracking_data.csv"

if not os.path.exists(csv_filename):
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Eye Direction", "Angle Change", "Arc Length", "Pupil Position"])

def log_eye_movement(direction, angle, arc_length, pupil_position):
    timestamp = time.strftime("%H:%M:%S")
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, direction, round(angle, 4), round(arc_length, 4), pupil_position])

def calculate_angle_and_arc(prev_pos, curr_pos, prev_angle):
    x_prev, y_prev = prev_pos
    x_curr, y_curr = curr_pos
    theta = math.atan2(y_curr - y_prev, x_curr - x_prev)
    delta_theta = theta - prev_angle if prev_angle is not None else 0
    delta_theta = math.atan2(math.sin(delta_theta), math.cos(delta_theta))
    r = math.sqrt((x_curr - x_prev) ** 2 + (y_curr - y_prev) ** 2)
    arc_length = abs(r * delta_theta)
    return delta_theta, arc_length, theta

def get_eye_bounds(landmarks, eye_indices, frame):
    xs = [int(landmarks[i].x * frame.shape[1]) for i in eye_indices]
    ys = [int(landmarks[i].y * frame.shape[0]) for i in eye_indices]
    return min(xs), min(ys), max(xs), max(ys)

def get_pupil_position(landmarks, eye_indices, frame):

    
    pupil_x = sum([landmarks[i].x for i in eye_indices]) / len(eye_indices)
    pupil_y = sum([landmarks[i].y for i in eye_indices]) / len(eye_indices)
    return int(pupil_x * frame.shape[1]), int(pupil_y * frame.shape[0])

cap = cv2.VideoCapture(0)
prev_pupil_center = None
prev_angle = None

LEFT_PUPIL_INDICES = [468]
RIGHT_PUPIL_INDICES = [473]

while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            left_pupil = get_pupil_position(face_landmarks.landmark, LEFT_PUPIL_INDICES, frame)
            right_pupil = get_pupil_position(face_landmarks.landmark, RIGHT_PUPIL_INDICES, frame)
            pupil_center = ((left_pupil[0] + right_pupil[0]) // 2, (left_pupil[1] + right_pupil[1]) // 2)
            
            cv2.rectangle(frame, (left_pupil[0] - 5, left_pupil[1] - 5), (left_pupil[0] + 5, left_pupil[1] + 5), (255, 0, 0), 2)
            cv2.rectangle(frame, (right_pupil[0] - 5, right_pupil[1] - 5), (right_pupil[0] + 5, right_pupil[1] + 5), (255, 0, 0), 2)

            frame_width, frame_height = frame.shape[1], frame.shape[0]
            
            if pupil_center[0] < frame_width * 0.4:
                direction = "Left"
            elif pupil_center[0] > frame_width * 0.6:
                direction = "Right"
            elif pupil_center[1] < frame_height * 0.4:
                direction = "Up"
            elif pupil_center[1] > frame_height * 0.6:
                direction = "Down"
            else:
                direction = "Center"

            if prev_pupil_center is not None:
                angle_change, arc_length, prev_angle = calculate_angle_and_arc(prev_pupil_center, pupil_center, prev_angle)
                log_eye_movement(direction, angle_change, arc_length, pupil_center)
            else:
                angle_change, arc_length = 0, 0
                prev_angle = 0

            prev_pupil_center = pupil_center

            cv2.putText(frame, f"Direction: {direction}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Angle Change: {round(angle_change, 2)} rad", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(frame, f"Arc Length: {round(arc_length, 2)} px", (30, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow("Pupil Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
