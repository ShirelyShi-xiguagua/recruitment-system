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

# 自定义CSS样式
st.markdown("""
<style>
/* 侧边栏浅蓝渐变 */
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

/* 主内容区域 */
.main .block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* 卡片样式 */
div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #d0e4f5;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* metric 卡片 */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #f0f7ff 0%, #e0efff 100%);
    border: 1px solid #c4daf0;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
div[data-testid="stMetric"] label {
    color: #1a3a5c !important;
    font-weight: 600 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #0d47a1 !important;
    font-size: 2rem !important;
}

/* 按钮样式 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    border: none;
    border-radius: 8px;
    padding: 0.6rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    box-shadow: 0 3px 10px rgba(33,150,243,0.3);
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 5px 15px rgba(33,150,243,0.4);
    transform: translateY(-1px);
}

/* 成功/警告/错误提示 */
div[data-testid="stAlert"] {
    border-radius: 8px;
}

/* 标题样式 */
h1 {
    color: #1a3a5c;
    font-weight: 700;
}
h2 {
    color: #1e4976;
    border-bottom: 2px solid #e0efff;
    padding-bottom: 0.5rem;
}

/* JSON 展示 */
div[data-testid="stJson"] {
    background: #f8fbff;
    border-radius: 8px;
    border: 1px solid #e0efff;
}

/* 分割线 */
hr {
    border-color: #d0e4f5;
}

/* 问题卡片 */
.question-card {
    background: linear-gradient(135deg, #f8fbff 0%, #f0f6ff 100%);
    border-left: 4px solid #2196F3;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.question-card .q-category {
    color: #1976D2;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.3rem;
}
.question-card .q-text {
    color: #1a3a5c;
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
}
.question-card .q-purpose {
    color: #5a7a9a;
    font-size: 0.85rem;
    font-style: italic;
}
.question-card .q-followup {
    color: #7a9aba;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}

/* 上传区域 */
div[data-testid="stFileUploader"] {
    background: #f8fbff;
    border-radius: 8px;
    border: 2px dashed #b3d9ff;
    padding: 0.5rem;
}

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1.5rem;
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
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            st.error(f"PDF解析失败: {e}")
            return ""

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            st.error(f"DOCX解析失败: {e}")
            return ""

    return raw.decode("utf-8", errors="replace")


# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("# :clipboard: 简历风险评估器")
    st.markdown("---")

    st.markdown("### :pushpin: 功能模块")
    st.markdown("""
    - :mag: **人才画像提取**
    - :bust_in_silhouette: **简历智能分析**
    - :bar_chart: **匹配度评估**
    - :warning: **风险识别**
    - :dart: **面试题目生成**
    """)

    st.markdown("---")
    st.markdown("### :page_facing_up: 上传岗位JD")
    jd_mode = st.radio("输入方式", ["上传文件", "粘贴文本"], key="jd_mode", horizontal=True)
    if jd_mode == "上传文件":
        jd_file = st.file_uploader("选择JD文件", type=["txt", "pdf", "docx"], key="jd", label_visibility="collapsed")
        jd_text = read_uploaded_file(jd_file) if jd_file else ""
    else:
        jd_text = st.text_area("粘贴JD内容", height=200, key="jd_text", placeholder="请粘贴职位描述...")
    if jd_text:
        st.success(f"JD已就绪 ({len(jd_text)} 字)")

    st.markdown("---")
    st.markdown("### :bust_in_silhouette: 上传简历")
    resume_mode = st.radio("输入方式", ["上传文件", "粘贴文本"], key="resume_mode", horizontal=True)
    if resume_mode == "上传文件":
        resume_file = st.file_uploader("选择简历文件", type=["txt", "pdf", "docx"], key="resume", label_visibility="collapsed")
        resume_text = read_uploaded_file(resume_file) if resume_file else ""
    else:
        resume_text = st.text_area("粘贴简历内容", height=200, key="resume_text", placeholder="请粘贴简历内容...")
    if resume_text:
        st.success(f"简历已就绪 ({len(resume_text)} 字)")

    st.markdown("---")
    start_btn = st.button(":rocket: 开始分析", type="primary", use_container_width=True, disabled=not (jd_text and resume_text))

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#5a7a9a; font-size:0.8rem;">
        Powered by Claude AI<br>
        v2.0
    </div>
    """, unsafe_allow_html=True)


# ===== 主内容区 =====
st.markdown("# :bar_chart: 分析结果")

