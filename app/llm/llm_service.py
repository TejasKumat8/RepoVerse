import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

class LLMService:
    @classmethod
    def generate_answer(
        cls, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        repo_info: Dict[str, Any],
        repo_summary: Optional[Dict[str, Any]] = None,
        api_provider: str = "gemini",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded natural language answers using RAG context chunks + repo summary intelligence.
        """
        context_text = ""
        citations = []
        
        for idx, chunk in enumerate(context_chunks, 1):
            file_ref = f"{chunk['file_path']} (Lines {chunk['start_line']}-{chunk['end_line']})"
            citations.append({
                "id": idx,
                "file_path": chunk['file_path'],
                "start_line": chunk['start_line'],
                "end_line": chunk['end_line'],
                "language": chunk['language'],
                "score": chunk.get('score', 0)
            })
            context_text += f"\n--- SOURCE FILE [{idx}]: {file_ref} ---\n```{chunk['language'].lower()}\n{chunk['content']}\n```\n"

        # Check if question is a high-level overview / purpose question
        query_lower = query.lower()
        is_overview_query = any(k in query_lower for k in [
            "purpose", "problem", "solve", "solving", "what is", "about", "overview", 
            "summary", "summarize", "architecture", "explain repo", "explain codebase"
        ])

        summary_text = ""
        if repo_summary:
            stack_str = ", ".join(repo_summary.get("tech_stack", [])) or "Standard Codebase"
            entries = [ep["path"] for ep in repo_summary.get("entry_points", [])]
            summary_text = (
                f"\n--- REPOSITORY OVERVIEW METADATA ---\n"
                f"Repository: {repo_summary.get('owner')}/{repo_summary.get('repo')}\n"
                f"Tech Stack: {stack_str}\n"
                f"Total Files: {repo_summary.get('total_files')} | Lines of Code: {repo_summary.get('total_lines')}\n"
                f"Main Entry Points: {', '.join(entries[:4])}\n"
            )

        system_prompt = (
            "You are RepoMind AI, an expert AI Pair Programmer and codebase analyst. "
            "Your job is to answer developer questions about a GitHub repository using the provided source code chunks and repository metadata.\n\n"
            "Guidelines:\n"
            "1. Give clear, well-structured markdown answers with code snippets.\n"
            "2. If asked about the purpose, problem solved, or overview of the repo, synthesize the project's core functionality, main components, and key entry points.\n"
            "3. Always reference exact files and line ranges when explaining specific logic (e.g. `[src/auth.py:L12-L45]`).\n"
            "4. Be direct, professional, and developer-friendly."
        )

        user_prompt = f"Repository: {repo_info.get('owner')}/{repo_info.get('repo')}\nQuestion: {query}\n{summary_text}\nRetrieved Code Context:\n{context_text}"

        effective_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")

        if effective_key:
            try:
                if api_provider.lower() == "gemini" or "AIza" in effective_key:
                    return cls._call_gemini(system_prompt, user_prompt, effective_key, citations)
                elif api_provider.lower() == "openai" or effective_key.startswith("sk-"):
                    return cls._call_openai(system_prompt, user_prompt, effective_key, citations)
                elif api_provider.lower() == "groq" or effective_key.startswith("gsk_"):
                    return cls._call_groq(system_prompt, user_prompt, effective_key, citations)
            except Exception as e:
                pass

        return cls._smart_local_synthesizer(query, context_chunks, repo_info, repo_summary, is_overview_query, citations)

    @classmethod
    def _call_gemini(cls, system_prompt: str, user_prompt: str, api_key: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048
            }
        }
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            answer = data['candidates'][0]['content']['parts'][0]['text']
            return {"answer": answer, "citations": citations, "provider": "Gemini 1.5 Flash"}

    @classmethod
    def _call_openai(cls, system_prompt: str, user_prompt: str, api_key: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            answer = data['choices'][0]['message']['content']
            return {"answer": answer, "citations": citations, "provider": "OpenAI gpt-4o-mini"}

    @classmethod
    def _call_groq(cls, system_prompt: str, user_prompt: str, api_key: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            answer = data['choices'][0]['message']['content']
            return {"answer": answer, "citations": citations, "provider": "Groq (Llama 3.3)"}

    @classmethod
    def _smart_local_synthesizer(
        cls, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        repo_info: Dict[str, Any], 
        repo_summary: Optional[Dict[str, Any]],
        is_overview_query: bool,
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        owner = repo_info.get('owner', 'repo')
        repo = repo_info.get('repo', 'project')
        stack_str = ", ".join(repo_summary.get('tech_stack', [])) if repo_summary else "Software Project"
        files_count = repo_summary.get('total_files', len(context_chunks)) if repo_summary else len(context_chunks)
        entries = [ep['path'] for ep in repo_summary.get('entry_points', [])] if repo_summary else []

        if is_overview_query:
            answer_parts = [
                f"### 🚀 Project Overview & Purpose of `{owner}/{repo}`\n",
                f"**`{owner}/{repo}`** is a **{stack_str}** project containing **{files_count} files**.\n",
                f"#### 🎯 Core Purpose & Problem It Solves:\n",
                f"1. **Primary Functionality**: Provides a structured codebase built with **{stack_str}** to execute key application workflows.",
                f"2. **Main Application Entry Points**: " + (", ".join([f"`{e}`" for e in entries]) if entries else "Standard project modules."),
                f"3. **Developer Efficiency**: Simplifies feature implementation and architecture organization for maintainability.\n",
                f"#### 📂 Key Implementation Files:\n"
            ]

            for chunk in context_chunks[:4]:
                answer_parts.append(f"- **`{chunk['file_path']}`** (Lines {chunk['start_line']}-{chunk['end_line']}): Implements core `{chunk['language']}` logic.")

            answer_parts.append("\n> 💡 *Tip: Enter a Gemini, OpenAI, or Groq API Key in the top-right Settings modal for full multi-turn AI reasoning!*")

            return {
                "answer": "\n".join(answer_parts),
                "citations": citations,
                "provider": "RepoMind Offline Intelligence Engine"
            }

        if not context_chunks:
            return {
                "answer": f"I analyzed `{owner}/{repo}`, but couldn't find code snippets directly matching **\"{query}\"**. Try rephrasing your search or exploring the directory tree.",
                "citations": [],
                "provider": "RepoMind Offline RAG Engine"
            }

        answer_parts = [
            f"### 🤖 Analysis of: *\"{query}\"*\n",
            f"Based on semantic retrieval from **{owner}/{repo}**, here are the relevant code implementations:\n"
        ]

        for idx, chunk in enumerate(context_chunks[:4], 1):
            answer_parts.append(
                f"#### {idx}. `{chunk['file_path']}` (Lines {chunk['start_line']}-{chunk['end_line']})\n"
                f"```{chunk['language'].lower()}\n{chunk['content']}\n```\n"
            )

        answer_parts.append("\n> 💡 *Tip: Connect a Gemini, OpenAI, or Groq API Key in settings for full multi-turn conversational responses!*")

        return {
            "answer": "\n".join(answer_parts),
            "citations": citations,
            "provider": "RepoMind Offline RAG Engine"
        }
