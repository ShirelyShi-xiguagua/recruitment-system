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


def _build_project_context(resume_profile: Dict) -> str:
    projects = resume_profile.get("projects", [])
    work_exp = resume_profile.get("work_experience", [])
    lines = []
    for i, exp in enumerate(work_exp[:3]):
        company = exp.get("company", "未知公司")
        position = exp.get("position", "未知职位")
        duration = exp.get("duration", "")
        achievements = exp.get("achievements", [])
        responsibilities = exp.get("responsibilities", [])
        lines.append(f"经历{i+1}: {company} - {position} ({duration})")
        if responsibilities:
            lines.append(f"  职责: {'; '.join(responsibilities[:3])}")
        if achievements:
            lines.append(f"  成就: {'; '.join(achievements[:3])}")
    for i, proj in enumerate(projects[:3]):
        name = proj.get("name", "未知项目")
        desc = proj.get("description", "")
        techs = proj.get("technologies", [])
        lines.append(f"项目{i+1}: {name}")
        if desc:
            lines.append(f"  描述: {desc}")
        if techs:
            lines.append(f"  技术栈: {', '.join(techs)}")
    return "\n".join(lines) if lines else "简历中未提供详细项目经历"


def _find_skill_gaps(talent_profile: Dict, resume_profile: Dict) -> List[str]:
    required = set(s.lower() for s in talent_profile.get("required_skills", []))
    have = set(s.lower() for s in resume_profile.get("skills", {}).get("technical_skills", []))
    tools_required = set(s.lower() for s in talent_profile.get("tools_technologies", []))
    tools_have = set(s.lower() for s in resume_profile.get("skills", {}).get("tools", []))
    missing = (required | tools_required) - (have | tools_have)
    return list(missing)[:5]


