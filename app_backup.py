import streamlit as st
import os
import json
import io
from jd_analyzer import extract_talent_profile
from resume_analyzer import extract_resume_profile
from risk_assessor import assess_match_and_risks
from question_generator import generate_interview_questions
from profile_store import save_profile, load_all_profiles, load_profile, update_profile, delete_profile, export_all_profiles, import_profiles

st.set_page_config(page_title="简历风险评估器", page_icon=":clipboard:", layout="wide", initial_sidebar_state="expanded")

# 初始化 session state
INIT_KEYS = ["talent_profile", "resume_profile", "assessment", "questions",
             "edited_profile", "jd_text", "resume_text", "current_profile_id",
             "manage_edit_id", "manage_mode"]
for key in INIT_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None
if "step" not in st.session_state:
    st.session_state.step = 1
if "page" not in st.session_state:
    st.session_state.page = "evaluate"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* 全局背景 — 浅紫蓝渐变 */
.stApp {
    background: linear-gradient(135deg, #f5f0ff 0%, #e8e0ff 15%, #dce8ff 40%, #e0f4ff 70%, #f0f0ff 100%);
}
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }

/* 侧边栏 — 深紫毛玻璃 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2d1b69 0%, #1e1145 50%, #150d35 100%) !important;
}
section[data-testid="stSidebar"] * { color: #e0d4ff !important; }
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 { color: #ffffff !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }

/* 主内容区 */
.main .block-container { padding-top: 2rem; max-width: 1150px; }

/* 毛玻璃卡片基础 */
.glass-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(80,60,180,0.08), 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(80,60,180,0.12), 0 4px 12px rgba(0,0,0,0.06);
}

