import re
import json
import streamlit as st
from api_client import call_api, parse_json_response, truncate_text
from typing import Dict, List, Any


def extract_talent_profile(jd_text: str) -> Dict[str, Any]:
    jd_text = truncate_text(jd_text)
    prompt = f"""请从以下职位描述中提取详细的人才画像。

职位描述：
{jd_text}

请严格按以下JSON格式返回（不要添加任何其他文字，只返回JSON）：

{{
    "job_title": "职位名称",
    "required_skills": ["技能1", "技能2"],
    "preferred_skills": ["技能1", "技能2"],
    "experience_level": "经验要求描述",
    "experience_years": 0,
    "education": "教育要求",
    "responsibilities": ["职责1", "职责2"],
    "qualifications": ["资格1", "资格2"],
    "soft_skills": ["软技能1", "软技能2"],
    "industry_knowledge": ["行业知识1", "行业知识2"],
    "tools_technologies": ["工具/技术1", "工具/技术2"],
    "language_requirements": ["语言要求1"],
    "salary_range": "薪资范围（如有）",
    "job_type": "工作类型",
    "location": "工作地点"
}}"""

    try:
        result_text = call_api(prompt, max_tokens=2000)
        return parse_json_response(result_text)
    except json.JSONDecodeError:
        return _extract_fallback_profile(jd_text)
    except Exception as e:
        st.warning(f"AI分析失败，使用本地解析: {e}")
        return _extract_fallback_profile(jd_text)


def _extract_fallback_profile(jd_text: str) -> Dict[str, Any]:
    return {
        "job_title": _extract_field(jd_text, r"职位名称|岗位名称|Position|职位", 30),
        "required_skills": _extract_list_field(jd_text, r"技能要求|Skills|技术能力|任职要求"),
        "preferred_skills": [],
        "experience_level": _extract_field(jd_text, r"经验要求|Experience", 30),
        "experience_years": _extract_years(jd_text),
        "education": _extract_field(jd_text, r"教育要求|Education|学历", 30),
        "responsibilities": _extract_list_field(jd_text, r"岗位职责|Responsibilities|工作职责|职责描述"),
        "qualifications": _extract_list_field(jd_text, r"任职要求|Qualifications|要求"),
        "soft_skills": _extract_list_field(jd_text, r"软技能|Soft Skills|个人素质"),
        "industry_knowledge": [],
        "tools_technologies": _extract_list_field(jd_text, r"工具|Tools|技术栈"),
        "language_requirements": [],
        "salary_range": "", "job_type": "", "location": ""
    }


def _extract_field(text: str, pattern: str, max_length: int = 50) -> str:
    m = re.search(f"(?:{pattern})[:\\s：]*([^\\n]{{1,{max_length}}})", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_years(text: str) -> int:
    for pat in [r"(\d+)\s*年", r"(\d+)\s*years?", r"(\d+)\s*yrs?"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def _extract_list_field(text: str, pattern: str) -> List[str]:
    lines = text.split("\n")
    result, capture = [], False
    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            capture = True
            continue
        if capture:
            stripped = line.strip()
            if not stripped:
                if result:
                    break
                continue
            cleaned = re.sub(r'^[\s\d\.\-\)\(\*\•:：]+', '', stripped)
            if cleaned and len(cleaned) > 1:
                result.append(cleaned)
            if len(result) >= 10:
                break
    return result
