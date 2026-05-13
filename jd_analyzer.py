import re
import json
import os
from anthropic import Anthropic
from typing import Dict, List, Any

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "your-api-key-here"))

def extract_talent_profile(jd_text: str) -> Dict[str, Any]:
    """
    从JD文本中提取岗位人才画像

    Args:
        jd_text: 职位描述文本

    Returns:
        人才画像字典，包含技能、经验、教育、软性要求等
    """

    prompt = f"""
    请从以下职位描述中提取详细的人才画像，并以JSON格式返回：

    {jd_text}

    请按以下结构分析：

    {{
        "job_title": "职位名称",
        "required_skills": ["技能1", "技能2", ...],
        "preferred_skills": ["技能1", "技能2", ...],
        "experience_level": "经验要求",
        "experience_years": 年数,
        "education": "教育要求",
        "responsibilities": ["职责1", "职责2", ...],
        "qualifications": ["资格1", "资格2", ...],
        "soft_skills": ["软技能1", "软技能2", ...],
        "industry_knowledge": ["行业知识1", "行业知识2", ...],
        "tools_technologies": ["工具/技术1", "工具/技术2", ...],
        "language_requirements": ["语言要求1", "语言要求2", ...],
        "salary_range": "薪资范围（如有）",
        "job_type": "工作类型",
        "location": "工作地点"
    }}

    请确保分析全面准确，特别是关键的技能和要求。
    """

    try:
        response = client.messages.create(
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
            return _extract_fallback_profile(jd_text)

    except Exception as e:
        print(f"Error extracting talent profile: {e}")
        return _extract_fallback_profile(jd_text)

def _extract_fallback_profile(jd_text: str) -> Dict[str, Any]:
    """
    使用正则表达式作为备用提取方法
    """
    profile = {
        "job_title": _extract_field(jd_text, "职位名称|岗位名称|Position", 20),
        "required_skills": _extract_list_field(jd_text, "技能要求|Skills|技术能力"),
        "preferred_skills": [],
        "experience_level": _extract_field(jd_text, "经验要求|Experience", 30),
        "experience_years": _extract_years(jd_text),
        "education": _extract_field(jd_text, "教育要求|Education", 30),
        "responsibilities": _extract_list_field(jd_text, "岗位职责|Responsibilities|工作职责"),
        "qualifications": _extract_list_field(jd_text, "任职要求|Qualifications|要求"),
        "soft_skills": _extract_list_field(jd_text, "软技能|Soft Skills|个人素质"),
        "industry_knowledge": [],
        "tools_technologies": _extract_list_field(jd_text, "工具|Tools|技术栈"),
        "language_requirements": [],
        "salary_range": "",
        "job_type": "",
        "location": ""
    }

    return profile

def _extract_field(text: str, pattern: str, max_length: int = 50) -> str:
    """提取文本字段"""
    match = re.search(f"{pattern}[:：]?\\s*([^\\n]{{0,{max_length}}})", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def _extract_years(text: str) -> int:
    """提取工作经验年数"""
    patterns = [
        r"(\d+)\s*年",
        r"(\d+)\s*yrs?",
        r"(\d+)\s*years?"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0

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
            elif re.search(r'技能|要求|职责|资格|素质|工具', line, re.IGNORECASE):
                break

    return result[:10]  # 限制最多10项