/* Metric 卡片 */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 4px 20px rgba(100,80,200,0.08);
}
div[data-testid="stMetric"] label { color: #6b5ce7 !important; font-weight: 600 !important; font-size: 0.85rem !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #2d1b69 !important; font-weight: 800 !important; }

/* 按钮 — 紫蓝渐变 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c5ce7 0%, #6366f1 50%, #4f8cff 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.8rem !important;
    font-weight: 600 !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35);
    transition: all 0.3s;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 25px rgba(99,102,241,0.5);
    transform: translateY(-2px);
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.6) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 12px !important;
    color: #4f46e5 !important;
    font-weight: 500 !important;
}

/* 标题 */
h1 { color: #2d1b69 !important; font-weight: 800 !important; letter-spacing: -0.5px; }
h2 { color: #3b2d7a !important; font-weight: 700 !important; border-bottom: 2px solid rgba(99,102,241,0.15); padding-bottom: 0.5rem; }
h3, h4, h5 { color: #4a3d8f !important; font-weight: 600 !important; }

/* 分割线 */
hr { border-color: rgba(99,102,241,0.1) !important; }

/* 步骤指示器 */
.step-num {
    display: inline-block; width: 30px; height: 30px; border-radius: 50%;
    text-align: center; line-height: 30px; font-weight: 700; font-size: 0.85rem;
    margin-right: 0.6rem;
}
.num-active { background: linear-gradient(135deg, #7c5ce7, #6366f1); color: white; box-shadow: 0 2px 10px rgba(99,102,241,0.4); }
.num-done { background: linear-gradient(135deg, #10b981, #34d399); color: white; }
.num-waiting { background: rgba(255,255,255,0.15); color: rgba(255,255,255,0.4); }

/* 面试题卡片 */
.question-card {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(12px);
    border-left: 4px solid;
    border-image: linear-gradient(180deg, #7c5ce7, #4f8cff) 1;
    border-radius: 0 16px 16px 0;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 16px rgba(80,60,180,0.06);
    transition: transform 0.2s;
}
.question-card:hover { transform: translateX(4px); }
.question-card .q-category {
    color: #7c5ce7; font-size: 0.75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.4rem;
}
.question-card .q-text { color: #2d1b69; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; line-height: 1.5; }
.question-card .q-purpose { color: #6b7db3; font-size: 0.85rem; }
.question-card .q-followup { color: #8b9dc3; font-size: 0.8rem; margin-top: 0.4rem; }

/* 文件上传区域 */
div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    border: 2px dashed rgba(99,102,241,0.25);
    padding: 0.8rem;
}
div[data-testid="stFileUploader"]:hover { border-color: rgba(99,102,241,0.5); }

/* 画像管理卡片 */
.profile-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 4px 20px rgba(80,60,180,0.06);
    margin-bottom: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
}
.profile-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(80,60,180,0.1);
}

/* Expander */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(80,60,180,0.05);
}

/* JSON展示 */
div[data-testid="stJson"] {
    background: rgba(255,255,255,0.4);
    border-radius: 12px;
    border: 1px solid rgba(99,102,241,0.1);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.4);
    border-radius: 12px 12px 0 0;
    backdrop-filter: blur(8px);
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: rgba(99,102,241,0.1);
}

/* Alert 提示 */
div[data-testid="stAlert"] { border-radius: 12px; }

/* 输入框 */
input, textarea, select {
    border-radius: 10px !important;
    border-color: rgba(99,102,241,0.2) !important;
}
input:focus, textarea:focus { border-color: #7c5ce7 !important; box-shadow: 0 0 0 2px rgba(124,92,231,0.15) !important; }

/* 匹配度条形图 */
.match-bar-card {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    border: 1px solid rgba(255,255,255,0.5);
    box-shadow: 0 2px 12px rgba(80,60,180,0.05);
}

/* 风险卡片 */
.risk-card {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    border: 1px solid rgba(255,255,255,0.5);
    box-shadow: 0 2px 12px rgba(80,60,180,0.05);
}

/* 欢迎页 Hero */
.hero-section {
    text-align: center;
    padding: 4rem 2rem;
}
.hero-section h2 {
    font-size: 2rem;
    background: linear-gradient(135deg, #7c5ce7 0%, #6366f1 50%, #4f8cff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    border: none !important;
    font-weight: 800 !important;
}
.hero-section p { color: #6b7db3; font-size: 1.1rem; }
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


def init_session_state():
    for key in ["talent_profile", "resume_profile", "assessment", "questions",
             "edited_profile", "jd_text", "resume_text", "current_profile_id",
             "manage_edit_id", "manage_mode", "scoring_session_id"]:
        if key not in st.session_state:
            st.session_state[key] = None
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "page" not in st.session_state:
        st.session_state.page = "evaluate"
    if "scoring_session_id" not in st.session_state:
        st.session_state.scoring_session_id = None


def render_profile_editor(profile, key_prefix=""):
    """可复用的画像编辑表单"""
    col1, col2, col3 = st.columns(3)
    with col1:
        profile["job_title"] = st.text_input("职位名称", value=profile.get("job_title", ""), key=f"{key_prefix}jt")
    with col2:
        profile["experience_years"] = st.number_input("经验要求(年)", value=int(profile.get("experience_years", 0)), min_value=0, max_value=30, key=f"{key_prefix}ey")
    with col3:
        profile["education"] = st.text_input("学历要求", value=profile.get("education", ""), key=f"{key_prefix}edu")

    col4, col5 = st.columns(2)
    with col4:
        profile["job_type"] = st.text_input("工作类型", value=profile.get("job_type", ""), key=f"{key_prefix}jtype")
    with col5:
        profile["location"] = st.text_input("工作地点", value=profile.get("location", ""), key=f"{key_prefix}loc")

    st.markdown("---")
    st.markdown("#### :wrench: 核心技能要求")
    rs = st.text_area("必备技能（每行一个）", value="\n".join(profile.get("required_skills", [])), height=100, key=f"{key_prefix}rs", help="每行一项技能")
    profile["required_skills"] = [s.strip() for s in rs.split("\n") if s.strip()]

    ps = st.text_area("加分技能（每行一个）", value="\n".join(profile.get("preferred_skills", [])), height=80, key=f"{key_prefix}ps")
    profile["preferred_skills"] = [s.strip() for s in ps.split("\n") if s.strip()]

    st.markdown("---")
    st.markdown("#### :clipboard: 岗位职责")
    rp = st.text_area("职责描述（每行一条）", value="\n".join(profile.get("responsibilities", [])), height=120, key=f"{key_prefix}rp")
    profile["responsibilities"] = [s.strip() for s in rp.split("\n") if s.strip()]

    st.markdown("---")
    col_s, col_t = st.columns(2)
    with col_s:
        st.markdown("#### :people_holding_hands: 软技能")
        ss = st.text_area("软技能（每行一个）", value="\n".join(profile.get("soft_skills", [])), height=80, key=f"{key_prefix}ss")
        profile["soft_skills"] = [s.strip() for s in ss.split("\n") if s.strip()]
    with col_t:
        st.markdown("#### :hammer_and_wrench: 工具/技术栈")
        ts = st.text_area("工具和技术（每行一个）", value="\n".join(profile.get("tools_technologies", [])), height=80, key=f"{key_prefix}ts")
        profile["tools_technologies"] = [s.strip() for s in ts.split("\n") if s.strip()]

    return profile


# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("# :clipboard: 简历风险评估器")
    st.markdown("---")

    # 页面导航
    st.markdown("### :compass: 导航")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button(":mag: 简历评估", use_container_width=True, type="primary" if st.session_state.page == "evaluate" else "secondary"):
            st.session_state.page = "evaluate"
            st.rerun()
    with nav_col2:
        if st.button(":file_cabinet: 画像管理", use_container_width=True, type="primary" if st.session_state.page == "manage" else "secondary"):
            st.session_state.page = "manage"
            st.session_state.manage_mode = "list"
            st.rerun()

    st.markdown("---")

    if st.session_state.page == "evaluate":
        step = st.session_state.step
        steps_info = [("上传JD & 生成画像", 1), ("查看/编辑人才画像", 2), ("上传简历 & 评估", 3), ("查看分析报告", 4)]
        for label, num in steps_info:
            if num < step:
                st.markdown(f'<div><span class="step-num num-done">✓</span><span style="color:#4CAF50;">{label}</span></div>', unsafe_allow_html=True)
            elif num == step:
                st.markdown(f'<div><span class="step-num num-active">{num}</span><strong style="color:#1a3a5c;">{label}</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div><span class="step-num num-waiting">{num}</span><span style="color:#aaa;">{label}</span></div>', unsafe_allow_html=True)
        st.markdown("---")
        if st.button(":arrows_counterclockwise: 重新开始", use_container_width=True):
            for key in INIT_KEYS:
                st.session_state[key] = None
            st.session_state.step = 1
            st.rerun()
    else:
        saved = load_all_profiles()
        st.markdown(f"### 已保存 {len(saved)} 个画像")

    st.markdown("---")
    st.markdown('<div style="text-align:center; color:rgba(255,255,255,0.4); font-size:0.75rem;">Powered by Claude AI<br>v4.1</div>', unsafe_allow_html=True)


# ======================================================================
# 简历评估页面
# ======================================================================
if st.session_state.page == "evaluate":

    # ===== 步骤1: 上传JD =====
    if st.session_state.step == 1:
        st.markdown("## :one: 上传岗位JD")

        # 快捷入口：从已保存画像选择
        saved = load_all_profiles()
        if saved:
            st.markdown("#### :zap: 快捷入口：从已保存画像开始")
            options = ["-- 不使用已有画像，新建 --"] + [f"{p['profile'].get('job_title', '未命名')} ({p['id'][:6]}... | {p.get('updated_at', '')})" for p in saved]
            choice = st.selectbox("选择已保存的画像", options, key="saved_profile_choice")
            if choice != options[0]:
                idx = options.index(choice) - 1
                if st.button(":arrow_right: 使用此画像，直接上传简历", type="primary"):
                    selected = saved[idx]
                    st.session_state.talent_profile = selected["profile"]
                    st.session_state.edited_profile = json.loads(json.dumps(selected["profile"]))
                    st.session_state.current_profile_id = selected["id"]
                    st.session_state.step = 3
                    st.rerun()
            st.markdown("---")

        st.caption("或上传新的职位描述，系统将自动提炼人才画像")
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
                    st.session_state.current_profile_id = None
                    st.session_state.step = 2
                    st.rerun()

    # ===== 步骤2: 编辑画像 =====
    elif st.session_state.step == 2:
        st.markdown("## :two: 岗位人才画像")
        st.caption("AI已根据JD生成人才画像，编辑调整后可保存或直接评估简历")

        profile = st.session_state.edited_profile
        profile = render_profile_editor(profile, key_prefix="s2_")
        st.session_state.edited_profile = profile

        with st.expander(":mag: 查看完整画像JSON"):
            st.json(profile)

        col_back, col_save, col_next = st.columns([1, 1, 1])
        with col_back:
            if st.button(":arrow_left: 返回", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with col_save:
            if st.button(":floppy_disk: 保存画像", use_container_width=True):
                pid = save_profile(profile, st.session_state.current_profile_id)
                st.session_state.current_profile_id = pid
                st.session_state.talent_profile = json.loads(json.dumps(profile))
                st.success(f"画像已保存! (ID: {pid[:8]})")
        with col_next:
            if st.button(":arrow_right: 确认画像，上传简历", type="primary", use_container_width=True):
                st.session_state.talent_profile = json.loads(json.dumps(profile))
                st.session_state.step = 3
                st.rerun()

    # ===== 步骤3: 上传简历 =====
    elif st.session_state.step == 3:
        st.markdown("## :three: 上传简历并评估")
        tp = st.session_state.talent_profile
        st.markdown(f"""
        <div class="glass-card" style="border-left:4px solid #7c5ce7;">
            <div style="font-weight:700; color:#2d1b69; font-size:1.1rem; margin-bottom:0.5rem;">📋 当前岗位: {tp.get('job_title', '未知')}</div>
            <div style="color:#6b7db3; font-size:0.9rem;">
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
        resume_mode = st.radio("简历输入方式", ["上传文件", "粘贴文本"], key="rm_s3", horizontal=True)
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

    # ===== 步骤4: 报告 =====
    elif st.session_state.step == 4:
        talent_profile = st.session_state.talent_profile
        resume_profile = st.session_state.resume_profile
        assessment = st.session_state.assessment
        questions = st.session_state.questions

        st.markdown("## :four: 评估报告")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("匹配度", f"{assessment['match_score']}%")
        with col2: st.metric("风险等级", assessment['risk_level'])
        with col3: st.metric("建议", assessment.get("recommendation", "待定"))
        with col4:
            name = resume_profile.get("name", "候选人")
            st.metric("候选人", f"{name} ({resume_profile.get('total_experience_years', 0)}年)")

        st.markdown("---")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([":bust_in_silhouette: 候选人画像", ":bar_chart: 匹配分析", ":warning: 风险报告", ":dart: 面试题目", ":page_facing_up: 岗位画像"])

        with tab1:
            cp = resume_profile
            info1, info2 = st.columns(2)
            with info1:
                st.markdown(f"""<div class="glass-card">
                    <div style="font-size:1.3rem; font-weight:800; color:#2d1b69;">{cp.get('name', '未知')}</div>
                    <div style="color:#6b7db3; margin-top:0.3rem;">{cp.get('current_job', '')} @ {cp.get('current_company', '')}</div>
                    <div style="color:#6b7db3; margin-top:0.2rem;">工作经验: {cp.get('total_experience_years', 0)} 年</div></div>""", unsafe_allow_html=True)
            with info2:
                c = cp.get("contact_info", {})
                st.markdown(f"""<div class="glass-card">
                    <div style="color:#6b7db3;">📧 {c.get('email', '未提供')}</div>
                    <div style="color:#6b7db3;">📱 {c.get('phone', '未提供')}</div>
                    <div style="color:#6b7db3;">📍 {c.get('location', '未提供')}</div></div>""", unsafe_allow_html=True)
            skills = cp.get("skills", {})
            if skills.get("technical_skills"):
                st.markdown("**技术技能:** " + " ".join([f"`{s}`" for s in skills["technical_skills"]]))
            if cp.get("work_experience"):
                st.markdown("#### 工作经历")
                for exp in cp["work_experience"]:
                    with st.expander(f"{exp.get('company', '?')} - {exp.get('position', '?')} ({exp.get('duration', '')})"):
                        for r in exp.get("responsibilities", []): st.markdown(f"- {r}")
                        for a in exp.get("achievements", []): st.markdown(f"- ✅ {a}")
            if cp.get("projects"):
                st.markdown("#### 项目经历")
                for proj in cp["projects"]:
                    with st.expander(f"{proj.get('name', '?')} ({proj.get('duration', '')})"):
                        st.write(proj.get("description", ""))
                        if proj.get("technologies"): st.markdown("技术栈: " + ", ".join(proj["technologies"]))

        with tab2:
            for item in assessment.get('match_details', []):
                score = item['score']
                color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                bar_bg = "linear-gradient(90deg, #7c5ce7, #4f8cff)" if score >= 80 else f"linear-gradient(90deg, {color}, {color})"
                st.markdown(f"""<div class="match-bar-card" style="border-left:4px solid {color};">
                    <div style="display:flex; justify-content:space-between;"><span style="font-weight:600; color:#2d1b69;">{item['dimension']}</span><span style="font-weight:800; color:{color}; font-size:1.2rem;">{score}%</span></div>
                    <div style="background:rgba(99,102,241,0.08); border-radius:6px; height:8px; margin-top:0.5rem; overflow:hidden;">
                        <div style="background:{bar_bg}; border-radius:6px; height:8px; width:{max(score,5)}%; transition:width 0.5s;"></div></div>
                    <div style="color:#6b7db3; font-size:0.9rem; margin-top:0.4rem;">{item['comment']}</div></div>""", unsafe_allow_html=True)
            if assessment.get('strengths'):
                st.markdown("#### :white_check_mark: 优势亮点")
                for s in assessment['strengths']: st.success(s)

        with tab3:
            for risk in assessment.get('risks', []):
                sev = risk.get('severity', '中')
                sc = {"高": "#ef4444", "中": "#f59e0b", "低": "#f59e0b"}.get(sev, "#f59e0b")
                st.markdown(f"""<div class="risk-card" style="border-left:4px solid {sc};">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;"><span style="font-weight:600; color:#2d1b69;">{risk['category']}</span><span style="background:{sc}; color:white; padding:2px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">{sev}</span></div>
                    <div style="color:#6b7db3;">{risk['description']}</div></div>""", unsafe_allow_html=True)
            if not assessment.get('risks'): st.success("未发现明显风险")

        with tab4:
            st.markdown("#### 面试题目清单")
            st.caption(f"共 {len(questions)} 道题目 | 三层面试法：项目深挖 → 现场设计 → 反作弊验证")
            categories = {}
            for q in questions: categories.setdefault(q.get("category", "其他"), []).append(q)
            cat_icons = {"项目深挖-架构追问": "🏗️", "项目深挖-方案选型": "⚖️", "项目深挖-数据与指标": "📊", "现场轻设计题": "📐", "技能盲区论证": "💡", "反作弊-细节压强": "🎯", "反作弊-改方案测试": "🔄", "反直觉问题": "🧠", "风险点验证": "⚠️", "压力/情景测试": "⚡"}
            for cat, qs in categories.items():
                icon = cat_icons.get(cat, "📋")
                st.markdown(f"##### {icon} {cat}（{len(qs)}题）")
                for i, q in enumerate(qs, 1):
                    fu = q.get("follow_up", "")
                    rf = q.get("red_flag", "")
                    fu_h = f'<div class="q-followup">↪️ <strong>追问:</strong> {fu}</div>' if fu else ""
                    rf_h = f'<div style="color:#d32f2f; font-size:0.8rem; margin-top:0.3rem; background:#fff5f5; padding:4px 8px; border-radius:4px;">🚩 <strong>红旗信号:</strong> {rf}</div>' if rf else ""
                    st.markdown(f'<div class="question-card"><div class="q-category">{cat}</div><div class="q-text">{i}. {q["question"]}</div><div class="q-purpose">🎯 考察点: {q["purpose"]}</div>{fu_h}{rf_h}</div>', unsafe_allow_html=True)

        with tab5:
            st.json(talent_profile)

        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button(":pencil2: 编辑画像", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with col_b:
            if st.button(":bust_in_silhouette: 换一份简历", use_container_width=True):
                st.session_state.resume_profile = st.session_state.assessment = st.session_state.questions = None
                st.session_state.step = 3
                st.rerun()
        with col_c:
            report = {"岗位画像": talent_profile, "候选人画像": resume_profile, "评估结果": assessment, "面试题目": questions}
            st.download_button(":arrow_down: 导出报告", data=json.dumps(report, ensure_ascii=False, indent=2), file_name="evaluation_report.json", mime="application/json", use_container_width=True)


# ======================================================================
# 画像管理页面
# ======================================================================
elif st.session_state.page == "manage":
    manage_mode = st.session_state.manage_mode or "list"

    if manage_mode == "list":
        st.markdown("## :file_cabinet: 人才画像管理")

        # 导入/导出
        exp_col, imp_col = st.columns(2)
        with exp_col:
            all_data = export_all_profiles()
            if all_data and all_data != "[]":
                st.download_button(":arrow_down: 导出所有画像", data=all_data, file_name="all_profiles.json", mime="application/json", use_container_width=True)
        with imp_col:
            uploaded = st.file_uploader("导入画像JSON", type=["json"], key="import_profiles", label_visibility="collapsed")
            if uploaded:
                try:
                    count = import_profiles(uploaded.read().decode("utf-8"))
                    st.success(f"成功导入 {count} 个画像")
                    st.rerun()
                except Exception as e:
                    st.error(f"导入失败: {e}")

        st.markdown("---")

        saved = load_all_profiles()
        if not saved:
            st.info("还没有保存任何画像。去「简历评估」页面创建一个吧！")
        else:
            for record in saved:
                p = record["profile"]
                pid = record["id"]
                skills_preview = ", ".join(p.get("required_skills", [])[:4])
                if len(p.get("required_skills", [])) > 4:
                    skills_preview += "..."

                st.markdown(f"""
                <div class="profile-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; color:#1a3a5c; font-size:1.1rem;">{p.get('job_title', '未命名')}</div>
                            <div style="color:#5a7a9a; font-size:0.85rem; margin-top:0.2rem;">{skills_preview}</div>
                            <div style="color:#aaa; font-size:0.75rem; margin-top:0.2rem;">经验: {p.get('experience_years', 0)}年 | 更新: {record.get('updated_at', '未知')} | ID: {pid[:8]}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button(":pencil2: 编辑", key=f"edit_{pid}", use_container_width=True):
                        st.session_state.manage_edit_id = pid
                        st.session_state.manage_mode = "edit"
                        st.rerun()
                with btn_col2:
                    if st.button(":mag: 用此画像评估简历", key=f"use_{pid}", use_container_width=True):
                        st.session_state.talent_profile = p
                        st.session_state.edited_profile = json.loads(json.dumps(p))
                        st.session_state.current_profile_id = pid
                        st.session_state.step = 3
                        st.session_state.page = "evaluate"
                        st.rerun()
                with btn_col3:
                    if st.button(":wastebasket: 删除", key=f"del_{pid}", use_container_width=True):
                        st.session_state[f"confirm_delete_{pid}"] = True

                if st.session_state.get(f"confirm_delete_{pid}"):
                    st.warning(f"确定要删除「{p.get('job_title', '未命名')}」吗？")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("确认删除", key=f"yes_del_{pid}", type="primary"):
                            delete_profile(pid)
                            st.session_state[f"confirm_delete_{pid}"] = False
                            st.success("已删除")
                            st.rerun()
                    with cc2:
                        if st.button("取消", key=f"no_del_{pid}"):
                            st.session_state[f"confirm_delete_{pid}"] = False
                            st.rerun()

                st.markdown("")

    elif manage_mode == "edit":
        pid = st.session_state.manage_edit_id
        record = load_profile(pid)
        if not record:
            st.error("画像不存在")
            st.session_state.manage_mode = "list"
            st.rerun()

        st.markdown(f"## :pencil2: 编辑画像: {record['profile'].get('job_title', '未命名')}")
        st.caption(f"ID: {pid} | 创建: {record.get('created_at', '')} | 更新: {record.get('updated_at', '')}")

        profile = record["profile"]
        profile = render_profile_editor(profile, key_prefix="mgr_")

        with st.expander(":mag: 查看完整JSON"):
            st.json(profile)

        col_back, col_save, col_use = st.columns(3)
        with col_back:
            if st.button(":arrow_left: 返回列表", use_container_width=True):
                st.session_state.manage_mode = "list"
                st.rerun()
        with col_save:
            if st.button(":floppy_disk: 保存修改", type="primary", use_container_width=True):
                update_profile(pid, profile)
                st.success("保存成功!")
        with col_use:
            if st.button(":mag: 用此画像评估简历", use_container_width=True):
                st.session_state.talent_profile = profile
                st.session_state.edited_profile = json.loads(json.dumps(profile))
                st.session_state.current_profile_id = pid
                st.session_state.step = 3
                st.session_state.page = "evaluate"
                st.rerun()
