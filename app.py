import streamlit as st
import os
import json
import io
from jd_analyzer import extract_talent_profile
from resume_analyzer import extract_resume_profile
from risk_assessor import assess_match_and_risks
from question_generator import generate_interview_questions

st.set_page_config(
    page_title="简历风险评估器",
    page_icon=":clipboard:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
for key in ["talent_profile", "resume_profile", "assessment", "questions",
            "step", "edited_profile", "jd_text", "resume_text"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "step" not in st.session_state or st.session_state.step is None:
    st.session_state.step = 1

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #e0f2ff 0%, #b3d9ff 40%, #8cc5ff 100%);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #1a3a5c;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: #2c5282;
}
.main .block-container { padding-top: 1.5rem; max-width: 1100px; }
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #f0f7ff 0%, #e0efff 100%);
    border: 1px solid #c4daf0; border-radius: 12px; padding: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
div[data-testid="stMetric"] label { color: #1a3a5c !important; font-weight: 600 !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #0d47a1 !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    border: none; border-radius: 8px; font-weight: 600;
    box-shadow: 0 3px 10px rgba(33,150,243,0.3);
}
h1 { color: #1a3a5c; font-weight: 700; }
h2 { color: #1e4976; border-bottom: 2px solid #e0efff; padding-bottom: 0.5rem; }
hr { border-color: #d0e4f5; }
.step-card {
    background: white; border-radius: 12px; padding: 1.5rem;
    border: 1px solid #d0e4f5; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
.step-active { border-left: 4px solid #2196F3; }
.step-done { border-left: 4px solid #4CAF50; opacity: 0.85; }
.step-waiting { border-left: 4px solid #ccc; opacity: 0.5; }
.step-num {
    display: inline-block; width: 28px; height: 28px; border-radius: 50%;
    text-align: center; line-height: 28px; font-weight: 700; font-size: 0.9rem;
    margin-right: 0.5rem;
}
.num-active { background: #2196F3; color: white; }
.num-done { background: #4CAF50; color: white; }
.num-waiting { background: #ccc; color: white; }
.profile-field {
    background: #f8fbff; border: 1px solid #e0efff; border-radius: 8px;
    padding: 0.6rem 0.8rem; margin-bottom: 0.5rem;
}
.profile-label { color: #5a7a9a; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.2rem; }
.question-card {
    background: linear-gradient(135deg, #f8fbff 0%, #f0f6ff 100%);
    border-left: 4px solid #2196F3; border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.question-card .q-category {
    color: #1976D2; font-size: 0.8rem; font-weight: 600;
    letter-spacing: 0.5px; margin-bottom: 0.3rem;
}
.question-card .q-text { color: #1a3a5c; font-size: 1rem; font-weight: 500; margin-bottom: 0.4rem; }
.question-card .q-purpose { color: #5a7a9a; font-size: 0.85rem; font-style: italic; }
.question-card .q-followup { color: #7a9aba; font-size: 0.8rem; margin-top: 0.3rem; }
div[data-testid="stFileUploader"] {
    background: #f8fbff; border-radius: 8px; border: 2px dashed #b3d9ff; padding: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


def read_uploaded_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".txt"):
        for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception as e:
            st.error(f"PDF解析失败: {e}")
            return ""
    if name.endswith(".docx"):
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
        except Exception as e:
            st.error(f"DOCX解析失败: {e}")
            return ""
    return raw.decode("utf-8", errors="replace")


# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("# :clipboard: 简历风险评估器")
    st.markdown("---")

    # 步骤指示器
    step = st.session_state.step
    steps_info = [
        ("上传JD & 生成画像", 1),
        ("查看/编辑人才画像", 2),
        ("上传简历 & 评估", 3),
        ("查看分析报告", 4),
    ]
    for label, num in steps_info:
        if num < step:
            st.markdown(f'<div><span class="step-num num-done">✓</span><span style="color:#4CAF50;">{label}</span></div>', unsafe_allow_html=True)
        elif num == step:
            st.markdown(f'<div><span class="step-num num-active">{num}</span><strong style="color:#1a3a5c;">{label}</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div><span class="step-num num-waiting">{num}</span><span style="color:#aaa;">{label}</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 重置按钮
    if st.button(":arrows_counterclockwise: 重新开始", use_container_width=True):
        for key in ["talent_profile", "resume_profile", "assessment", "questions",
                     "edited_profile", "jd_text", "resume_text"]:
            st.session_state[key] = None
        st.session_state.step = 1
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#5a7a9a; font-size:0.8rem;">
        Powered by Claude AI<br>v3.0
    </div>
    """, unsafe_allow_html=True)


# ===== 步骤1: 上传JD =====
if st.session_state.step == 1:
    st.markdown("## :one: 上传岗位JD")
    st.caption("上传职位描述后，系统将自动提炼人才画像，您可以查看和编辑")

    jd_mode = st.radio("输入方式", ["上传文件", "粘贴文本"], key="jd_mode_s1", horizontal=True)
    if jd_mode == "上传文件":
        jd_file = st.file_uploader("选择JD文件", type=["txt", "pdf", "docx"], key="jd_s1")
        jd_text = read_uploaded_file(jd_file) if jd_file else ""
    else:
        jd_text = st.text_area("粘贴JD内容", height=250, placeholder="请粘贴完整的职位描述...")

    if jd_text:
        st.success(f"JD已就绪（{len(jd_text)} 字）")
        if st.button(":mag: 生成人才画像", type="primary", use_container_width=True):
            with st.spinner("正在分析JD，提炼人才画像..."):
                profile = extract_talent_profile(jd_text)
                st.session_state.talent_profile = profile
                st.session_state.edited_profile = json.loads(json.dumps(profile))
                st.session_state.jd_text = jd_text
                st.session_state.step = 2
                st.rerun()


# ===== 步骤2: 查看/编辑人才画像 =====
elif st.session_state.step == 2:
    st.markdown("## :two: 岗位人才画像")
    st.caption("AI已根据JD生成人才画像，您可以直接编辑调整后再进行简历评估")

    profile = st.session_state.edited_profile

    # 基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        profile["job_title"] = st.text_input("职位名称", value=profile.get("job_title", ""))
    with col2:
        profile["experience_years"] = st.number_input("经验要求(年)", value=int(profile.get("experience_years", 0)), min_value=0, max_value=30)
    with col3:
        profile["education"] = st.text_input("学历要求", value=profile.get("education", ""))

    col4, col5 = st.columns(2)
    with col4:
        profile["job_type"] = st.text_input("工作类型", value=profile.get("job_type", ""))
    with col5:
        profile["location"] = st.text_input("工作地点", value=profile.get("location", ""))

    st.markdown("---")

    # 核心技能 - 可编辑的tag风格
    st.markdown("#### :wrench: 核心技能要求")
    required_skills_str = st.text_area(
        "必备技能（每行一个）",
        value="\n".join(profile.get("required_skills", [])),
        height=100,
        help="每行填写一项技能，系统将据此评估简历匹配度"
    )
    profile["required_skills"] = [s.strip() for s in required_skills_str.split("\n") if s.strip()]

    preferred_skills_str = st.text_area(
        "加分技能（每行一个）",
        value="\n".join(profile.get("preferred_skills", [])),
        height=80
    )
    profile["preferred_skills"] = [s.strip() for s in preferred_skills_str.split("\n") if s.strip()]

    st.markdown("---")

    # 岗位职责
    st.markdown("#### :clipboard: 岗位职责")
    resp_str = st.text_area(
        "职责描述（每行一条）",
        value="\n".join(profile.get("responsibilities", [])),
        height=120
    )
    profile["responsibilities"] = [s.strip() for s in resp_str.split("\n") if s.strip()]

    st.markdown("---")

    # 软技能
    col_soft, col_tools = st.columns(2)
    with col_soft:
        st.markdown("#### :people_holding_hands: 软技能要求")
        soft_str = st.text_area(
            "软技能（每行一个）",
            value="\n".join(profile.get("soft_skills", [])),
            height=80,
            key="soft_skills_edit"
        )
        profile["soft_skills"] = [s.strip() for s in soft_str.split("\n") if s.strip()]

    with col_tools:
        st.markdown("#### :hammer_and_wrench: 工具/技术栈")
        tools_str = st.text_area(
            "工具和技术（每行一个）",
            value="\n".join(profile.get("tools_technologies", [])),
            height=80,
            key="tools_edit"
        )
        profile["tools_technologies"] = [s.strip() for s in tools_str.split("\n") if s.strip()]

    st.markdown("---")

    # 预览JSON（折叠）
    with st.expander(":mag: 查看完整画像JSON"):
        st.json(profile)

    st.session_state.edited_profile = profile

    col_back, col_next = st.columns([1, 2])
    with col_back:
        if st.button(":arrow_left: 返回修改JD", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button(":arrow_right: 确认画像，上传简历", type="primary", use_container_width=True):
            st.session_state.talent_profile = json.loads(json.dumps(profile))
            st.session_state.step = 3
            st.rerun()


# ===== 步骤3: 上传简历 & 一键评估 =====
elif st.session_state.step == 3:
    st.markdown("## :three: 上传简历并评估")

    # 显示当前画像摘要
    tp = st.session_state.talent_profile
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f0f7ff,#e0efff); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; border:1px solid #c4daf0;">
        <div style="font-weight:700; color:#1a3a5c; margin-bottom:0.5rem;">当前岗位: {tp.get('job_title', '未知')}</div>
        <div style="color:#5a7a9a; font-size:0.9rem;">
            核心技能: {', '.join(tp.get('required_skills', [])[:6])} |
            经验要求: {tp.get('experience_years', 0)}年 |
            学历: {tp.get('education', '不限')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(":pencil2: 返回编辑画像", key="back_to_profile"):
        st.session_state.step = 2
        st.rerun()

    st.markdown("---")

    resume_mode = st.radio("简历输入方式", ["上传文件", "粘贴文本"], key="resume_mode_s3", horizontal=True)
    if resume_mode == "上传文件":
        resume_file = st.file_uploader("选择简历文件", type=["txt", "pdf", "docx"], key="resume_s3")
        resume_text = read_uploaded_file(resume_file) if resume_file else ""
    else:
        resume_text = st.text_area("粘贴简历内容", height=300, placeholder="请粘贴候选人简历...")

    if resume_text:
        st.success(f"简历已就绪（{len(resume_text)} 字）")
        if st.button(":rocket: 开始全面评估", type="primary", use_container_width=True):
            talent_profile = st.session_state.talent_profile

            with st.status(":bust_in_silhouette: 正在解析简历...", expanded=True) as status:
                resume_profile = extract_resume_profile(resume_text)
                st.session_state.resume_profile = resume_profile
                status.update(label=":white_check_mark: 简历解析完成", state="complete", expanded=False)

            with st.status(":bar_chart: 正在评估匹配度和风险...", expanded=True) as status:
                assessment = assess_match_and_risks(talent_profile, resume_profile)
                st.session_state.assessment = assessment
                status.update(label=":white_check_mark: 评估完成", state="complete", expanded=False)

            with st.status(":dart: 正在生成面试题目...", expanded=True) as status:
                questions = generate_interview_questions(talent_profile, resume_profile, assessment)
                st.session_state.questions = questions
                status.update(label=":white_check_mark: 题目生成完成", state="complete", expanded=False)

            st.session_state.resume_text = resume_text
            st.session_state.step = 4
            st.rerun()


# ===== 步骤4: 分析报告 =====
elif st.session_state.step == 4:
    talent_profile = st.session_state.talent_profile
    resume_profile = st.session_state.resume_profile
    assessment = st.session_state.assessment
    questions = st.session_state.questions

    st.markdown("## :four: 评估报告")

    # 概览卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("匹配度", f"{assessment['match_score']}%")
    with col2:
        risk_level = assessment['risk_level']
        st.metric("风险等级", risk_level)
    with col3:
        st.metric("建议", assessment.get("recommendation", "待定"))
    with col4:
        name = resume_profile.get("name", "候选人")
        exp = resume_profile.get("total_experience_years", 0)
        st.metric("候选人", f"{name} ({exp}年)")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":bust_in_silhouette: 候选人画像",
        ":bar_chart: 匹配分析",
        ":warning: 风险报告",
        ":dart: 面试题目",
        ":page_facing_up: 岗位画像"
    ])

    with tab1:
        st.markdown("#### 候选人概况")
        cp = resume_profile

        # 基本信息卡
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.markdown(f"""
            <div style="background:white; border-radius:10px; padding:1rem; border:1px solid #e0efff; margin-bottom:1rem;">
                <div style="font-size:1.3rem; font-weight:700; color:#1a3a5c;">{cp.get('name', '未知')}</div>
                <div style="color:#5a7a9a; margin-top:0.3rem;">{cp.get('current_job', '')} @ {cp.get('current_company', '')}</div>
                <div style="color:#5a7a9a; margin-top:0.2rem;">工作经验: {cp.get('total_experience_years', 0)} 年</div>
            </div>
            """, unsafe_allow_html=True)

        with info_col2:
            contact = cp.get("contact_info", {})
            st.markdown(f"""
            <div style="background:white; border-radius:10px; padding:1rem; border:1px solid #e0efff; margin-bottom:1rem;">
                <div style="color:#5a7a9a;">📧 {contact.get('email', '未提供')}</div>
                <div style="color:#5a7a9a;">📱 {contact.get('phone', '未提供')}</div>
                <div style="color:#5a7a9a;">📍 {contact.get('location', '未提供')}</div>
            </div>
            """, unsafe_allow_html=True)

        # 技能
        skills = cp.get("skills", {})
        if skills.get("technical_skills"):
            st.markdown("**技术技能**")
            st.markdown(" ".join([f"`{s}`" for s in skills["technical_skills"]]))
        if skills.get("tools"):
            st.markdown("**工具**")
            st.markdown(" ".join([f"`{s}`" for s in skills["tools"]]))

        # 工作经历
        if cp.get("work_experience"):
            st.markdown("#### 工作经历")
            for exp in cp["work_experience"]:
                with st.expander(f"{exp.get('company', '未知')} - {exp.get('position', '未知')} ({exp.get('duration', '')})"):
                    if exp.get("responsibilities"):
                        st.markdown("**职责:**")
                        for r in exp["responsibilities"]:
                            st.markdown(f"- {r}")
                    if exp.get("achievements"):
                        st.markdown("**成就:**")
                        for a in exp["achievements"]:
                            st.markdown(f"- {a}")

        # 项目经历
        if cp.get("projects"):
            st.markdown("#### 项目经历")
            for proj in cp["projects"]:
                with st.expander(f"{proj.get('name', '未知')} ({proj.get('duration', '')})"):
                    st.write(proj.get("description", ""))
                    if proj.get("technologies"):
                        st.markdown("技术栈: " + ", ".join(proj["technologies"]))

        # 完整JSON
        with st.expander(":mag: 查看完整候选人画像JSON"):
            st.json(resume_profile)

    with tab2:
        st.markdown("#### 多维匹配分析")
        for item in assessment.get('match_details', []):
            score = item['score']
            color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 60 else "#F44336"
            bar_width = max(score, 5)
            st.markdown(f"""
            <div style="background:white; border-radius:8px; padding:0.8rem 1rem; margin-bottom:0.6rem; border-left:4px solid {color}; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#1a3a5c;">{item['dimension']}</span>
                    <span style="font-weight:700; color:{color}; font-size:1.2rem;">{score}%</span>
                </div>
                <div style="background:#eee; border-radius:4px; height:6px; margin-top:0.4rem;">
                    <div style="background:{color}; border-radius:4px; height:6px; width:{bar_width}%;"></div>
                </div>
                <div style="color:#5a7a9a; font-size:0.9rem; margin-top:0.3rem;">{item['comment']}</div>
            </div>
            """, unsafe_allow_html=True)

        if assessment.get('strengths'):
            st.markdown("#### :white_check_mark: 优势亮点")
            for s in assessment['strengths']:
                st.success(s)

    with tab3:
        if assessment.get('risks'):
            for risk in assessment['risks']:
                sev = risk.get('severity', '中')
                sev_color = {"高": "#F44336", "中": "#FF9800", "低": "#FFC107"}.get(sev, "#FF9800")
                st.markdown(f"""
                <div style="background:white; border-radius:8px; padding:1rem; margin-bottom:0.8rem; border-left:4px solid {sev_color}; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
                        <span style="font-weight:600; color:#1a3a5c; font-size:1.05rem;">{risk['category']}</span>
                        <span style="background:{sev_color}; color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem;">严重程度: {sev}</span>
                    </div>
                    <div style="color:#5a7a9a;">{risk['description']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("未发现明显风险")

        if assessment.get('suggestions'):
            st.markdown("#### :bulb: 改进建议")
            for s in assessment['suggestions']:
                st.info(s)

    with tab4:
        st.markdown("#### 面试题目清单")
        st.caption(f"共 {len(questions)} 道题目，针对候选人简历和岗位要求定制")

        categories = {}
        for q in questions:
            cat = q.get("category", "其他")
            categories.setdefault(cat, []).append(q)

        cat_icons = {
            "项目经历深挖": "🔍", "经历真实性验证": "🔍",
            "岗位技能实操": "🔧", "核心能力考察": "🔧",
            "技能盲区论证": "💡",
            "风险点验证": "⚠️", "风险点深挖": "⚠️",
            "压力/情景测试": "⚡", "岗位匹配验证": "🎯",
        }

        for cat, qs in categories.items():
            icon = cat_icons.get(cat, "📋")
            st.markdown(f"##### {icon} {cat}（{len(qs)}题）")
            for i, q in enumerate(qs, 1):
                follow_up = q.get("follow_up", "")
                follow_html = f'<div class="q-followup">↪️ 追问: {follow_up}</div>' if follow_up else ""
                st.markdown(f"""
                <div class="question-card">
                    <div class="q-category">{cat}</div>
                    <div class="q-text">{i}. {q['question']}</div>
                    <div class="q-purpose">🎯 考察点: {q['purpose']}</div>
                    {follow_html}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("")

    with tab5:
        st.markdown("#### 岗位人才画像")
        st.json(talent_profile)
        if st.button(":pencil2: 返回编辑画像并重新评估"):
            st.session_state.step = 2
            st.rerun()

    # 底部操作栏
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button(":pencil2: 编辑人才画像", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_b:
        if st.button(":bust_in_silhouette: 换一份简历评估", use_container_width=True):
            st.session_state.resume_profile = None
            st.session_state.assessment = None
            st.session_state.questions = None
            st.session_state.step = 3
            st.rerun()
    with col_c:
        report = {
            "岗位画像": talent_profile,
            "候选人画像": resume_profile,
            "评估结果": assessment,
            "面试题目": questions
        }
        st.download_button(
            ":arrow_down: 导出报告JSON",
            data=json.dumps(report, ensure_ascii=False, indent=2),
            file_name="evaluation_report.json",
            mime="application/json",
            use_container_width=True
        )