def generate_interview_questions(
    talent_profile: Dict[str, Any],
    resume_profile: Dict[str, Any],
    assessment: Dict[str, Any]
) -> List[Dict[str, str]]:
    project_context = _build_project_context(resume_profile)
    skill_gaps = _find_skill_gaps(talent_profile, resume_profile)

    prompt = f"""你是一位有15年经验的互联网行业面试官，擅长通过细节追问甄别候选人的真实能力。

## 你的任务
根据以下信息，为面试官生成一套高质量、针对性极强的面试题。

## 绝对禁止
- 不要出任何关于学历、专业、证书验证的问题
- 不要出"请介绍一下您自己"这种泛泛的问题
- 不要出与具体岗位和简历无关的通用问题

## 出题要求
每道题必须做到以下至少一点：
1. 引用简历中的**具体项目名称/公司名称/技术栈**进行追问
2. 围绕岗位JD要求的**具体技能**，设计实操场景题
3. 针对简历中**未提及但岗位要求的技能**（技能盲区），设计论证题
4. 针对**风险点**设计深挖题

---

## 岗位信息
职位: {talent_profile.get('job_title', '未知')}
核心技能要求: {', '.join(talent_profile.get('required_skills', []))}
岗位职责: {'; '.join(talent_profile.get('responsibilities', [])[:5])}

## 候选人项目经历（重点深挖对象）
{project_context}

## 候选人技能盲区（简历未体现但岗位要求的技能）
{', '.join(skill_gaps) if skill_gaps else '暂无明显盲区'}

## 风险评估
匹配度: {assessment['match_score']}%
风险等级: {assessment['risk_level']}
具体风险:
{json.dumps(assessment.get('risks', []), ensure_ascii=False, indent=2)}

---

请严格按以下JSON数组格式返回（不要添加任何其他文字）：

[
    {{
        "question": "具体的面试问题（必须引用简历中的项目/公司/技术细节）",
        "purpose": "这道题考察什么、为什么要问这道题",
        "category": "项目经历深挖",
        "follow_up": "如果候选人回答得好，进一步追问什么"
    }}
]

## 出题分布（共15题左右）

**项目经历深挖（4-5题）**：
- 必须点名简历中的具体项目/公司，追问：你在项目中具体负责哪个模块？团队几个人？你做了哪些关键决策？遇到过什么技术瓶颈？最终数据效果如何？
- 交叉验证：同一经历从不同角度问（技术选型、团队协作、业务指标）

**岗位技能实操（3-4题）**：
- 基于岗位JD的核心技能，设计具体的实操场景题
- 例如JD要求"高并发系统设计"，就问"如果让你设计一个日活100万的系统，你会怎么做"

**技能盲区论证（2-3题）**：
- 针对候选人简历中未提及、但岗位明确要求的技能
- 不是问"你会不会"，而是设计一个使用该技能的场景，看候选人的思路
- 例如简历没提Kafka但岗位要求，就问"如果系统需要处理每秒10万条消息，你会如何设计消息队列方案"

**风险点验证（3-4题）**：
- 针对每个具体风险点设计深挖问题
- 跳槽频繁→逐一追问每次离职原因
- 经验空窗→问空窗期在做什么
- 技能不匹配→用场景题验证实际水平

**压力/情景题（2题）**：
- 模拟目标岗位的真实工作场景
- 考察候选人的实际应变能力和工作方法"""

    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=4000,
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
    work_exp = resume_profile.get("work_experience", [])
    projects = resume_profile.get("projects", [])
    skill_gaps = _find_skill_gaps(talent_profile, resume_profile)

    # 项目经历深挖
    if work_exp:
        exp = work_exp[0]
        company = exp.get("company", "上一家公司")
        position = exp.get("position", "上一个岗位")
        resps = exp.get("responsibilities", [])
        questions.append({
            "question": f"您在{company}担任{position}期间，{resps[0] if resps else '主要工作'}的具体流程是什么？团队有多少人？您个人负责哪个环节？请用数据说明您的工作成果。",
            "purpose": f"深挖{company}工作经历的真实性和贡献度",
            "category": "项目经历深挖",
            "follow_up": "这个项目的技术架构是怎样的？为什么选择这个方案？"
        })
    if len(work_exp) > 1:
        exp2 = work_exp[1]
        questions.append({
            "question": f"您从{exp2.get('company', '前公司')}到{work_exp[0].get('company', '当前公司')}，工作内容有什么本质变化？您觉得哪段经历对您成长帮助最大？为什么？",
            "purpose": "交叉验证多段经历的一致性和成长逻辑",
            "category": "项目经历深挖",
            "follow_up": "两家公司的工作方法有什么不同？您更适应哪种？"
        })
    if projects:
        proj = projects[0]
        techs = proj.get("technologies", [])
        questions.append({
            "question": f"关于您的{proj.get('name', '')}项目，请详细说明：1)项目的业务背景和目标 2)您负责的核心模块 3)使用{', '.join(techs[:2]) if techs else '相关技术'}时遇到的最棘手问题 4)最终交付的业务指标。",
            "purpose": f"通过四个维度深挖项目{proj.get('name', '')}的真实性",
            "category": "项目经历深挖",
            "follow_up": "如果重新做这个项目，你会在哪些地方做不同的技术选型？"
        })

    # 岗位技能实操
    for skill in talent_profile.get("required_skills", [])[:3]:
        resp_text = talent_profile.get("responsibilities", [""])[0] if talent_profile.get("responsibilities") else "日常工作"
        questions.append({
            "question": f"假设你入职后需要用{skill}来完成{resp_text}，请描述你的具体实施方案，包括技术选型、关键步骤和预期可能遇到的问题。",
            "purpose": f"通过实操场景验证{skill}的实战能力",
            "category": "岗位技能实操",
            "follow_up": f"你之前用{skill}做过类似的事情吗？结果如何？"
        })

    # 技能盲区论证
    for gap_skill in skill_gaps[:2]:
        questions.append({
            "question": f"这个岗位需要使用{gap_skill}，我注意到您的简历中没有提到相关经验。如果现在给您一个需要用{gap_skill}解决的问题，您会从哪里入手？您的学习路径是什么？",
            "purpose": f"论证候选人在{gap_skill}领域的潜力和学习能力",
            "category": "技能盲区论证",
            "follow_up": f"您有没有了解过{gap_skill}的基本原理？能简单描述一下吗？"
        })

    # 风险点验证
    for risk in assessment.get("risks", [])[:3]:
        cat = risk.get("category", "")
        desc = risk.get("description", "")
        if "稳定" in cat or "跳槽" in desc:
            questions.append({
                "question": "我注意到您过去几年换了几份工作。请按时间顺序，逐一说明每次离开的具体原因、离开时的薪资变化、以及每次求职时最看重什么。",
                "purpose": f"风险验证: {desc}，评估真实离职动机和稳定性预期",
                "category": "风险点验证",
                "follow_up": "如果这次入职，什么情况会让您考虑离开？"
            })
        elif "技能" in cat or "不足" in desc or "匹配" in cat:
            questions.append({
                "question": f"从评估来看，您在某些岗位核心技能上经验偏少。请分享一个您在短时间内从零掌握一项新技术并实际应用的案例，说明当时的学习方法和最终效果。",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": "您通常用什么方法来保持技能的更新和学习？"
            })
        elif "空窗" in cat or "空缺" in desc:
            questions.append({
                "question": "您的简历中有一段时间没有工作记录，能否说明这段时间您在做什么？有没有进行相关学习或项目实践？",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": "这段空窗期对您后来的工作有什么影响？"
            })
        else:
            questions.append({
                "question": f"关于{cat}，能否用一个具体的工作案例来说明您在这方面的实际水平？",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": f"您觉得自己在{cat}方面还有哪些提升空间？"
            })

    # 压力/情景题
    job_title = talent_profile.get("job_title", "该岗位")
    questions.append({
        "question": f"假设您作为{job_title}入职第二周，发现前任留下的系统存在严重的架构问题，同时业务方催着要上新功能。您会如何权衡和推进？",
        "purpose": "模拟真实工作场景，考察优先级判断和沟通推动能力",
        "category": "压力/情景测试",
        "follow_up": "您过去有没有遇到过类似的两难局面？当时怎么处理的？"
    })
    questions.append({
        "question": "如果您和直属领导在技术方案上产生了严重分歧，而您确信自己的方案更优，您会怎么做？请说一个您过去处理类似情况的真实案例。",
        "purpose": "考察向上管理能力和技术坚持/妥协的判断力",
        "category": "压力/情景测试",
        "follow_up": "最终的结果是什么？事后回看您觉得当时的做法对吗？"
    })

    return questions
