import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "profiles")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _make_filename(profile_id: str) -> str:
    return os.path.join(DATA_DIR, f"{profile_id}.json")


def save_profile(profile_data: Dict[str, Any], profile_id: Optional[str] = None) -> str:
    _ensure_dir()
    if profile_id is None:
        profile_id = uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "id": profile_id,
        "created_at": now,
        "updated_at": now,
        "profile": profile_data,
    }
    existing = load_profile(profile_id)
    if existing:
        record["created_at"] = existing.get("created_at", now)
    with open(_make_filename(profile_id), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return profile_id


def load_profile(profile_id: str) -> Optional[Dict]:
    path = _make_filename(profile_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_profiles() -> List[Dict]:
    _ensure_dir()
    profiles = []
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                profiles.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    profiles.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return profiles


def update_profile(profile_id: str, profile_data: Dict[str, Any]) -> bool:
    existing = load_profile(profile_id)
    if not existing:
        return False
    existing["profile"] = profile_data
    existing["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(_make_filename(profile_id), "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return True


def delete_profile(profile_id: str) -> bool:
    path = _make_filename(profile_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def export_all_profiles() -> str:
    profiles = load_all_profiles()
    return json.dumps(profiles, ensure_ascii=False, indent=2)


def import_profiles(json_str: str) -> int:
    _ensure_dir()
    data = json.loads(json_str)
    if not isinstance(data, list):
        data = [data]
    count = 0
    for record in data:
        if "profile" in record and "id" in record:
            with open(_make_filename(record["id"]), "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            count += 1
        elif "job_title" in record:
            save_profile(record)
            count += 1
    return count
