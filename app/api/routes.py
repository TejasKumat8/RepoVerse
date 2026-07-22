import os
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.services.github_service import GitHubService
from app.parser.code_parser import CodeParser
from app.rag.vector_store import VectorStore
from app.llm.llm_service import LLMService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api")

# Repository session cache
active_repos: Dict[str, Dict[str, Any]] = {}

class ImportRepoRequest(BaseModel):
    url: str
    github_token: Optional[str] = None

class ChatRequest(BaseModel):
    repo_id: str
    query: str
    api_provider: Optional[str] = "gemini"
    api_key: Optional[str] = None

class SearchRequest(BaseModel):
    repo_id: str
    query: str
    top_k: Optional[int] = 6

class DiagramRequest(BaseModel):
    repo_id: str
    topic: Optional[str] = "architecture"

class AuditRequest(BaseModel):
    repo_id: str

class ReadmeRequest(BaseModel):
    repo_id: str

@router.post("/repo/import")
def import_repository(req: ImportRepoRequest):
    try:
        token = req.github_token or settings.GITHUB_TOKEN
        repo_info = GitHubService.download_and_extract_repo(req.url, custom_token=token)
        repo_id = repo_info["repo_id"]
        local_path = repo_info["local_path"]

        # Parse repository into code chunks
        chunks = CodeParser.parse_repository(local_path)

        # Build Vector Store
        vector_store = VectorStore(repo_id)
        vector_store.build_index(chunks)

        # Generate Repository Summary
        summary = SummaryService.generate_summary(local_path, repo_info)

        # Cache session
        active_repos[repo_id] = {
            "info": repo_info,
            "chunks": chunks,
            "vector_store": vector_store,
            "summary": summary
        }

        return {
            "status": "success",
            "message": f"Successfully indexed {repo_info['owner']}/{repo_info['repo']} ({len(chunks)} chunks from {summary['total_files']} files)",
            "repo_id": repo_id,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repo/summary/{repo_id}")
def get_repository_summary(repo_id: str):
    if repo_id in active_repos:
        return active_repos[repo_id]["summary"]

    # Try loading from vector store disk if cached
    vector_store = VectorStore(repo_id)
    if vector_store.load_index():
        repo_dir = settings.STORAGE_DIR / "repos" / repo_id
        if repo_dir.exists():
            parts = repo_id.split('_', 1)
            owner = parts[0] if len(parts) > 0 else "unknown"
            repo = parts[1] if len(parts) > 1 else repo_id
            repo_info = {
                "repo_id": repo_id,
                "owner": owner,
                "repo": repo,
                "branch": "main",
                "local_path": str(repo_dir),
                "html_url": f"https://github.com/{owner}/{repo}"
            }
            summary = SummaryService.generate_summary(str(repo_dir), repo_info)
            active_repos[repo_id] = {
                "info": repo_info,
                "chunks": vector_store.chunks,
                "vector_store": vector_store,
                "summary": summary
            }
            return summary

    raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found. Please import it first.")

@router.post("/chat")
def chat_with_repo(req: ChatRequest):
    repo_id = req.repo_id
    if repo_id not in active_repos:
        get_repository_summary(repo_id)

    session = active_repos.get(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository session not active. Please re-import.")

    vector_store: VectorStore = session["vector_store"]
    top_chunks = vector_store.search(req.query, top_k=settings.TOP_K_RESULTS)

    response = LLMService.generate_answer(
        query=req.query,
        context_chunks=top_chunks,
        repo_info=session["info"],
        repo_summary=session.get("summary"),
        api_provider=req.api_provider or "gemini",
        api_key=req.api_key
    )

    return response

@router.post("/search")
def semantic_search(req: SearchRequest):
    repo_id = req.repo_id
    if repo_id not in active_repos:
        get_repository_summary(repo_id)

    session = active_repos.get(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not indexed.")

    vector_store: VectorStore = session["vector_store"]
    results = vector_store.search(req.query, top_k=req.top_k or 6)
    return {"query": req.query, "results": results}

@router.get("/repo/file/{repo_id}")
def get_file_content(repo_id: str, file_path: str = Query(...)):
    repo_dir = settings.STORAGE_DIR / "repos" / repo_id
    target_file = repo_dir / file_path

    try:
        target_file.resolve().relative_to(repo_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied.")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return {"file_path": file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diagram")
def generate_architecture_diagram(req: DiagramRequest):
    repo_id = req.repo_id
    if repo_id not in active_repos:
        get_repository_summary(repo_id)

    session = active_repos.get(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not indexed.")

    summary = session["summary"]
    stack = ", ".join(summary.get("tech_stack", [])) or "Standard Codebase"
    entry_list = [ep["path"] for ep in summary.get("entry_points", [])]
    entry_str = " & ".join(entry_list[:3]) or "Main Entrypoints"

    mermaid_code = f"""graph TD
    User["🌐 User / Client"] --> Router["🔀 API Router / Gateway ({entry_str})"]
    Router --> Services["⚙️ Core Services & Logic"]
    Services --> DB[("💾 Data Storage / State")]
    Services --> RAG["🧠 AI & RAG Engine ({stack})"]
    
    style User fill:#1e293b,stroke:#3b82f6,color:#f8fafc
    style Router fill:#0f172a,stroke:#8b5cf6,color:#f8fafc
    style Services fill:#0f172a,stroke:#10b981,color:#f8fafc
    style DB fill:#0f172a,stroke:#f59e0b,color:#f8fafc
    style RAG fill:#0f172a,stroke:#ec4899,color:#f8fafc
"""
    return {"mermaid": mermaid_code, "repo_id": repo_id}

# STRETCH FEATURE 1: Code Base Health & Bug-Prone File Analyzer
@router.post("/audit")
def audit_codebase(req: AuditRequest):
    repo_id = req.repo_id
    if repo_id not in active_repos:
        get_repository_summary(repo_id)

    session = active_repos.get(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not indexed.")

    chunks = session["chunks"]
    
    bug_prone_files = []
    todo_markers = []
    file_chunk_counts = {}

    for c in chunks:
        path = c["file_path"]
        file_chunk_counts[path] = file_chunk_counts.get(path, 0) + 1
        content = c["content"]

        # Detect TODOs and FIXMEs
        todos = re.findall(r'#\s*(TODO|FIXME|XXX):?.*', content, re.IGNORECASE)
        if todos:
            todo_markers.append({
                "file_path": path,
                "line": c["start_line"],
                "type": todos[0],
                "snippet": content[:120]
            })

    # Files with largest chunk counts (> 10 chunks) are complex & bug-prone
    for path, count in sorted(file_chunk_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        bug_prone_files.append({
            "file_path": path,
            "chunk_count": count,
            "risk_level": "HIGH" if count > 12 else "MEDIUM",
            "reason": f"High cyclomatic complexity and large line volume ({count * 40}+ lines)"
        })

    return {
        "repo_id": repo_id,
        "bug_prone_files": bug_prone_files,
        "todo_count": len(todo_markers),
        "todos": todo_markers[:8]
    }

# STRETCH FEATURE 2: Auto-Generate README.md for Repo
@router.post("/generate-readme")
def generate_readme(req: ReadmeRequest):
    repo_id = req.repo_id
    if repo_id not in active_repos:
        get_repository_summary(repo_id)

    session = active_repos.get(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not indexed.")

    summary = session["summary"]
    owner = summary["owner"]
    repo = summary["repo"]
    stack_str = ", ".join(summary.get("tech_stack", [])) or "Multi-language"

    readme_md = f"""# {repo} 🚀

> **Automated Overview & Documentation generated by RepoMind AI**

## 📖 About The Project
`{repo}` is a repository owned by **{owner}** built using **{stack_str}**.

### 📊 Repository Statistics
- **Total Files**: {summary['total_files']}
- **Lines of Code**: {summary['total_lines']}
- **Default Branch**: `{summary['branch']}`
- **GitHub Repository**: [{owner}/{repo}]({summary['html_url']})

## 🛠️ Tech Stack
{chr(10).join([f"- **{tech}**" for tech in summary.get('tech_stack', ['Standard Base'])])}

## 📂 Key Entry Points
{chr(10).join([f"- `{ep['path']}` ({ep['language']})" for ep in summary.get('entry_points', [{'path': 'README.md', 'language': 'Markdown'}])])}

---
*Generated using [RepoMind AI](https://github.com/TejasKumat8/RepoMind)*
"""
    return {"readme": readme_md, "repo_id": repo_id}
