# 智能知识库问答系统

基于 RAG（检索增强生成）技术的智能知识库问答系统。

## 功能特性

- 📄 支持多种文档格式（TXT、PDF、DOCX）
- 🔍 基于向量数据库的语义检索
- 💬 自然语言问答
- 📚 多轮对话记忆
- 🌐 美观的 Web 交互界面
- 🔄 动态索引更新

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 OpenAI API（可选）

本系统支持两种模式：
- **完整模式**：需要 OpenAI API Key，支持 GPT 模型
- **离线模式**：无需 API Key，使用关键词匹配

如需使用完整模式，请设置环境变量：

```bash
# Windows
set OPENAI_API_KEY=your-api-key

# Linux/Mac
export OPENAI_API_KEY=your-api-key
```

或者在代码中直接修改 `rag_core.py` 中的配置。

## 运行项目

### 启动服务器

```bash
python app.py
```

服务器启动后，访问 http://localhost:5000

### 使用方法

1. **上传文档**：点击上传按钮，选择 TXT、PDF 或 DOCX 格式的文档
2. **开始问答**：在输入框中输入问题，系统会从已上传的文档中检索答案
3. **查看来源**：答案会显示参考的文档来源

## 项目结构

```
knowledge_base_qa/
├── app.py                 # Flask Web 应用
├── rag_core.py            # RAG 核心引擎
├── requirements.txt       # Python 依赖
├── templates/
│   └── index.html        # 前端页面
├── knowledge_base/        # 文档存储目录
│   └── sample.txt         # 示例文档
└── vector_store/          # 向量数据库存储
```

## 技术栈

- **后端**：Flask
- **RAG 引擎**：LangChain
- **向量数据库**：ChromaDB
- **嵌入模型**：OpenAI Embeddings
- **前端**：HTML + CSS + JavaScript

## 示例问题

- 这篇文章的主要内容是什么？
- 请总结文档中的关键点
- 文档中提到了哪些重要概念？

## 注意事项

- 首次上传文档时，系统会自动进行向量化处理
- 离线模式下，系统使用关键词匹配，答案可能不够精确
- 建议单个文档大小不超过 10MB

## 故障排除

### 问题：ImportError 相关错误

确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### 问题：向量数据库错误

删除 `vector_store` 目录后重启：
```bash
rm -rf vector_store
python app.py
```

### 问题：上传文档失败

- 检查 `knowledge_base` 目录是否存在
- 确保文件格式受支持
- 检查文件大小是否超过限制
