import json
import os
import streamlit as st
from typing import Dict, List
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "interviews")

CATEGORIES = {
    "项目深挖-架构追问": {"icon": "🏗️", "layer": 1},
    "项目深挖-方案选型": {"icon": "⚖️", "layer": 1},
    "项目深挖-数据与指标": {"icon": "📊", "layer": 1},
    "经历真实性验证": {"icon": "🔍", "layer": 1},
    "现场轻设计题": {"icon": "📐", "layer": 2},
    "岗位技能实操": {"icon": "🔧", "layer": 2},
    "核心能力考察": {"icon": "🔧", "layer": 2},
    "技能盲区论证": {"icon": "💡", "layer": 2},
    "反作弊-细节压强": {"icon": "🎯", "layer": 3},
    "反作弊-改方案测试": {"icon": "🔄", "layer": 3},
    "反直觉问题": {"icon": "🧠", "layer": 3},
    "风险点验证": {"icon": "⚠️", "layer": 3},
    "风险点深挖": {"icon": "⚠️", "layer": 3},
    "压力/情景测试": {"icon": "⚡", "layer": 3},
    "岗位匹配验证": {"icon": "🎯", "layer": 3},
}

DIFFICULTY_LEVELS = {"低": 1, "中": 2, "高": 3}
TAGS = ["业务理解", "技术能力", "沟通能力", "解决问题"]


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _make_filepath(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def create_session() -> str:
    session_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex[:8]
    return session_id


def save_session(candidate_name: str, candidate_id: str, questions: List[Dict]) -> str:
    _ensure_dir()
    session_data = {
        "session_id": session_id,
        "candidate_name": candidate_name,
        "candidate_id": candidate_id,
        "questions": questions,
        "start_time": datetime.now().isoformat(),
        "status": "completed"
    }
    with open(_make_filepath(f"session_{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    return session_id


def submit_scores(session_id: str, scores: List[int]) -> bool:
    _ensure_dir()
    sessions_file = _make_filepath("interview_sessions.json")
    all_sessions = []
    if os.path.exists(sessions_file):
        with open(sessions_file, "r", encoding="utf-8") as f:
            all_sessions = json.load(f)

    target_session = next((s for s in all_sessions if s["session_id"] == session_id), None)
    if not target_session:
        return False

    target_session["scores"] = scores
    target_session["end_time"] = datetime.now().isoformat()
    target_session["status"] = "completed"

    all_sessions.append(target_session)
    with open(sessions_file, "w", encoding="utf-8") as f:
        json.dump(all_sessions, f, ensure_ascii=False, indent=2)
    return True


def get_session(session_id: str) -> Dict:
    _ensure_dir()
    sessions_file = _make_filepath("interview_sessions.json")
    if not os.path.exists(sessions_file):
        return {}
    all_sessions = json.load(open(sessions_file, "r", encoding="utf-8"))
    return next((s for s in all_sessions if s["session_id"] == session_id), {})


def get_all_sessions() -> List[Dict]:
    _ensure_dir()
    sessions_file = _make_filepath("interview_sessions.json")
    if not os.path.exists(sessions_file):
        return []
    with open(sessions_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_average_score(difficulty: int, category: str) -> float:
    _ensure_dir()
    sessions_file = _make_filepath("interview_sessions.json")
    if not os.path.exists(sessions_file):
        return 0
    all_sessions = json.load(open(sessions_file, "r", encoding="utf-8"))

    if difficulty not in [1, 2, 3]:
        return 0

    category_scores = []
    for s in all_sessions:
        for q in s.get("questions", []):
            if q.get("category") == category and q.get("difficulty") == difficulty:
                scores = q.get("score", [])
                if scores:
                    category_scores.append(max(scores))

    return sum(category_scores) / len(category_scores) if category_scores else 0


def get_total_score(scores: List[int]) -> int:
    return sum(scores) / len(scores) if scores else 0


def get_grade(percentage: int) -> str:
    if percentage >= 90:
        return "优秀"
    elif percentage >= 75:
        return "良好"
    elif percentage >= 60:
        return "及格"
    else:
        return "待提升"


def get_excellent_rate() -> float:
    _ensure_dir()
    sessions_file = _make_filepath("interview_sessions.json")
    if not os.path.exists(sessions_file):
        return 0
    all_sessions = json.load(open(sessions_file, "r", encoding="utf-8"))

    total_questions = sum(len(s.get("questions", [])) for s in all_sessions)
    total_answered = sum(len([q for q in s.get("questions", []) if q.get("score") is not None]) for s in all_sessions)

    return total_answered / total_questions if total_questions > 0 else 0
