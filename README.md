# 简历风险评估器

智能简历分析工具，基于AI技术评估简历与岗位的匹配度及潜在风险。

## 功能特性

- **人才画像提取**：从JD中自动提炼岗位人才画像，包括技能、经验、教育、软性要求等
- **简历智能分析**：解析简历文本，提取候选人背景信息
- **匹配度评估**：多维度分析简历与岗位的匹配程度
- **风险识别**：自动识别潜在风险，如技能差距、经验不足、稳定性问题等
- **面试问题生成**：基于分析结果生成针对性的面试考察问题

## 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd resume_risk_assessor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置API密钥

设置 Anthropic API 密钥：
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

或在 Windows 上：
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

## 运行应用

启动 Streamlit 应用：
```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址为 http://localhost:8501

## 使用说明

1. **上传JD**：点击左侧上传按钮，选择职位描述文件（支持TXT、PDF、DOCX格式）
2. **上传简历**：点击右侧上传按钮，选择候选人简历文件
3. **开始分析**：点击"开始分析"按钮
4. **查看结果**：
   - 人才画像详情
   - 简历分析结果
   - 匹配度评分（0-100%）
   - 风险等级（低/中/高）
   - 优势亮点
   - 风险提示
   - 面试问题建议

## 项目结构

```
resume_risk_assessor/
├── app.py                    # 主应用入口
├── jd_analyzer.py            # JD分析模块
├── resume_analyzer.py        # 简历分析模块
├── risk_assessor.py          # 风险评估模块
├── question_generator.py     # 面试问题生成模块
├── requirements.txt          # 依赖包列表
└── README.md                 # 项目说明文档
```

## 技术栈

- **前端**：Streamlit
- **AI引擎**：Anthropic Claude API
- **文档处理**：PyPDF2, python-docx
- **数据处理**：pandas, numpy

## 核心模块说明

### jd_analyzer.py
负责从职位描述中提取人才画像，使用AI分析JD文本，提取关键信息。

### resume_analyzer.py
解析简历内容，提取候选人的教育背景、工作经验、技能等信息。

### risk_assessor.py
对比岗位要求和候选人背景，计算匹配度，识别潜在风险。

### question_generator.py
基于分析结果生成针对性的面试问题，帮助HR深入了解候选人。

## 注意事项

1. 需要有效的 Anthropic API 密钥才能使用AI分析功能
2. 首次使用时会下载必要的NLTK数据
3. PDF和DOCX文件需要安装相应的解析库
4. 建议使用Chrome或Edge浏览器以获得最佳体验

## 未来改进

- 支持更多文档格式
- 添加批量简历分析功能
- 导出分析报告
- 与招聘系统集成
- 添加简历相似度对比功能

## 许可证

MIT License
