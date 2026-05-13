import streamlit as st
import os
import json
from jd_analyzer import extract_talent_profile
from resume_analyzer import extract_resume_profile
from risk_assessor import assess_match_and_risks
from question_generator import generate_interview_questions

# 设置页面配置
st.set_page_config(
    page_title="简历风险评估器",
    page_icon=":clipboard:",
    layout="wide"
)

st.title("📋 简历风险评估器")

st.markdown("""
    上传职位描述(JD)和简历，系统将：
    1. 提炼岗位人才画像
    2. 分析简历匹配度
    3. 评估潜在风险
    4. 生成面试考察问题
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader(":page_facing_up: 职位描述 (JD)")
    jd_file = st.file_uploader("上传JD文档", type=['txt', 'pdf', 'docx'], key='jd')
    if jd_file:
        st.success(f"已上传: {jd_file.name}")
        jd_text = jd_file.read().decode('utf-8')
    else:
        jd_text = ""

with col2:
    st.subheader("👤 简历")
    resume_file = st.file_uploader("上传简历文档", type=['txt', 'pdf', 'docx'], key='resume')
    if resume_file:
        st.success(f"已上传: {resume_file.name}")
        resume_text = resume_file.read().decode('utf-8')
    else:
        resume_text = ""

if st.button("开始分析", type="primary") and jd_text and resume_text:
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
                st.metric("匹配度", f"{assessment['match_score']}%", delta=assessment['match_trend'])

            with col_risk:
                risk_level = assessment['risk_level']
                risk_color = "🟢" if risk_level == "低" else "🟡" if risk_level == "中" else "🔴"
                st.metric("风险等级", f"{risk_color} {risk_level}")

            st.markdown("## 📊 匹配度分析")
            for item in assessment['match_details']:
                st.write(f"- **{item['dimension']}**: {item['score']}% - {item['comment']}")

            st.markdown("## ⚠️ 风险提示")
            for risk in assessment['risks']:
                st.warning(f"**{risk['category']}**: {risk['description']} (严重程度: {risk['severity']})")

            st.markdown("## ✅ 优势亮点")
            for strength in assessment['strengths']:
                st.success(f"- {strength}")

            st.markdown("## 🎯 建议面试问题")
            for i, q in enumerate(questions, 1):
                st.write(f"**{q['category']}**")
                st.write(f"- {q['question']}")
                st.write(f"  *考察点: {q['purpose']}*")
                st.write("")

        except Exception as e:
            st.error(f"分析过程中出现错误: {str(e)}")
            st.exception(e)

st.markdown("---")
st.caption("使用 Anthropic Claude API 进行智能分析")