if not (jd_text and resume_text):
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem; color:#8aa8c8;">
        <div style="font-size:4rem; margin-bottom:1rem;">:arrow_left:</div>
        <h3 style="color:#5a7a9a;">请在左侧上传JD和简历</h3>
        <p>支持 TXT / PDF / DOCX 格式，也可以直接粘贴文本</p>
    </div>
    """, unsafe_allow_html=True)

if start_btn and jd_text and resume_text:
    try:
        # ===== 步骤1: 人才画像 =====
        with st.status(":mag: 正在提炼岗位人才画像...", expanded=True) as status:
            talent_profile = extract_talent_profile(jd_text)
            status.update(label=":white_check_mark: 人才画像提取完成", state="complete", expanded=False)

        # ===== 步骤2: 简历分析 =====
        with st.status(":bust_in_silhouette: 正在分析简历...", expanded=True) as status:
            resume_profile = extract_resume_profile(resume_text)
            status.update(label=":white_check_mark: 简历分析完成", state="complete", expanded=False)

        # ===== 步骤3: 匹配评估 =====
        with st.status(":bar_chart: 正在评估匹配度...", expanded=True) as status:
            assessment = assess_match_and_risks(talent_profile, resume_profile)
            status.update(label=":white_check_mark: 匹配评估完成", state="complete", expanded=False)

        # ===== 步骤4: 面试题 =====
        with st.status(":dart: 正在生成面试题目...", expanded=True) as status:
            questions = generate_interview_questions(talent_profile, resume_profile, assessment)
            status.update(label=":white_check_mark: 面试题目生成完成", state="complete", expanded=False)

        st.markdown("---")

        # ===== 概览卡片 =====
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("匹配度", f"{assessment['match_score']}%", delta=assessment.get('match_trend', ''))
        with col2:
            risk_level = assessment['risk_level']
            icon = {"低": ":green_circle:", "中": ":yellow_circle:", "高": ":red_circle:"}.get(risk_level, "")
            st.metric("风险等级", f"{risk_level}", delta=icon)
        with col3:
            st.metric("建议", assessment.get("recommendation", "待定"))

        st.markdown("---")

        # ===== Tabs =====
        tab1, tab2, tab3, tab4 = st.tabs([":page_facing_up: 人才画像", ":bar_chart: 匹配分析", ":warning: 风险报告", ":dart: 面试题目"])

        with tab1:
            col_jd, col_resume = st.columns(2)
            with col_jd:
                st.markdown("#### 岗位画像")
                st.json(talent_profile)
            with col_resume:
                st.markdown("#### 候选人画像")
                st.json(resume_profile)

        with tab2:
            st.markdown("#### 多维匹配分析")
            for item in assessment.get('match_details', []):
                score = item['score']
                color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 60 else "#F44336"
                st.markdown(f"""
                <div style="background:white; border-radius:8px; padding:0.8rem 1rem; margin-bottom:0.6rem; border-left:4px solid {color}; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:600; color:#1a3a5c;">{item['dimension']}</span>
                        <span style="font-weight:700; color:{color}; font-size:1.2rem;">{score}%</span>
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
            st.caption(f"共 {len(questions)} 道题目，按类别分组展示")

            categories = {}
            for q in questions:
                cat = q.get("category", "其他")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(q)

            cat_icons = {
                "项目经历深挖": ":mag:",
                "经历真实性验证": ":mag:",
                "岗位技能实操": ":wrench:",
                "核心能力考察": ":wrench:",
                "技能盲区论证": ":bulb:",
                "风险点验证": ":warning:",
                "风险点深挖": ":warning:",
                "压力/情景测试": ":zap:",
                "岗位匹配验证": ":dart:",
            }

            for cat, qs in categories.items():
                icon = cat_icons.get(cat, ":clipboard:")
                st.markdown(f"##### {icon} {cat}（{len(qs)}题）")
                for i, q in enumerate(qs, 1):
                    follow_up = q.get("follow_up", "")
                    follow_html = f'<div class="q-followup">:arrow_right_hook: 追问: {follow_up}</div>' if follow_up else ""
                    st.markdown(f"""
                    <div class="question-card">
                        <div class="q-category">{cat}</div>
                        <div class="q-text">{i}. {q['question']}</div>
                        <div class="q-purpose">:dart: 考察点: {q['purpose']}</div>
                        {follow_html}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("")

    except Exception as e:
        st.error(f"分析过程中出现错误: {str(e)}")
        st.exception(e)
