import json
import os
from io import BytesIO
from typing import Dict, List, Tuple, Optional

import numpy as np
from PIL import Image
import face_recognition


ENCODINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "encodings.json")


def _ensure_encodings_file_exists() -> None:
    if not os.path.exists(ENCODINGS_FILE_PATH):
        with open(ENCODINGS_FILE_PATH, "w", encoding="utf-8") as fp:
            json.dump({"encodings": []}, fp)


def load_known_encodings() -> Tuple[Dict[int, np.ndarray], Dict[int, str]]:
    """Load known face encodings from local JSON store.

    Returns a mapping of student_id -> encoding (numpy array) and student_id -> name.
    """
    _ensure_encodings_file_exists()
    with open(ENCODINGS_FILE_PATH, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    id_to_encoding: Dict[int, np.ndarray] = {}
    id_to_name: Dict[int, str] = {}
    for item in data.get("encodings", []):
        try:
            student_id = int(item["student_id"])  # stored as int or str
            id_to_encoding[student_id] = np.array(item["encoding"], dtype="float32")
            id_to_name[student_id] = item.get("name", str(student_id))
        except Exception:
            continue
    return id_to_encoding, id_to_name


def save_student_encoding(student_id: int, name: str, encoding: np.ndarray) -> None:
    """Persist a student's face encoding locally for quick matching."""
    _ensure_encodings_file_exists()
    with open(ENCODINGS_FILE_PATH, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    enc_list = data.get("encodings", [])
    # Remove existing entry if present
    enc_list = [e for e in enc_list if int(e.get("student_id", -1)) != int(student_id)]
    enc_list.append({
        "student_id": int(student_id),
        "name": name,
        "encoding": encoding.astype(float).tolist(),
    })
    data["encodings"] = enc_list

    with open(ENCODINGS_FILE_PATH, "w", encoding="utf-8") as fp:
        json.dump(data, fp)


def compute_face_encoding_from_image_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """Compute a single face encoding from raw image bytes. Returns None if no single face found."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    np_image = np.array(image)
    face_locations = face_recognition.face_locations(np_image)
    if len(face_locations) != 1:
        return None
    encodings = face_recognition.face_encodings(np_image, known_face_locations=face_locations)
    if not encodings:
        return None
    return encodings[0]


def match_faces_in_frame(
    frame_rgb: np.ndarray,
    known_encodings: Dict[int, np.ndarray],
    tolerance: float = 0.45,
) -> List[Tuple[Tuple[int, int, int, int], Optional[int], float]]:
    """Detect and match faces in a frame.

    Returns a list of tuples: (top, right, bottom, left), matched_student_id (or None), distance
    """
    face_locations = face_recognition.face_locations(frame_rgb)
    face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

    results: List[Tuple[Tuple[int, int, int, int], Optional[int], float]] = []
    known_ids = list(known_encodings.keys())
    known_vectors = [known_encodings[sid] for sid in known_ids]
    for (face_location, face_encoding) in zip(face_locations, face_encodings):
        if known_vectors:
            distances = face_recognition.face_distance(known_vectors, face_encoding)
            best_index = int(np.argmin(distances))
            best_distance = float(distances[best_index])
            best_id: Optional[int] = None
            if best_distance <= tolerance:
                best_id = known_ids[best_index]
            results.append((face_location, best_id, best_distance))
        else:
            results.append((face_location, None, 1.0))
    return results
