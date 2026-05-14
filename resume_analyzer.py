import re
import json
import streamlit as st
from api_client import call_api, parse_json_response, truncate_text
from typing import Dict, List, Any


def extract_resume_profile(resume_text: str) -> Dict[str, Any]:
    resume_text = truncate_text(resume_text)
    prompt = f"""请从以下简历中提取详细的人才画像。

重要提示：
- total_experience_years 必须只计算工作经历的总年限，不要把教育年份算进去
- 如果简历明确写了"X年经验"，直接使用该数字
- 如果没有明确写，根据工作经历的起止时间计算

简历内容：
{resume_text}

请严格按以下JSON格式返回（不要添加任何其他文字，只返回JSON）：

{{
    "name": "姓名",
    "contact_info": {{"email": "邮箱", "phone": "电话", "location": "地点"}},
    "summary": "个人总结/职业概述",
    "current_job": "当前职位",
    "current_company": "当前公司",
    "total_experience_years": 0,
    "education": [{{"degree": "学位", "school": "学校", "major": "专业", "graduation_year": "毕业年份"}}],
    "work_experience": [{{"position": "职位", "company": "公司", "duration": "在职时间", "responsibilities": ["职责1"], "achievements": ["成就1"]}}],
    "skills": {{"technical_skills": ["技能1"], "soft_skills": ["软技能1"], "language_skills": [{{"language": "语言", "level": "水平"}}], "tools": ["工具1"]}},
    "certifications": [{{"name": "证书名称", "issuer": "颁发机构", "year": "年份"}}],
    "projects": [{{"name": "项目名称", "duration": "时间", "description": "描述", "technologies": ["技术1"]}}],
    "career_gaps": [],
    "job_hopping_frequency": "高/中/低",
    "industries_worked": ["行业1"]
}}"""

    try:
        result_text = call_api(prompt, max_tokens=2000)
        return parse_json_response(result_text)
    except json.JSONDecodeError:
        return _extract_fallback_profile(resume_text)
    except Exception as e:
        st.warning(f"AI分析失败，使用本地解析: {e}")
        return _extract_fallback_profile(resume_text)


def _extract_fallback_profile(resume_text: str) -> Dict[str, Any]:
    return {
        "name": _extract_name(resume_text),
        "contact_info": {"email": _extract_email(resume_text), "phone": _extract_phone(resume_text), "location": ""},
        "summary": "", "current_job": "", "current_company": "",
        "total_experience_years": _calculate_total_experience(resume_text),
        "education": [], "work_experience": [],
        "skills": {"technical_skills": _extract_list_field(resume_text, r"技能|Skills|技术能力"), "soft_skills": [], "language_skills": [], "tools": []},
        "certifications": [], "projects": [], "career_gaps": [],
        "job_hopping_frequency": "未知", "industries_worked": []
    }


def _extract_name(text: str) -> str:
    for line in text.split("\n")[:5]:
        line = line.strip()
        if 2 <= len(line) <= 4 and re.match(r'^[一-鿿]+$', line):
            return line
    return ""

def _extract_email(text: str) -> str:
    m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    return m.group(0) if m else ""

def _extract_phone(text: str) -> str:
    m = re.search(r'\d{3}[-.]?\d{4}[-.]?\d{4}', text)
    return m.group(0) if m else ""

def _calculate_total_experience(text: str) -> int:
    explicit = re.search(r'(\d{1,2})\s*[年年]\s*(?:以上\s*)?(?:工作|从业|开发|项目|相关|管理)?(?:经验|经历)', text)
    if explicit:
        return int(explicit.group(1))
    m = re.search(r'(?:工作经[验历]|Work\s*Experience)', text, re.IGNORECASE)
    if m:
        edu = re.search(r'(?:教育背景|Education|学历|项目经[验历]|技能)', text[m.end():], re.IGNORECASE)
        section = text[m.end():m.end() + edu.start()] if edu else text[m.end():]
        years = [int(y) for y in re.findall(r'(20\d{2}|19\d{2})', section) if 1990 <= int(y) <= 2026]
        if years:
            return max(years) - min(years)
    return 0

def _extract_list_field(text: str, pattern: str) -> list:
    lines = text.split("\n")
    result, capture = [], False
    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            capture = True
            continue
        if capture:
            stripped = line.strip()
            if not stripped:
                if result: break
                continue
            cleaned = re.sub(r'^[\s\d\.\-\)\(\*\•:：]+', '', stripped)
            if cleaned and len(cleaned) > 1:
                result.append(cleaned)
            if len(result) >= 10: break
    return result
