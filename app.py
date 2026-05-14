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
    layout="wide"
)

st.title(":clipboard: 简历风险评估器")

st.markdown("""
上传职位描述(JD)和简历，系统将：
1. 提炼岗位人才画像
2. 分析简历匹配度
3. 评估潜在风险
4. 生成面试考察问题
""")


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


col1, col2 = st.columns(2)

with col1:
    st.subheader(":page_facing_up: 职位描述 (JD)")
    jd_input_mode = st.radio("JD输入方式", ["上传文件", "粘贴文本"], key="jd_mode", horizontal=True)
    if jd_input_mode == "上传文件":
        jd_file = st.file_uploader("上传JD文档", type=["txt", "pdf", "docx"], key="jd")
        jd_text = read_uploaded_file(jd_file) if jd_file else ""
    else:
        jd_text = st.text_area("粘贴JD内容", height=300, key="jd_text")
    if jd_text:
        st.success("JD已就绪")

with col2:
    st.subheader(":bust_in_silhouette: 简历")
    resume_input_mode = st.radio("简历输入方式", ["上传文件", "粘贴文本"], key="resume_mode", horizontal=True)
    if resume_input_mode == "上传文件":
        resume_file = st.file_uploader("上传简历文档", type=["txt", "pdf", "docx"], key="resume")
        resume_text = read_uploaded_file(resume_file) if resume_file else ""
    else:
        resume_text = st.text_area("粘贴简历内容", height=300, key="resume_text")
    if resume_text:
        st.success("简历已就绪")

if st.button("开始分析", type="primary", disabled=not (jd_text and resume_text)):
    with st.spinner("正在分析..."):
        try:
            with st.status("正在提炼人才画像...", expanded=True) as status:
                talent_profile = extract_talent_profile(jd_text)
                st.json(talent_profile)
                status.update(label="人才画像提取完成!", state="complete", expanded=False)

            with st.status("正在分析简历...", expanded=True) as status:
                resume_profile = extract_resume_profile(resume_text)
                st.json(resume_profile)
                status.update(label="简历分析完成!", state="complete", expanded=False)

            with st.status("正在评估匹配度和风险...", expanded=True) as status:
                assessment = assess_match_and_risks(talent_profile, resume_profile)
                status.update(label="风险评估完成!", state="complete", expanded=False)

            with st.status("正在生成面试问题...", expanded=True) as status:
                questions = generate_interview_questions(talent_profile, resume_profile, assessment)
                status.update(label="问题生成完成!", state="complete", expanded=False)

            st.markdown("---")

            col_match, col_risk = st.columns(2)
            with col_match:
                st.metric("匹配度", f"{assessment['match_score']}%", delta=assessment.get('match_trend', ''))
            with col_risk:
                risk_level = assessment['risk_level']
                icon = {"低": ":green_circle:", "中": ":yellow_circle:", "高": ":red_circle:"}.get(risk_level, "")
                st.metric("风险等级", f"{icon} {risk_level}")

            st.markdown("## :bar_chart: 匹配度分析")
            for item in assessment.get('match_details', []):
                st.write(f"- **{item['dimension']}**: {item['score']}% - {item['comment']}")

            st.markdown("## :warning: 风险提示")
            for risk in assessment.get('risks', []):
                st.warning(f"**{risk['category']}**: {risk['description']} (严重程度: {risk['severity']})")

            st.markdown("## :white_check_mark: 优势亮点")
            for strength in assessment.get('strengths', []):
                st.success(f"- {strength}")

            st.markdown("## :dart: 建议面试问题")
            for q in questions:
                st.write(f"**{q['category']}**")
                st.write(f"- {q['question']}")
                st.write(f"  *考察点: {q['purpose']}*")
                st.write("")

        except Exception as e:
            st.error(f"分析过程中出现错误: {str(e)}")
            st.exception(e)

st.markdown("---")
st.caption("使用 Anthropic Claude API 进行智能分析")
