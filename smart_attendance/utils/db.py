import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase_client: Optional[Client] = None


def get_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")
        _supabase_client = create_client(url, key)
    return _supabase_client


def _get_bucket_name() -> str:
    return os.getenv("STORAGE_BUCKET", "students")


def ensure_bucket_exists() -> None:
    client = get_client()
    bucket = _get_bucket_name()
    try:
        client.storage.create_bucket(bucket, {"public": True})
    except Exception:
        pass


def upload_student_image(image_bytes: bytes, filename: str) -> str:
    client = get_client()
    ensure_bucket_exists()
    bucket = _get_bucket_name()

    ext = ""
    if "." in filename:
        ext = filename.split(".")[-1].lower()
    path = f"{uuid.uuid4().hex}.{ext or 'jpg'}"

    # path first, then content bytes
    client.storage.from_(bucket).upload(path, image_bytes, file_options={"contentType": f"image/{ext or 'jpeg'}"})
    public_url = client.storage.from_(bucket).get_public_url(path)
    return public_url


def add_student(name: str, image_bytes: bytes, image_filename: str) -> Dict[str, Any]:
    client = get_client()
    image_url = upload_student_image(image_bytes, image_filename)
    response = client.table("students").insert({
        "name": name,
        "image_url": image_url,
    }).execute()
    if not response.data:
        raise RuntimeError("Failed to insert student")
    return response.data[0]


def get_students() -> List[Dict[str, Any]]:
    client = get_client()
    response = client.table("students").select("*").order("created_at", desc=True).execute()
    return response.data or []


def has_marked_today(student_id: int) -> bool:
    client = get_client()
    today = datetime.now().date().isoformat()
    response = (
        client.table("attendance")
        .select("id")
        .eq("student_id", student_id)
        .eq("date", today)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def mark_attendance(student_id: int, status: str = "present") -> Dict[str, Any]:
    client = get_client()
    now = datetime.now()
    date_str = now.date().isoformat()
    time_str = now.strftime("%H:%M:%S")

    if has_marked_today(student_id):
        return {"status": "already_marked", "student_id": student_id, "date": date_str}

    response = client.table("attendance").insert({
        "student_id": student_id,
        "date": date_str,
        "time": time_str,
        "status": status,
    }).execute()
    if not response.data:
        raise RuntimeError("Failed to mark attendance")
    return response.data[0]


def get_attendance_records(date: Optional[str] = None, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
    client = get_client()
    query = client.table("attendance").select("*")
    if date:
        query = query.eq("date", date)
    if student_id is not None:
        query = query.eq("student_id", student_id)
    response = query.order("date", desc=True).order("time", desc=True).execute()
    return response.data or []
