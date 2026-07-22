# RepoMind AI — Your AI Pair Programmer for Any GitHub Repository 🚀

> **Chat with any GitHub repository. Understand any codebase in minutes using AI.**

![RepoMind AI Banner](https://img.shields.io/badge/RepoMind%20AI-v1.0.0-00f0ff?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-Vector%20Embeddings-8A2BE2?style=for-the-badge)

---

## 🧠 Problem Statement

Developers joining a new project often spend hours or even days understanding an unfamiliar codebase. Finding where a feature is implemented, understanding architecture, or tracing business logic is slow and frustrating.

**RepoMind AI** solves this by allowing developers to ask natural language questions about any GitHub repository and receive accurate, context-aware answers grounded in the repository's actual source code.

---

## 🎯 Key Features

1. **GitHub Repository Importer**:
   - Paste any public GitHub repository URL or slug (`owner/repo`).
   - Downloads, extracts, and indexes the entire codebase automatically.
   - Fine-grained GitHub Personal Access Token support for high rate-limits.

2. **Smart Code Parser & Line Chunker**:
   - Filters out build noise (`node_modules`, `.git`, `dist`, binaries, lockfiles).
   - Multi-language support (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.md`, `.sql`, etc.).
   - Tracks exact file starting and ending line numbers (`[file.py:L12-L45]`).

3. **RAG Pipeline & Vector Embedding Engine**:
   - Generates vector embeddings for all code chunks.
   - Cosine similarity vector search engine returning top relevant code context.

4. **Multi-LLM AI Pair Programmer Chat**:
   - Integrated support for **Google Gemini 1.5**, **OpenAI (gpt-4o-mini)**, **Groq (Llama 3.3)**, or built-in offline smart RAG context synthesis.
   - Formatted markdown responses with code copy buttons and clickable line citation badges.

5. **Repository Intelligence Overview**:
   - Automatic Tech Stack detection.
   - Metrics (Total files, lines of code, top languages).
   - Interactive codebase folder tree explorer.
   - Important entry points detection (`main.py`, `app.py`, `index.js`, `server.ts`, etc.).

6. **1-Click Code Inspector & Mermaid Diagram Visualizer**:
   - Clicking any file citation badge opens the raw source file modal with syntax highlighting.
   - Generates interactive Mermaid.js architecture flowcharts.

---

## 📂 Project Structure

```
repomind-ai/
│
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI REST endpoints
│   ├── core/
│   │   └── config.py              # Settings & environment configuration
│   ├── llm/
│   │   └── llm_service.py         # Multi-LLM provider integration (Gemini/OpenAI/Groq/Local)
│   ├── parser/
│   │   └── code_parser.py         # Code crawler & line-aware chunker
│   ├── rag/
│   │   └── vector_store.py        # Vector embedding index & cosine search engine
│   ├── services/
│   │   ├── github_service.py      # GitHub repo downloader & extractor
│   │   └── summary_service.py     # Tech stack detector & folder tree generator
│   └── static/
│       ├── app.js                 # Interactive frontend logic & chat engine
│       ├── index.html             # Glassmorphism dark mode Web UI
│       └── styles.css             # Cyberpunk design system stylesheet
│
├── storage/                       # Local repository storage & vector indices
├── .env                           # Environment configuration
├── main.py                        # FastAPI application server entry point
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## ⚡ Quick Start

### 1. Requirements
- Python 3.10+

### 2. Launch Server
```bash
python main.py
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## ⭐ Resume Description

> **RepoMind AI — Your AI Pair Programmer for Any GitHub Repository**
> Built RepoMind AI, an LLM-powered GitHub repository assistant that enables developers to chat with any public codebase using Retrieval-Augmented Generation (RAG), semantic search, and vector embeddings. The system analyzes repositories, retrieves relevant code context, and provides accurate explanations with source file references.
