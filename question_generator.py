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
    prompt = f"""请基于以下信息，为该岗位生成针对性的面试问题。

岗位人才画像：
{json.dumps(talent_profile, ensure_ascii=False, indent=2)}

简历人才画像：
{json.dumps(resume_profile, ensure_ascii=False, indent=2)}

评估结果：
- 匹配度：{assessment['match_score']}%
- 风险等级：{assessment['risk_level']}
- 关键风险：{[r['category'] for r in assessment.get('risks', [])]}

请严格按以下JSON数组格式返回（不要添加任何其他文字，只返回JSON数组）：

[
    {{"question": "面试问题1", "purpose": "考察目的1", "category": "技术能力"}},
    {{"question": "面试问题2", "purpose": "考察目的2", "category": "行为面试"}},
    {{"question": "面试问题3", "purpose": "考察目的3", "category": "情景测试"}},
    {{"question": "面试问题4", "purpose": "考察目的4", "category": "经验深挖"}},
    {{"question": "面试问题5", "purpose": "考察目的5", "category": "文化匹配"}},
    {{"question": "面试问题6", "purpose": "考察目的6", "category": "风险验证"}}
]

每个类别生成2-3个问题，共12-18个问题。确保问题针对性强、有深度。"""

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

    for skill in talent_profile.get("required_skills", [])[:3]:
        questions.append({
            "question": f"请详细介绍您在{skill}方面的经验和项目案例。",
            "purpose": f"考察{skill}实际应用能力",
            "category": "技术能力"
        })

    for resp in talent_profile.get("responsibilities", [])[:2]:
        questions.append({
            "question": f"请分享一个您在{resp}方面的成功经历，遇到了什么挑战？如何解决的？",
            "purpose": "考察问题解决能力和实战经验",
            "category": "行为面试"
        })

    questions.append({
        "question": "如果您同时面临多个紧急任务，您会如何安排优先级？",
        "purpose": "考察时间管理和压力处理能力",
        "category": "情景测试"
    })

    questions.append({
        "question": "您在当前/上一份工作中最重要的成就是什么？请具体说明。",
        "purpose": "深入了解实际工作能力和成就",
        "category": "经验深挖"
    })

    questions.append({
        "question": "请描述一个您与团队成员产生分歧并最终达成共识的例子。",
        "purpose": "考察沟通能力和团队协作精神",
        "category": "文化匹配"
    })

    for risk in assessment.get("risks", [])[:2]:
        questions.append({
            "question": f"关于{risk['category']}，您有什么想补充说明的？",
            "purpose": f"验证风险点: {risk['description']}",
            "category": "风险验证"
        })

    return questions
