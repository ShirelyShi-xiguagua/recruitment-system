import json
import os
import streamlit as st
from anthropic import Anthropic
from typing import Dict, List, Any

def _get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    return Anthropic(api_key=api_key)

def generate_interview_questions(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any], assessment: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    基于人才画像和评估结果生成面试问题

    Args:
        talent_profile: 岗位人才画像
        resume_profile: 简历人才画像
        assessment: 评估结果

    Returns:
        面试问题列表
    """

    prompt = f"""
    请基于以下信息，为该岗位生成针对性的面试问题：

    岗位人才画像：
    {json.dumps(talent_profile, ensure_ascii=False, indent=2)}

    简历人才画像：
    {json.dumps(resume_profile, ensure_ascii=False, indent=2)}

    评估结果：
    - 匹配度：{assessment['match_score']}%
    - 风险等级：{assessment['risk_level']}
    - 关键风险：{[r['category'] for r in assessment['risks']]}

    请生成JSON格式的面试问题，包含以下类别：

    {{
        "technical_questions": [
            {{
                "question": "技术问题1",
                "purpose": "考察候选人���技术能力",
                "category": "技术能力"
            }}
        ],
        "behavioral_questions": [
            {{
                "question": "行为问题1",
                "purpose": "考察候选人的团队协作能力",
                "category": "行为面试"
            }}
        ],
        "scenario_questions": [
            {{
                "question": "情景问题1",
                "purpose": "考察候选人的问题解决能力",
                "category": "情景测试"
            }}
        ],
        "experience_questions": [
            {{
                "question": "经验问题1",
                "purpose": "深入了解候选人的项目经验",
                "category": "经验深挖"
            }}
        ],
        "culture_fit_questions": [
            {{
                "question": "文化匹配问题1",
                "purpose": "考察候选人与公司文化的契合度",
                "category": "文化匹配"
            }}
        ],
        "risk_verification_questions": [
            {{
                "question": "风险验证问题1",
                "purpose": "验证评估中发现的风险点",
                "category": "风险验证"
            }}
        ]
    }}

    每个类别生成3-5个问题，确保问题针对性强、有深度。
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
            # 如果JSON解析失败，使用生成方法
            return _generate_fallback_questions(talent_profile, resume_profile, assessment)

    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return _generate_fallback_questions(talent_profile, resume_profile, assessment)

def _generate_fallback_questions(talent_profile: Dict[str, Any], resume_profile: Dict[str, Any], assessment: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    生成备用面试问题
    """
    questions = []

    # 技术问题
    required_skills = talent_profile.get('required_skills', [])
    if required_skills:
        for i, skill in enumerate(required_skills[:3]):
            questions.append({
                "question": f"请详细介绍您在{skill}方面的经验和项目案例。",
                "purpose": f"考察候选人的{skill}实际应用能力",
                "category": "技术能力"
            })

    # 行为问题
    responsibilities = talent_profile.get('responsibilities', [])
    if responsibilities:
        for i, resp in enumerate(responsibilities[:2]):
            questions.append({
                "question": f"请分享一个您在{resp}方面的成功经历，遇到了什么挑战？如何解决的？",
                "purpose": "考察候选人的问题解决能力和团队合作",
                "category": "行为面试"
            })

    # 经验深挖问题
    current_job = resume_profile.get('current_job', '')
    if current_job:
        questions.append({
            "question": f"您在当前工作中最重要的成就是什么？请具体说明。",
            "purpose": "深入了解候选人的实际工作能力和成就",
            "category": "经��深挖"
        })

    # 风险验证问题
    for risk in assessment.get('risks', [])[:2]:
        if risk['category'] == '技能差距':
            questions.append({
                "question": "面对不熟悉的技术，您通常如何快速学习和掌握？",
                "purpose": "评估候选人的学习能力和适应性",
                "category": "风险验证"
            })

    # 文化匹配问题
    soft_skills = talent_profile.get('soft_skills', [])
    if soft_skills:
        questions.append({
            "question": "请描述一个您与团队成员产生分歧并最终达成共识的例子。",
            "purpose": "考察候选人的沟通能力和团队协作精神",
            "category": "文化匹配"
        })

    # 情景测试问题
    questions.append({
        "question": "如果您同时面临多个紧急任务，您会如何安排优先级并确保完成？",
        "purpose": "考察候选人的时间管理和压力处理能力",
        "category": "情景测试"
    })

    # 按类别分组
    categorized_questions = {
        "technical_questions": [],
        "behavioral_questions": [],
        "scenario_questions": [],
        "experience_questions": [],
        "culture_fit_questions": [],
        "risk_verification_questions": []
    }

    for q in questions:
        if q['category'] in ['技术能力']:
            categorized_questions["technical_questions"].append(q)
        elif q['category'] in ['行为面试']:
            categorized_questions["behavioral_questions"].append(q)
        elif q['category'] in ['情景测试']:
            categorized_questions["scenario_questions"].append(q)
        elif q['category'] in ['经验深挖']:
            categorized_questions["experience_questions"].append(q)
        elif q['category'] in ['文化匹配']:
            categorized_questions["culture_fit_questions"].append(q)
        elif q['category'] in ['风险验证']:
            categorized_questions["risk_verification_questions"].append(q)

    # 转换为列表格式
    result = []
    for category, qs in categorized_questions.items():
        for q in qs:
            result.append(q)

    return result

def generate_follow_up_questions(answers: List[str], question_type: str) -> List[str]:
    """
    根据候选人回答生成追问问题
    """
    follow_ups = []

    if question_type == "technical":
        follow_ups = [
            "能具体解释一下您使用的技术栈吗？",
            "这个项目中您遇到的最大技术挑战是什么？",
            "您如何确保代码的质量和可维护性？"
        ]
    elif question_type == "behavioral":
        follow_ups = [
            "能详细描述一下当时的情况吗？",
            "您在这个过程中扮演了什么角色？",
            "如果重来一次，您会做不同的选择吗？"
        ]
    elif question_type == "experience":
        follow_ups = [
            "这个项目的具体背景是什么？",
            "您最大的收获是什么？",
            "您从中学到了什么经验？"
        ]

    return follow_ups