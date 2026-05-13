"""
简历风险评估器 - 示例测试脚本
"""

# 示例JD文本
SAMPLE_JD = """
职位：高级软件工程师

职责：
- 负责核心系统的设计和开发
- 参与技术架构决策
- 指导 junior 工程师成长

技能要求：
- Python/Java/Go 至少精通一门
- 熟悉微服务架构
- 有高并发系统设计经验
- 熟悉 MySQL、Redis、Kafka 等中间件
- 了解 Docker、Kubernetes 等容器化技术

任职要求：
- 本科及以上学历，计算机相关专业
- 5年以上软件开发经验
- 有团队管理经验优先
- 有大型互联网公司工作经验优先

软技能：
- 良好的沟通能力
- 团队协作精神
- 问题解决能力
- 学习能力强
"""

# 示例简历文本
SAMPLE_RESUME = """
姓名：张三
邮箱：zhangsan@example.com
电话：138-1234-5678

个人总结：
拥有6年软件开发经验，精通 Python 和 Java，有丰富的高并发系统开发经验。善于沟通，具有团队合作精神。

工作经历：
高级软件工程师 | ABC科技公司 | 2020 - 至今
- 负责电商平台核心系统开发
- 参与微服务架构设计
- 带领3人团队完成多个项目

软件工程师 | XYZ互联网公司 | 2017 - 2020
- 参与 OA 系统开发
- 使用 Django 框架开发后端服务

教育背景：
本科 计算机科学与技术 | 清华大学 | 2013 - 2017

技能：
- Python, Java, JavaScript
- Django, Spring Boot
- MySQL, Redis, MongoDB
- Docker, Kubernetes
- AWS, Azure

证书：
- AWS Certified Solutions Architect
- PMP 项目管理专业人士

项目经验：
电商平台重构项目（2022-2023）
- 技术栈：Python, Kafka, Redis, Docker
- 职责：负责订单系统重构
"""

if __name__ == "__main__":
    from jd_analyzer import extract_talent_profile
    from resume_analyzer import extract_resume_profile
    from risk_assessor import assess_match_and_risks
    from question_generator import generate_interview_questions

    print("=" * 50)
    print("简历风险评估器 - 示例测试")
    print("=" * 50)

    print("\n1. 正在提取岗位人才画像...")
    talent_profile = extract_talent_profile(SAMPLE_JD)
    print(f"职位：{talent_profile.get('job_title', 'N/A')}")
    print(f"经验要求：{talent_profile.get('experience_years', 0)} 年")

    print("\n2. 正在分析简历...")
    resume_profile = extract_resume_profile(SAMPLE_RESUME)
    print(f"姓名：{resume_profile.get('name', 'N/A')}")
    print(f"当前职位：{resume_profile.get('current_job', 'N/A')}")
    print(f"工作经验：{resume_profile.get('total_experience_years', 0)} 年")

    print("\n3. 正在评估匹配度和风险...")
    assessment = assess_match_and_risks(talent_profile, resume_profile)
    print(f"匹配度：{assessment['match_score']}%")
    print(f"风险等级：{assessment['risk_level']}")
    print(f"建议：{assessment['recommendation']}")

    print("\n4. 正在生成面试问题...")
    questions = generate_interview_questions(talent_profile, resume_profile, assessment)
    print(f"生成了 {len(questions)} 个面试问题")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
