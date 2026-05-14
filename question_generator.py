import json
import os
import streamlit as st
from anthropic import Anthropic
from typing import Dict, List, Any

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


def generate_interview_questions(
    talent_profile: Dict[str, Any],
    resume_profile: Dict[str, Any],
    assessment: Dict[str, Any]
) -> List[Dict[str, str]]:
    prompt = f"""你是一位资深的互联网招聘面试官。请基于以下信息，生成高质量的面试问题。

核心原则：
1. 所有问题必须聚焦于"工作经历的真实性验证"和"岗位能力匹配度考察"
2. 不要出任何关于学历验证、专业验证、证书核实的问题
3. 针对简历中发现的风险点（如跳槽频繁、经验空窗、技能不匹配等）设计深挖问题
4. 通过STAR法则（情境-任务-行动-结果）验证候选人经历的真实性
5. 问题要具体、有细节，不要泛泛而谈

岗位人才画像：
{json.dumps(talent_profile, ensure_ascii=False, indent=2)}

简历人才画像：
{json.dumps(resume_profile, ensure_ascii=False, indent=2)}

评估结果：
- 匹配度：{assessment['match_score']}%
- 风险等级：{assessment['risk_level']}
- 关键风险：{json.dumps([r for r in assessment.get('risks', [])], ensure_ascii=False)}

请严格按以下JSON数组格式返回（不要添加任何其他文字，只返回JSON数组）：

[
    {{"question": "面试问题", "purpose": "考察目的", "category": "经历真实性验证"}},
    {{"question": "面试问题", "purpose": "考察目的", "category": "核心能力考察"}},
    {{"question": "面试问题", "purpose": "考察目的", "category": "风险点深挖"}},
    {{"question": "面试问题", "purpose": "考察目的", "category": "岗位匹配验证"}},
    {{"question": "面试问题", "purpose": "考察目的", "category": "压力/情景测试"}}
]

问题分布要求：
- 经历真实性验证：3-4个（针对简历中关键项目和岗位经历，追问细节）
- 核心能力考察：3-4个（针对岗位要求的核心技能，设计实操性问题）
- 风险点深挖：2-3个（针对评估发现的每个风险，设计验证问题）
- 岗位匹配验证：2-3个（考察候选人对目标岗位的理解和胜任力）
- 压力/情景测试：2个（模拟实际工作场景，考察应变能力）

共生成12-16个问题。"""

    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        result = _parse_json_response(response.content[0].text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            flat = []
            for qs in result.values():
                if isinstance(qs, list):
                    flat.extend(qs)
            return flat
        return _generate_fallback_questions(talent_profile, resume_profile, assessment)
    except json.JSONDecodeError:
        return _generate_fallback_questions(talent_profile, resume_profile, assessment)
    except Exception as e:
        st.warning(f"AI问题生成失败，使用默认问题: {e}")
        return _generate_fallback_questions(talent_profile, resume_profile, assessment)


def _generate_fallback_questions(
    talent_profile: Dict[str, Any],
    resume_profile: Dict[str, Any],
    assessment: Dict[str, Any]
) -> List[Dict[str, str]]:
    questions = []

    # 经历真实性验证
    work_exp = resume_profile.get("work_experience", [])
    if work_exp:
        latest = work_exp[0]
        company = latest.get("company", "上一家公司")
        position = latest.get("position", "上一个岗位")
        questions.append({
            "question": f"请详细描述您在{company}担任{position}期间，负责的最核心的一个项目，包括项目背景、您的具体角色、遇到的最大困难及解决方案。",
            "purpose": "通过细节追问验证工作经历真实性",
            "category": "经历真实性验证"
        })
    questions.append({
        "question": "您离开上一家公司的真正原因是什么？当时有没有其他选择？",
        "purpose": "验证离职动机的真实性，评估稳定性",
        "category": "经历真实性验证"
    })
    questions.append({
        "question": "在您过去的工作中，有没有一次项目失败的经历？请具体说说发生了什么，您从中学到了什么。",
        "purpose": "通过失败案例验证经历真实性（编造经历者通常回避失败）",
        "category": "经历真实性验证"
    })

    # 核心能力考察
    for skill in talent_profile.get("required_skills", [])[:3]:
        questions.append({
            "question": f"请举一个您实际使用{skill}解决复杂问题的案例，描述当时的具体情境和您的做法。",
            "purpose": f"验证{skill}的实际掌握深度",
            "category": "核心能力考察"
        })

    # 风险点深挖
    for risk in assessment.get("risks", [])[:3]:
        if "稳定" in risk.get("category", "") or "跳槽" in risk.get("description", ""):
            questions.append({
                "question": "您过去几次换工作的节奏比较快，能否逐一说明每次离开的原因？您理想的工作周期是多久？",
                "purpose": f"深挖风险: {risk['description']}",
                "category": "风险点深挖"
            })
        elif "技能" in risk.get("category", "") or "不足" in risk.get("description", ""):
            questions.append({
                "question": f"这个岗位需要的部分技能您目前经验较少，您打算如何快速补齐？能否举例说明您过去快速学习新技能的经历？",
                "purpose": f"深挖风险: {risk['description']}",
                "category": "风险点深挖"
            })
        else:
            questions.append({
                "question": f"关于{risk['category']}方面，能否详细说明您的实际情况？",
                "purpose": f"深挖风险: {risk['description']}",
                "category": "风险点深挖"
            })

    # 岗位匹配验证
    questions.append({
        "question": "您对这个岗位的理解是什么？您认为自己最大的优势和最大的短板分别是什么？",
        "purpose": "评估候选人对岗位的认知和自我认知准确度",
        "category": "岗位匹配验证"
    })

    # 压力/情景测试
    questions.append({
        "question": "假设您刚入职一个月，负责的项目出现了严重的线上问题，而您的直属领导正好不在，您会如何处理？",
        "purpose": "考察应变能力和独立解决问题的能力",
        "category": "压力/情景测试"
    })

    return questions
