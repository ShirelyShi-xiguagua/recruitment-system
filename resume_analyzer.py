import re
import json
import os
import streamlit as st
from anthropic import Anthropic
from typing import Dict, List, Any

def _get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    return Anthropic(api_key=api_key)

def extract_resume_profile(resume_text: str) -> Dict[str, Any]:
    """
    从简历文本中提取人才画像

    Args:
        resume_text: 简历文本内容

    Returns:
        简历人才画像字典
    """

    prompt = f"""
    请从以下简历中提取详细的人才画像，并以JSON格式返回：

    {resume_text}

    请按以下结构分析：

    {{
        "name": "姓名",
        "contact_info": {{
            "email": "邮箱",
            "phone": "电话",
            "location": "地点"
        }},
        "summary": "个人总结/职业概述",
        "current_job": "当前职位",
        "current_company": "当前公司",
        "total_experience_years": 总工作年限,
        "education": [
            {{
                "degree": "学位",
                "school": "学校",
                "major": "专业",
                "graduation_year": "毕业年份"
            }}
        ],
        "work_experience": [
            {{
                "position": "职位",
                "company": "公司",
                "duration": "在职时间",
                "responsibilities": ["职责1", "职责2", ...],
                "achievements": ["成就1", "成就2", ...]
            }}
        ],
        "skills": {{
            "technical_skills": ["技能1", "技能2", ...],
            "soft_skills": ["软技能1", "软技能2", ...],
            "language_skills": [
                {{
                    "language": "语言",
                    "level": "水平"
                }}
            ],
            "tools": ["工具1", "工具2", ...]
        }},
        "certifications": [
            {{
                "name": "证书名称",
                "issuer": "颁发机构",
                "year": "获得年份"
            }}
        ],
        "projects": [
            {{
                "name": "项目名称",
                "duration": "项目时间",
                "description": "项目描述",
                "technologies": ["技术1", "技术2", ...]
            }}
        ],
        "career_gaps": ["职业空缺期1", "职业空缺期2", ...],
        "job_hopping_frequency": "跳槽频率（高/中/低）",
        "industries_worked": ["行业1", "行业2", ...]
    }}

    请确保分析全面准确，特别是技能和经验部分。
    """

    try:
        response = _get_client().messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text

        # 尝试解析JSON响应
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            # 如果JSON解析失败，使用正则提取关键信息
            return _extract_fallback_profile(resume_text)

    except Exception as e:
        print(f"Error extracting resume profile: {e}")
        return _extract_fallback_profile(resume_text)

def _extract_fallback_profile(resume_text: str) -> Dict[str, Any]:
    """
    使用正则表达式作为备用提取方法
    """
    profile = {
        "name": _extract_name(resume_text),
        "contact_info": {
            "email": _extract_email(resume_text),
            "phone": _extract_phone(resume_text),
            "location": _extract_field(resume_text, "地址|Location", 30)
        },
        "summary": _extract_field(resume_text, "个人总结|自我介绍|Summary", 100),
        "current_job": _extract_current_position(resume_text),
        "current_company": _extract_current_company(resume_text),
        "total_experience_years": _calculate_total_experience(resume_text),
        "education": _extract_education(resume_text),
        "work_experience": _extract_work_experience(resume_text),
        "skills": {
            "technical_skills": _extract_list_field(resume_text, "技能|Skills|技术能力"),
            "soft_skills": _extract_list_field(resume_text, "软技能|Soft Skills|个人素质"),
            "language_skills": [],
            "tools": _extract_list_field(resume_text, "工具|Tools|熟悉工具")
        },
        "certifications": [],
        "projects": [],
        "career_gaps": [],
        "job_hopping_frequency": "未知",
        "industries_worked": []
    }

    return profile

def _extract_name(text: str) -> str:
    """提取姓名"""
    # 查找可能的姓名位置（通常是开头）
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if len(line) < 20 and not re.search(r'\w+@\w+\.com|@\w+\.com', line):
            # 简单判断，不是邮箱或电话的可能是姓名
            if re.search(r'^[一-龥]{2,4}$', line) or re.match(r'^[A-Za-z\s]+$', line):
                return line
    return ""

def _extract_email(text: str) -> str:
    """提取邮箱"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def _extract_phone(text: str) -> str:
    """提取电话"""
    phone_patterns = [
        r'\b\d{3}[-.]?\d{4}[-.]?\d{4}\b',  # 11位手机号
        r'\b\d{3,4}[-.]?\d{4}[-.]?\d{4}\b',  # 座机
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""

def _extract_field(text: str, pattern: str, max_length: int = 50) -> str:
    """提取文本字段"""
    match = re.search(f"{pattern}[:：]?\\s*([^\\n]{{0,{max_length}}})", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def _extract_current_position(text: str) -> str:
    """提取当前职位"""
    # 查找工作经验中的最新职位
    experience_section = re.search(r'工作经验|Work Experience|职业经历', text, re.IGNORECASE)
    if experience_section:
        start_pos = experience_section.end()
        # 找到下一个部分
        next_section = re.search(r'\n\s*(教育背景|技能|项目经验|自我评价)', text[start_pos:], re.IGNORECASE)
        if next_section:
            experience_text = text[start_pos:start_pos + next_section.start()]
        else:
            experience_text = text[start_pos:]

        # 提取第一个职位
        first_job = re.search(r'^\s*([^\n]+)', experience_text)
        if first_job:
            return first_job.group(1).strip()
    return ""

def _extract_current_company(text: str) -> str:
    """提取当前公司"""
    # 简单实现：提取当前职位后的公司名
    return _extract_field(text, "公司|Company", 30)

def _calculate_total_experience(text: str) -> int:
    """计算总工作年限"""
    # 查找工作经验相关的时间描述
    experience_matches = re.findall(r'(\d{4})\s*年', text)
    if len(experience_matches) >= 2:
        try:
            years = [int(y) for y in experience_matches]
            return max(years) - min(years)
        except:
            pass
    return 0

def _extract_education(text: str) -> List[Dict]:
    """提取教育背景"""
    education = []
    education_section = re.search(r'教育背景|Education|学历', text, re.IGNORECASE)
    if education_section:
        start_pos = education_section.end()
        # 简单提取第一个学历
        degree_match = re.search(r'(\w+).*?(\w+).*?(\d{4})', text[start_pos:start_pos+200])
        if degree_match:
            education.append({
                "degree": degree_match.group(1),
                "school": degree_match.group(2),
                "major": "",
                "graduation_year": degree_match.group(3)
            })
    return education

def _extract_work_experience(text: str) -> List[Dict]:
    """提取工作经验"""
    experience = []
    # 简化实现
    experience_section = re.search(r'工作经验|Work Experience', text, re.IGNORECASE)
    if experience_section:
        experience.append({
            "position": _extract_current_position(text),
            "company": _extract_current_company(text),
            "duration": "",
            "responsibilities": [],
            "achievements": []
        })
    return experience

def _extract_list_field(text: str, pattern: str) -> List[str]:
    """提取列表字段"""
    lines = text.split('\n')
    result = []
    capture = False

    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            capture = True
            continue

        if capture:
            if line.strip() and not re.match(r'^[\s\d\.\-\(\)]+$', line):
                # 清理项目符号和数字前缀
                cleaned = re.sub(r'^[\s\*\-\•\d\.\)\(\:：]+', '', line.strip())
                if cleaned:
                    result.append(cleaned)
            elif re.search(r'教育|技能|证书|项目', line, re.IGNORECASE):
                break

    return result[:10]  # 限制最多10项