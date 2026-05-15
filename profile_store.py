import json
import os
import streamlit as st
from typing import Dict, List, Any, Tuple
from datetime import datetime
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "profiles")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _make_filepath(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


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


def export_all_profiles() -> str:
    profiles = load_all_profiles()
    export_data = {
        "version": "1.0",
        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profiles": profiles
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)


def import_profiles(json_data: str) -> int:
    _ensure_dir()
    data = json.loads(json_data)
    count = 0
    if isinstance(data, list):
        for record in data:
            if "profile" in record:
                pid = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex[:4]
                profile_data = {"id": pid, "profile": record["profile"], "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                with open(_make_filepath(f"{pid}.json"), "w", encoding="utf-8") as f:
                    json.dump(profile_data, f, ensure_ascii=False, indent=2)
                count += 1
    return count
