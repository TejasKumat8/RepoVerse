# RepoMind AI — Your AI Pair Programmer for Any GitHub Repository 🚀

> **Chat with any GitHub repository. Understand any codebase in minutes using Retrieval-Augmented Generation (RAG) & Multi-LLM Reasoning.**

![RepoMind AI Banner](https://img.shields.io/badge/RepoMind%20AI-v1.2.0-00f0ff?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![RAG Engine](https://img.shields.io/badge/RAG-Vector%20Embeddings-8A2BE2?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![CI/CD](https://img.shields.io/badge/GitHub%20Actions-Passing-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

---

## 🧠 Problem Statement

Developers joining a new project or auditing unfamiliar repositories often spend hours tracing dependencies, finding entry points, and understanding complex business logic. 

**RepoMind AI** solves this by downloading and parsing any public GitHub repository, extracting vector embeddings, and allowing developers to ask natural language questions grounded in exact source code lines and live repository metadata.

---

## 🎯 Key Features & Capabilities

### 1. 📥 GitHub Repository Auto-Importer & Live Metadata Fetcher
- Paste any public GitHub repository URL or slug (`owner/repo`).
- Dynamically fetches **Created Date**, **Total Stars**, **Total Forks**, **Open Issues**, and **Repository Description** via GitHub REST API.
- Supports fine-grained GitHub Personal Access Tokens for high rate-limits.

### 2. ⚡ Line-Aware Code Parser & Chunking Engine
- Automatically ignores build noise (`node_modules`, `.git`, `dist`, binaries, lockfiles).
- Supports multi-language code parsing (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.md`, `.sql`, etc.).
- Tracks precise start/end line numbers (`[src/auth.py:L12-L45]`) for citations.

### 3. 🧠 RAG Vector Embedding & Keyword Boost Engine
- Uses TF-IDF vectorization with n-gram feature extraction.
- Keyword relevance boosting for fast, deterministic code snippet retrieval.

### 4. 🤖 Multi-LLM AI Pair Programmer Chat
- Support for **Google Gemini 1.5/2.0**, **Groq (Llama 3.3 70B)**, **OpenAI (gpt-4o-mini)**, and built-in **Offline RAG Synthesizer**.
- Automatic Cloudflare bypass & quota fallback to ensure uninterrupted chat.

### 5. 🛡️ Codebase Health & Bug-Prone Risk Analyzer (Stretch Feature)
- Runs static cyclomatic complexity analysis across indexed files.
- Flags high-risk/complex files and extracts `TODO`, `FIXME`, and `XXX` markers.

### 6. 📝 Auto-Generate README.md (Stretch Feature)
- Instantly generates comprehensive `README.md` documentation for any repository using RAG analysis.

### 7. 🗺️ Interactive Folder Explorer & Architecture Diagrams
- Render 2-level interactive folder tree structure.
- Generate dynamic Mermaid.js architecture flowcharts.

---

## 🏗️ Architecture Overview

```
                          ┌───────────────────────────┐
                          │   🌐 User Web Interface   │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   🔀 FastAPI REST API    │
                          └─────────────┬─────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
  ┌──────────────────┐       ┌────────────────────┐      ┌──────────────────┐
  │ GitHub Importer  │       │  RAG Vector Store  │      │ Multi-LLM Engine │
  │ & Metadata Sync  │       │ (TF-IDF + Cosine)  │      │ (Gemini/Groq/OA) │
  └──────────────────┘       └────────────────────┘      └──────────────────┘
```

---

## 📂 Project Structure

```
repomind-ai/
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD Pipeline
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI REST endpoints & routes
│   ├── core/
│   │   └── config.py              # Settings & environment config
│   ├── llm/
│   │   └── llm_service.py         # Gemini, Groq, OpenAI & Offline RAG Engine
│   ├── parser/
│   │   └── code_parser.py         # Code crawler & line-aware chunker
│   ├── rag/
│   │   └── vector_store.py        # Vector embedding index & cosine search
│   ├── services/
│   │   ├── github_service.py      # GitHub repo downloader & metadata fetcher
│   │   └── summary_service.py     # Tech stack detector & tree builder
│   └── static/
│       ├── app.js                 # Interactive frontend logic & chat UI
│       ├── index.html             # Glassmorphism dark mode Web UI
│       └── styles.css             # Cyberpunk design system
│
├── storage/                       # Local repo code cache & vector store
├── Dockerfile                     # Docker container definition
├── docker-compose.yml             # Docker Compose orchestrator
├── .env                           # Environment configuration
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## ⚡ Quick Start

### Option A: Local Run (Python)

1. **Clone repository:**
   ```bash
   git clone https://github.com/TejasKumat8/RepoMind.git
   cd RepoMind
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Web Server:**
   ```bash
   python main.py
   ```
   Open browser at: `http://127.0.0.1:8000`

---

### Option B: Docker Compose (1-Click Launch) 🐳

```bash
docker-compose up -d
```
Open browser at: `http://127.0.0.1:8000`

---

## ⭐ Resume & Portfolio Description

> **RepoMind AI — Your AI Pair Programmer for Any GitHub Repository**
> Designed and built RepoMind AI, an enterprise-grade LLM-powered codebase intelligence platform that enables developers to query any GitHub repository using Retrieval-Augmented Generation (RAG), vector embeddings, and static code complexity analysis. Integrated support for Google Gemini, Groq (Llama 3.3), and OpenAI APIs alongside an offline RAG synthesizer. Added automatic GitHub metadata extraction, interactive Mermaid architecture diagrams, and 1-click README generation. Containerized with Docker and automated via GitHub Actions CI/CD.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
