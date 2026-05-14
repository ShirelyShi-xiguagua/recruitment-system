import json
import os
import streamlit as st
from anthropic import Anthropic
from typing import Dict, List, Any, Tuple

def _get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    return Anthropic(api_key=api_key)

def assess_match_and_risks(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    评估简历与岗位的匹配度和风险

    Args:
        talent_profile: 岗位人才画像
        resume_profile: 简历人才画像

    Returns:
        评估结果，包含匹配度、风险和优势
    """

    prompt = f"""
    请基于以下两个人才画像，评估简历与岗位的匹配度和风险：

    岗位人才画像：
    {json.dumps(talent_profile, ensure_ascii=False, indent=2)}

    简历人才画像：
    {json.dumps(resume_profile, ensure_ascii=False, indent=2)}

    请提供JSON格式的评估结果，包含以下内容：

    {{
        "match_score": 匹配度百分比(0-100),
        "match_trend": "上升/下降/稳定",
        "match_details": [
            {{
                "dimension": "技能匹配",
                "score": 85,
                "comment": "候选人具备岗位所需的核心技能"
            }},
            {{
                "dimension": "经验匹配",
                "score": 70,
                "comment": "相关经验符合要求，但某些领域经验不足"
            }}
        ],
        "risk_level": "低/中/高",
        "risks": [
            {{
                "category": "技能差距",
                "description": "候选人缺乏某些关键技术",
                "severity": "高/中/低"
            }}
        ],
        "strengths": [
            "候选人的优势1",
            "候��人的优势2"
        ],
        "recommendation": "建议/不推荐/谨慎考虑",
        "key_concerns": ["关注点1", "关注点2"],
        "suggestions": ["建议1", "建议2"]
    }}

    请确保评估客观、全面，并提供具体的改进建议。
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
            # 如果JSON解析失败，使用计算方法
            return _calculate_match_score(talent_profile, resume_profile)

    except Exception as e:
        print(f"Error in assessing match and risks: {e}")
        return _calculate_match_score(talent_profile, resume_profile)

def _calculate_match_score(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用启发式方法计算匹配度
    """
    score_details = []
    total_score = 0
    max_score = 0

    # 技能匹配评分 (40%)
    skill_score, skill_comment = _assess_skill_match(talent_profile, resume_profile)
    score_details.append({
        "dimension": "技能匹配",
        "score": skill_score,
        "comment": skill_comment
    })
    total_score += skill_score * 0.4
    max_score += 40

    # 经验匹配评分 (30%)
    exp_score, exp_comment = _assess_experience_match(talent_profile, resume_profile)
    score_details.append({
        "dimension": "经验匹配",
        "score": exp_score,
        "comment": exp_comment
    })
    total_score += exp_score * 0.3
    max_score += 30

    # 教育背景评分 (15%)
    edu_score, edu_comment = _assess_education_match(talent_profile, resume_profile)
    score_details.append({
        "dimension": "教育背景",
        "score": edu_score,
        "comment": edu_comment
    })
    total_score += edu_score * 0.15
    max_score += 15

    # 软技能评分 (15%)
    soft_score, soft_comment = _assess_soft_skill_match(talent_profile, resume_profile)
    score_details.append({
        "dimension": "软技能匹配",
        "score": soft_score,
        "comment": soft_comment
    })
    total_score += soft_score * 0.15
    max_score += 15

    final_score = min(100, int((total_score / max_score) * 100) if max_score > 0 else 0)

    # 确定风险等级
    risk_level = _determine_risk_level(final_score, score_details)

    # 识别风险
    risks = _identify_risks(talent_profile, resume_profile, score_details)

    # 提取优势
    strengths = _identify_strengths(score_details)

    return {
        "match_score": final_score,
        "match_trend": "稳定",
        "match_details": score_details,
        "risk_level": risk_level,
        "risks": risks,
        "strengths": strengths,
        "recommendation": _get_recommendation(final_score, risk_level),
        "key_concerns": _get_key_concerns(score_details),
        "suggestions": _get_suggestions(talent_profile, resume_profile)
    }

def _assess_skill_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    """评估技能匹配度"""
    required_skills = set(talent.get('required_skills', []))
    resume_skills = set(resume.get('skills', {}).get('technical_skills', []))

    if not required_skills:
        return 80, "岗位无明确技能要求"

    matched = len(required_skills & resume_skills)
    match_ratio = matched / len(required_skills) if required_skills else 0

    score = int(match_ratio * 100)

    if score >= 80:
        comment = f"候选人掌握{matched}/{len(required_skills)}项核心技能"
    elif score >= 60:
        comment = f"候选人掌握部分核心技能，需补充{len(required_skills)-matched}项技能"
    else:
        comment = f"候选人核心技能不足，需重点培养{len(required_skills)-matched}项技能"

    return score, comment

def _assess_experience_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    """评估经验匹配度"""
    required_years = talent.get('experience_years', 0)
    resume_years = resume.get('total_experience_years', 0)

    if required_years == 0:
        return 80, "岗位无明确经验要求"

    # 计算经验匹配比例
    if resume_years >= required_years:
        score = min(100, 80 + (resume_years - required_years) * 5)
        comment = f"候选人经验丰富，超出要求{resume_years - required_years}年"
    else:
        score = max(30, int((resume_years / required_years) * 80))
        gap = required_years - resume_years
        comment = f"候选人经验不足，尚需{gap}年相关经验"

    return score, comment

def _assess_education_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    """评估教育背景匹配度"""
    required_edu = talent.get('education', '')
    resume_edu = resume.get('education', [])

    if not required_edu:
        return 80, "岗位无明确学历要求"

    # 简化教育匹配判断
    has_match = False
    for edu in resume_edu:
        if required_edu in edu.get('degree', ''):
            has_match = True
            break

    if has_match:
        return 90, "候选人学历符合要求"
    else:
        return 60, "候选人学历与要求有差距"

def _assess_soft_skill_match(talent: Dict, resume: Dict) -> Tuple[int, str]:
    """评估软技能匹配度"""
    required_soft = set(talent.get('soft_skills', []))
    resume_soft = set(resume.get('skills', {}).get('soft_skills', []))

    if not required_soft:
        return 80, "岗位无明确软技能要求"

    matched = len(required_soft & resume_soft)
    match_ratio = matched / len(required_soft) if required_soft else 0

    score = int(match_ratio * 100)

    if score >= 70:
        comment = f"候选人具备大部分软技能要求"
    else:
        comment = f"候选人软技能匹配度较低，需重点培养"

    return score, comment

def _determine_risk_level(match_score: int, score_details: List[Dict]) -> str:
    """确定风险等级"""
    if match_score >= 80:
        return "低"
    elif match_score >= 60:
        return "中"
    else:
        return "高"

def _identify_risks(talent: Dict, resume: Dict, score_details: List[Dict]) -> List[Dict]:
    """识别风险"""
    risks = []

    # 检查技能差距
    skill_score = next((d['score'] for d in score_details if d['dimension'] == '技能匹配'), 100)
    if skill_score < 70:
        risks.append({
            "category": "技能差距",
            "description": "候选人缺乏岗位所需的关键技能",
            "severity": "高" if skill_score < 50 else "中"
        })

    # 检查经验差距
    exp_score = next((d['score'] for d in score_details if d['dimension'] == '经验匹配'), 100)
    if exp_score < 70:
        risks.append({
            "category": "经验不足",
            "description": "候选人相关经验不符合岗位要求",
            "severity": "高" if exp_score < 50 else "中"
        })

    # 检查稳定性
    if resume.get('job_hopping_frequency') == '高':
        risks.append({
            "category": "职业稳定性",
            "description": "候选人跳槽频率较高，可能影响团队稳定性",
            "severity": "中"
        })

    # 检查教育背景
    edu_score = next((d['score'] for d in score_details if d['dimension'] == '教育背景'), 100)
    if edu_score < 70:
        risks.append({
            "category": "教育背景",
            "description": "候选人学历与岗位要求有差距",
            "severity": "低"
        })

    return risks

def _identify_strengths(score_details: List[Dict]) -> List[str]:
    """识别优势"""
    strengths = []

    for detail in score_details:
        if detail['score'] >= 80:
            if detail['dimension'] == '技能匹配':
                strengths.append("技能匹配度高，具备核心能力")
            elif detail['dimension'] == '经验匹配':
                strengths.append("经验丰富，符合岗位要求")
            elif detail['dimension'] == '教育背景':
                strengths.append("学历背景优秀")
            elif detail['dimension'] == '软技能匹配':
                strengths.append("软技能突出，适合团队协作")

    return strengths

def _get_recommendation(match_score: int, risk_level: str) -> str:
    """获取推荐意见"""
    if match_score >= 80 and risk_level == "低":
        return "强烈推荐"
    elif match_score >= 70 and risk_level in ["低", "中"]:
        return "推荐"
    elif match_score >= 60:
        return "谨慎考虑"
    else:
        return "不推荐"

def _get_key_concerns(score_details: List[Dict]) -> List[str]:
    """获取关键关注点"""
    concerns = []
    for detail in score_details:
        if detail['score'] < 70:
            concerns.append(f"{detail['dimension']}需要重点关注")
    return concerns

def _get_suggestions(talent: Dict, resume: Dict) -> List[str]:
    """获取建议"""
    suggestions = []

    # 技能提升建议
    required_skills = set(talent.get('required_skills', []))
    resume_skills = set(resume.get('skills', {}).get('technical_skills', []))
    missing_skills = required_skills - resume_skills
    if missing_skills:
        suggestions.append(f"建议补充技能: {', '.join(list(missing_skills)[:3])}")

    # 学习建议
    if talent.get('education') and not resume.get('education'):
        suggestions.append("建议提供详细的学历背景信息")

    # 经验积累建议
    if resume.get('total_experience_years', 0) < talent.get('experience_years', 0):
        suggestions.append("建议积累更多相关项目经验")

    return suggestions