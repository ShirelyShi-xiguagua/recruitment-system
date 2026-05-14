import json
import os
import streamlit as st
from anthropic import Anthropic
from typing import Dict, List, Any, Tuple

MODEL = "claude-sonnet-4-20250514"


def _get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    return Anthropic(api_key=api_key)


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                lines = lines[:i]
                break
        text = "\n".join(lines)
    return json.loads(text)


def assess_match_and_risks(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""请基于以下两个人才画像，评估简历与岗位的匹配度和风险。

岗位人才画像：
{json.dumps(talent_profile, ensure_ascii=False, indent=2)}

简历人才画像：
{json.dumps(resume_profile, ensure_ascii=False, indent=2)}

请严格按以下JSON格式返回（不要添加任何其他文字，只返回JSON）：

{{
    "match_score": 75,
    "match_trend": "稳定",
    "match_details": [
        {{"dimension": "技能匹配", "score": 85, "comment": "具体评价"}},
        {{"dimension": "经验匹配", "score": 70, "comment": "具体评价"}},
        {{"dimension": "教育背景", "score": 80, "comment": "具体评价"}},
        {{"dimension": "软技能匹配", "score": 75, "comment": "具体评价"}}
    ],
    "risk_level": "低",
    "risks": [
        {{"category": "风险类别", "description": "风险描述", "severity": "高"}}
    ],
    "strengths": ["优势1", "优势2"],
    "recommendation": "推荐/谨慎考虑/不推荐",
    "key_concerns": ["关注点1"],
    "suggestions": ["建议1"]
}}"""

    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return _parse_json_response(response.content[0].text)
    except json.JSONDecodeError:
        return _calculate_match_score(talent_profile, resume_profile)
    except Exception as e:
        st.warning(f"AI评估失败，使用本地评估: {e}")
        return _calculate_match_score(talent_profile, resume_profile)


def _calculate_match_score(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    score_details = []
    total_score = 0
    max_score = 0

    skill_score, skill_comment = _assess_skill_match(talent_profile, resume_profile)
    score_details.append({"dimension": "技能匹配", "score": skill_score, "comment": skill_comment})
    total_score += skill_score * 0.4
    max_score += 40

    exp_score, exp_comment = _assess_experience_match(talent_profile, resume_profile)
    score_details.append({"dimension": "经验匹配", "score": exp_score, "comment": exp_comment})
    total_score += exp_score * 0.3
    max_score += 30

    edu_score, edu_comment = _assess_education_match(talent_profile, resume_profile)
    score_details.append({"dimension": "教育背景", "score": edu_score, "comment": edu_comment})
    total_score += edu_score * 0.15
    max_score += 15

    soft_score, soft_comment = _assess_soft_skill_match(talent_profile, resume_profile)
    score_details.append({"dimension": "软技能匹配", "score": soft_score, "comment": soft_comment})
    total_score += soft_score * 0.15
    max_score += 15

    final_score = min(100, int((total_score / max_score) * 100) if max_score > 0 else 0)
    risk_level = "低" if final_score >= 80 else "中" if final_score >= 60 else "高"
    risks = _identify_risks(talent_profile, resume_profile, score_details)
    strengths = [d["comment"] for d in score_details if d["score"] >= 80]

    return {
        "match_score": final_score,
        "match_trend": "稳定",
        "match_details": score_details,
        "risk_level": risk_level,
        "risks": risks,
        "strengths": strengths if strengths else ["暂未发现突出优势"],
        "recommendation": "推荐" if final_score >= 70 else "谨慎考虑" if final_score >= 50 else "不推荐",
        "key_concerns": [d["dimension"] for d in score_details if d["score"] < 70],
        "suggestions": []
    }


def _assess_skill_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    required = set(s.lower() for s in talent.get("required_skills", []))
    have = set(s.lower() for s in resume.get("skills", {}).get("technical_skills", []))
    if not required:
        return 80, "岗位无明确技能要求"
    matched = len(required & have)
    score = int((matched / len(required)) * 100)
    return score, f"匹配 {matched}/{len(required)} 项核心技能"


def _assess_experience_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    req = talent.get("experience_years", 0)
    have = resume.get("total_experience_years", 0)
    if req == 0:
        return 80, "岗位无明确经验要求"
    if have >= req:
        return min(100, 80 + (have - req) * 5), f"经验充足({have}年 >= {req}年)"
    return max(30, int((have / req) * 80)), f"经验不足({have}年 < {req}年)"


def _assess_education_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    req = talent.get("education", "")
    edu_list = resume.get("education", [])
    if not req:
        return 80, "岗位无明确学历要求"
    for edu in edu_list:
        if req in str(edu.get("degree", "")):
            return 90, "学历符合要求"
    return 60, "学历与要求有差距"


def _assess_soft_skill_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    required = set(talent.get("soft_skills", []))
    have = set(resume.get("skills", {}).get("soft_skills", []))
    if not required:
        return 80, "岗位无明确软技能要求"
    matched = len(required & have)
    score = int((matched / len(required)) * 100) if required else 0
    return score, f"软技能匹配 {matched}/{len(required)} 项"


def _identify_risks(talent: Dict, resume: Dict, details: List[Dict]) -> List[Dict]:
    risks = []
    for d in details:
        if d["score"] < 70:
            risks.append({
                "category": d["dimension"],
                "description": d["comment"],
                "severity": "高" if d["score"] < 50 else "中"
            })
    if resume.get("job_hopping_frequency") == "高":
        risks.append({"category": "职业稳定性", "description": "跳槽频率较高", "severity": "中"})
    if resume.get("career_gaps"):
        risks.append({"category": "职业空窗", "description": "存在职业空窗期", "severity": "低"})
    return risks
