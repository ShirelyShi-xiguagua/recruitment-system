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
    for i, exp in enumerate(work_exp[:4]):
        company = exp.get("company", "未知公司")
        position = exp.get("position", "未知职位")
        duration = exp.get("duration", "")
        achievements = exp.get("achievements", [])
        responsibilities = exp.get("responsibilities", [])
        lines.append(f"【经历{i+1}】{company} | {position} | {duration}")
        if responsibilities:
            lines.append(f"  职责: {'; '.join(responsibilities[:4])}")
        if achievements:
            lines.append(f"  成就: {'; '.join(achievements[:4])}")
    for i, proj in enumerate(projects[:4]):
        name = proj.get("name", "未知项目")
        desc = proj.get("description", "")
        techs = proj.get("technologies", [])
        lines.append(f"【项目{i+1}】{name}")
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
    return list((required | tools_required) - (have | tools_have))[:6]


def generate_interview_questions(
    talent_profile: Dict[str, Any],
    resume_profile: Dict[str, Any],
    assessment: Dict[str, Any]
) -> List[Dict[str, str]]:
    project_context = _build_project_context(resume_profile)
    skill_gaps = _find_skill_gaps(talent_profile, resume_profile)

    prompt = f"""你是一位有15年经验的技术面试官，擅长通过"拆穿型"问题设计甄别候选人的真实能力。

## 面试题目设计方法论

你必须严格遵循以下三层面试设计框架：

### 第一层：项目深挖（拆穿型，最有效）
不要问"你做过什么项目"，而是让候选人讲一个具体项目，然后按以下路径追问：
1. 架构图：整体架构是什么？画出来/讲清楚
2. 数据流：数据从哪里来？怎么处理？
3. 方案选型：为什么选这个方案而不是其他方案？做过哪些trade-off？
4. 踩坑经历：最大的坑是什么？怎么解决的？
5. 反思优化：如果重做一遍会怎么优化？

识别"包装型选手"的信号：说不清数据流、讲不清设计原因、一问细节就抽象化

### 第二层：现场轻设计题（比算法题更有用）
给一个与目标岗位相关的真实业务场景，看候选人能否覆盖：
- 系统设计全链路思维
- 工程化意识（并发、缓存、监控、降本）
- 成本意识（非常关键）
- fallback和容错设计

关键不是答案对不对，而是有没有工程意识+成本意识

### 第三层：反作弊验证（识别AI造简历）
方法1 - 细节压强测试：连续追问一个技术点的具体数值、对比、踩坑故事
方法2 - 改方案测试：给一个变化（数据量扩大10倍/延迟要求缩短10倍），看能否灵活调整
方法3 - 反直觉问题：问"行业坑点"，只有真正做过的人才会有感觉

---

## 岗位信息
职位: {talent_profile.get('job_title', '未知')}
核心技能要求: {', '.join(talent_profile.get('required_skills', []))}
岗位职责: {'; '.join(talent_profile.get('responsibilities', [])[:5])}
工具/技术栈: {', '.join(talent_profile.get('tools_technologies', []))}

## 候选人项目经历（深挖对象）
{project_context}

## 候选人技能盲区（简历未体现但岗位要求）
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
        "question": "具体的面试问题",
        "purpose": "这道题考察什么、为什么要问",
        "category": "问题类别",
        "follow_up": "追问方向",
        "red_flag": "候选人回答中哪些信号说明可能是编造的"
    }}
]

## 出题要求（共18-22题）

**一、项目深挖-架构追问（3-4题）** category="项目深挖-架构追问"
- 必须点名简历中具体的项目/公司名称
- 追问整体架构设计、数据流向、模块划分
- 追问"为什么这么设计而不是其他方案"
- 追问最大的坑和解决方案
- red_flag中写明包装型选手的典型回答特征

**二、项目深挖-方案选型（2-3题）** category="项目深挖-方案选型"
- 针对候选人简历中提到的具体技术选型进行追问
- 问trade-off：为什么用A不用B？对比过哪些方案？
- 问"如果重做一遍会怎么优化"
- red_flag：只会说优点不会说缺点、无法对比多种方案

**三、项目深挖-数据与指标（2-3题）** category="项目深挖-数据与指标"
- 追问具体的业务指标：解决了什么业务问题？效果数据是什么？
- 追问数据量级、QPS、延迟等工程指标
- 追问"有没有被用户真正用起来？用户反馈如何？"
- red_flag：说不出具体数字、只有模糊描述

**四、现场轻设计题（3-4题）** category="现场轻设计题"
- 基于目标岗位的核心职责，设计一个真实业务场景
- 要求候选人现场给出系统设计方案
- 关注：全链路思维、工程化能力、成本意识、容错设计
- follow_up中追问：并发怎么处理？成本怎么控？模型挂了怎么办？监控怎么做？

**五、技能盲区论证（2-3题）** category="技能盲区论证"
- 针对候选人简历中未提及但岗位要求的技能
- 不是问"你会不会"，而是给一个使用该技能的具体场景
- 看候选人的思路、学习能力、是否有迁移能力

**六、反作弊-细节压强（2-3题）** category="反作弊-细节压强"
- 针对简历中最亮眼的项目/成就，连续追问具体技术参数
- 例如：具体用了什么模型？参数多少？为什么选这个？试过别的吗？效果差多少？
- red_flag：回答开始模糊化、用"大概""差不多"搪塞

**七、反作弊-改方案测试（1-2题）** category="反作弊-改方案测试"
- 基于候选人描述的项目，给一个条件变化
- 例如"数据量扩大10倍怎么办？""延迟要求从3s降到300ms怎么办？"
- 看候选人能否灵活调整方案（索引优化、分层存储、缓存策略等）
- red_flag：无法给出具体优化方向，只会说"加机器"

**八、反直觉问题（1-2题）** category="反直觉问题"
- 问行业中"做过坑的人才知道"的反直觉问题
- 与岗位技术栈相关，例如：
  - 为什么XX技术在某些场景下反而更差？
  - 为什么某个看似高级的方案在实际中不好用？
- 真正做过的人会有具体案例和踩坑故事

**九、风险点验证（2-3题）** category="风险点验证"
- 针对评估中发现的每个具体风险点设计验证问题
- 跳槽频繁→逐一追问每次离职的真正原因和薪资变化
- 经验不足→用场景题验证实际水平
- 稳定性→问"什么情况会让你考虑离开"

每道题的red_flag字段必须填写，帮助面试官识别"包装型"回答。"""

    try:
        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=6000,
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
    job_title = talent_profile.get("job_title", "该岗位")
    required_skills = talent_profile.get("required_skills", [])

    # === 项目深挖-架构追问 ===
    if work_exp:
        exp = work_exp[0]
        company = exp.get("company", "上一家公司")
        position = exp.get("position", "上一个岗位")
        resps = exp.get("responsibilities", [])
        questions.append({
            "question": f"请从整体架构层面描述您在{company}担任{position}时负责的核心系统：整体架构长什么样？有哪些核心模块？数据怎么流转的？您负责哪个部分？",
            "purpose": "通过架构层面追问验证候选人是否真正参与过系统设计",
            "category": "项目深挖-架构追问",
            "follow_up": "这个架构做过哪些迭代？为什么要改？改完效果如何？",
            "red_flag": "无法画出清晰的架构图；说不清模块间的数据流向；只描述自己'用了什么'而说不清'为什么这么设计'"
        })
    if projects:
        proj = projects[0]
        techs = proj.get("technologies", [])
        questions.append({
            "question": f"关于您的{proj.get('name', '')}项目，请讲清楚三件事：1)为什么选{', '.join(techs[:2]) if techs else '这套技术栈'}而不是其他方案？2)做过哪些方案对比？3)最大的技术坑是什么，怎么解决的？",
            "purpose": "通过方案选型追问验证真实参与度",
            "category": "项目深挖-方案选型",
            "follow_up": "如果让你重做这个项目，你会在哪些地方做不同的选择？为什么？",
            "red_flag": "只能说选型的优点，说不出缺点和trade-off；对比时只能列举名字但说不出差异"
        })

    # === 项目深挖-数据与指标 ===
    if work_exp:
        questions.append({
            "question": f"您在{work_exp[0].get('company', '上一家公司')}做的项目，最终解决了什么业务问题？用什么指标衡量效果？具体数据是多少？这个系统有多少人在用？",
            "purpose": "验证候选人是'做项目'还是'做结果'",
            "category": "项目深挖-数据与指标",
            "follow_up": "这些数据是怎么统计的？上线前后对比差多少？用户反馈是什么？",
            "red_flag": "说不出具体数字；只有'提升了效率''优化了体验'等模糊描述；无法说明指标怎么定的"
        })

    # === 现场轻设计题 ===
    resp_text = talent_profile.get("responsibilities", [""])[0] if talent_profile.get("responsibilities") else "核心业务"
    questions.append({
        "question": f"现场设计题：假设要为公司搭建一个{resp_text}系统，要求支持1000人同时使用，成本可控。请给出你的系统设计方案，包括架构、技术选型、数据处理流程。",
        "purpose": "考察全链路系统设计能力、工程化意识和成本意识",
        "category": "现场轻设计题",
        "follow_up": "并发怎么处理？成本怎么控？核心服务挂了怎么办？怎么监控系统质量？",
        "red_flag": "只能说理论架构，无法回答具体的工程问题（缓存策略、降级方案、监控指标）；没有成本意识"
    })
    if len(required_skills) >= 2:
        questions.append({
            "question": f"设计题：如果需要用{required_skills[0]}和{required_skills[1]}搭建一个处理大规模数据的服务，延迟要求500ms以内，你会怎么设计？请讲清楚关键链路和可能的瓶颈点。",
            "purpose": f"验证候选人对{required_skills[0]}和{required_skills[1]}的工程化理解",
            "category": "现场轻设计题",
            "follow_up": "如果延迟要求缩短到50ms怎么办？如果数据量增长10倍呢？",
            "red_flag": "只会堆技术名词，说不清关键链路；无法分析瓶颈在哪里"
        })

    # === 技能盲区论证 ===
    for gap in skill_gaps[:2]:
        questions.append({
            "question": f"这个岗位需要用到{gap}，我注意到您简历中没有直接的经验。给你一个场景：如果现在需要用{gap}解决一个线上问题，你会从哪里入手？你的学习路径是什么？",
            "purpose": f"评估候选人在{gap}领域的学习能力和技术迁移能力",
            "category": "技能盲区论证",
            "follow_up": f"你之前用过什么类似的技术？和{gap}相比有什么异同？",
            "red_flag": "完全没有思路；或者只会说'我可以学'但说不出具体怎么学"
        })

    # === 反作弊-细节压强 ===
    if projects or work_exp:
        target = projects[0].get("name", "") if projects else work_exp[0].get("company", "")
        questions.append({
            "question": f"关于{target}项目，我想深入了解一个技术细节：你们的数据量有多大？处理延迟是多少？核心算法/模型的具体参数是什么？为什么选这个参数？试过其他配置吗？效果差多少？",
            "purpose": "通过连续细节追问验证经历真实性（编造者在这一步会开始模糊）",
            "category": "反作弊-细节压强",
            "follow_up": "这些数据是在什么环境下测的？有没有做过A/B测试？",
            "red_flag": "回答开始用'大概''差不多''记不太清了'搪塞；无法给出任何具体数值"
        })

    # === 反作弊-改方案测试 ===
    questions.append({
        "question": "基于你刚才描述的项目方案，现在需求变了：数据量扩大10倍，同时要把成本降低50%。你的方案需要做哪些调整？请具体说。",
        "purpose": "通过方案变化测试候选人是否真正理解系统（真做过的人能灵活调整）",
        "category": "反作弊-改方案测试",
        "follow_up": "你会优先优化哪个环节？为什么？有没有你不愿意妥协的部分？",
        "red_flag": "只会说'加机器'或'用更好的模型'；无法给出具体的优化策略（缓存、分层存储、降精度等）"
    })

    # === 反直觉问题 ===
    if required_skills:
        questions.append({
            "question": f"反直觉问题：你在实际工作中有没有遇到过{required_skills[0]}在某些场景下反而比简单方案更差的情况？为什么会这样？你怎么处理的？",
            "purpose": "测试候选人是否有深度实践经验（只有踩过坑的人才会有反直觉认知）",
            "category": "反直觉问题",
            "follow_up": "在你的经验里，什么时候不应该用这个技术？",
            "red_flag": "从没想过这个技术有缺点；无法举出具体的反面案例"
        })

    # === 风险点验证 ===
    for risk in assessment.get("risks", [])[:3]:
        cat = risk.get("category", "")
        desc = risk.get("description", "")
        if "稳定" in cat or "跳槽" in desc:
            questions.append({
                "question": "我注意到您过去几年换了几份工作。请按时间顺序，逐一说明：每次离开的真正原因、离开时的薪资变化、以及每次求职时最看重什么。",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": "如果入职后发现工作内容和预期有差距，你会怎么做？什么情况会让你考虑离开？",
                "red_flag": "每次离职原因都说是'公司问题'而从不反思自身；薪资变化逻辑不通"
            })
        elif "技能" in cat or "不足" in desc or "匹配" in cat:
            questions.append({
                "question": "从评估来看，您在部分岗位核心技能上经验偏少。请分享一个您在短时间内从零掌握一项新技术并用于生产环境的案例，说明学习方法和最终效果数据。",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": "这个学习过程中踩过什么坑？如果有人问你怎么学，你会怎么建议？",
                "red_flag": "举不出具体案例；或者案例只到'学了一下'而没有实际应用和效果"
            })
        elif "空窗" in cat or "空缺" in desc:
            questions.append({
                "question": "您的简历中有一段时间没有工作记录。能否详细说明这段时间您在做什么？有没有进行技术学习或项目实践？",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": "这段经历对您后来的工作有什么影响？技术有没有落下？怎么追回的？",
                "red_flag": "解释含糊不清；或者说在学习但举不出任何学习成果"
            })
        else:
            questions.append({
                "question": f"关于{cat}方面，请用一个你亲身经历的具体案例来说明你的实际水平。要有背景、你的做法、和最终结果。",
                "purpose": f"风险验证: {desc}",
                "category": "风险点验证",
                "follow_up": f"如果在新岗位遇到类似情况，你会怎么处理？",
                "red_flag": "案例缺乏细节；或者回答过于教科书化"
            })

    return questions
