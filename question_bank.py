import json
import os
from typing import Dict, List, Any
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "questions")

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
    "压力/情景测试": {"icon": "⚡", "layer": 2},
    "岗位匹配验证": {"icon": "🎯", "layer": 2},
}

DIFFICULTY_LEVELS = {"低": 1, "中": 2, "高": 3}
TAGS = ["数据结构", "算法", "系统设计", "工程化", "业务理解"]


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _make_filepath(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def get_all_questions() -> List[Dict]:
    _ensure_dir()
    questions_file = _make_filepath("questions.json")
    if not os.path.exists(questions_file):
        return []
    with open(questions_file, "r", encoding="utf-8") as f:
        return json.load(f)


def add_question(question_data: Dict) -> bool:
    _ensure_dir()
    questions_file = _make_filepath("questions.json")
    questions = get_all_questions()
    question_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex[:4]
    question_data["id"] = question_id
    question_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions.append(question_data)
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return True


def update_question(question_id: str, updates: Dict) -> bool:
    questions_file = _make_filepath("questions.json")
    questions = get_all_questions()
    for q in questions:
        if q.get("id") == question_id:
            q.update(updates)
            break
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return True


def delete_question(question_id: str) -> bool:
    questions_file = _make_filepath("questions.json")
    questions = get_all_questions()
    questions = [q for q in questions if q.get("id") != question_id]
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return True


def get_questions_by_category(category: str) -> List[Dict]:
    all_questions = get_all_questions()
    return [q for q in all_questions if q.get("category") == category]


def get_questions_by_difficulty(difficulty: int) -> List[Dict]:
    all_questions = get_all_questions()
    return [q for q in all_questions if q.get("difficulty") == difficulty]


def get_questions_by_tag(tag: str) -> List[Dict]:
    all_questions = get_all_questions()
    return [q for q in all_questions if tag in q.get("tags", [])]


def search_questions(keyword: str) -> List[Dict]:
    all_questions = get_all_questions()
    keyword = keyword.lower()
    results = []
    for q in all_questions:
        search_text = (q.get("question", "") + " " + q.get("purpose", "")).lower()
        if keyword in search_text:
            results.append(q)
    return results


def export_questions() -> str:
    all_questions = get_all_questions()
    return json.dumps(all_questions, ensure_ascii=False, indent=2)


def import_questions(json_data: str) -> int:
    _ensure_dir()
    data = json.loads(json_data)
    count = 0
    for item in data:
        if "question" in item and "category" in item:
            questions = get_all_questions()
            existing_ids = {q["id"] for q in questions}
            if item["id"] not in existing_ids:
                item["id"] = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + os.urandom(4).hex[:4]
                questions.append(item)
                count += 1
    with open(_make_filepath("questions.json"), "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return count
