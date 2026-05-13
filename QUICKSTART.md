# 快速开始指南

## 1. 获取 API 密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册或登录账户
3. 在 API Keys 页面创建新的 API 密钥
4. 复制��钥并妥善保存

## 2. 配置环境变量

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

**Windows (命令提示符):**
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

或创建 `.env` 文件：
```
ANTHROPIC_API_KEY=your-api-key-here
```

## 3. 安装依赖

```bash
pip install -r requirements.txt
```

或使用启动脚本（自动创建虚拟环境并安装依赖）：

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

## 4. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：http://localhost:8501

## 5. 使用应用

1. 上传职位描述 (JD)
2. 上传候选人简历
3. 点击"开始分析"按钮
4. 查看分析结果和面试问题建议

## 测试示例

运行示例测试（不需要上传文件）：

```bash
python test_sample.py
```

这将使用内置的示例 JD 和简历进行测试。

## 常见问题

### Q: 提示 API 密钥错误
A: 检查 `ANTHROPIC_API_KEY` 环境变量是否正确设置。

### Q: 支持哪些文件格式？
A: 支持 TXT、PDF、DOCX 格式的文件。

### Q: 分析速度慢怎么办？
A: 这是正常的，因为需要调用 AI API。您可以尝试使用更小的文件或减少分析维度。

### Q: 如何批量分析简历？
A: 当前版本仅支持单个简历分析。批量分析功能正在开发中。

## 下一步

- 查看 [README.md](README.md) 了解更多详细信息
- 根据需要自定义配置文件
- 探索源代码以了解实现细节
