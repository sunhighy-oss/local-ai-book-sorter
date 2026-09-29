# 📚 AI 本地图书自动分类系统 (基于中图法与本地大模型)

本项目是一个完全本地化、保护隐私的电子书自动分类工具。它利用本地大模型（llama.cpp / Ollama）和关键词规则，将海量 PDF/EPUB 文件按《中国图书馆分类法》（中图法）自动整理。

## ✨ 核心特性
- **🔒 100% 本地运行**：无需联网，保护隐私。
- **📖 多格式支持**：兼容 PDF 和 EPUB。
- **🧠 混合智能决策**：AI 语义理解优先，Keyword 规则兜底。
- **🛡️ 鲁棒的异常处理**：自动隔离扫描版、加密、乱码文件。
- **📊 可视化统计**：一键生成 3 层交互式旭日图。

## 🚀 快速开始
1. 启动本地模型服务 (llama.cpp server 或 Ollama)。
2. 安装依赖：`pip3 install -r requirements.txt`
3. 将待分类文件放入 `input_pdfs/` 目录。
4. 运行分类：`python3 clc_classify.py`
5. 查看统计：`python3 analyze_log.py`
