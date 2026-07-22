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

        summary_text = ""
        if repo_summary:
            stack_str = ", ".join(repo_summary.get("tech_stack", [])) or "Standard Codebase"
            entries = [ep["path"] for ep in repo_summary.get("entry_points", [])]
            summary_text = (
                f"\n--- REPOSITORY OVERVIEW METADATA ---\n"
                f"Repository: {repo_summary.get('owner')}/{repo_summary.get('repo')}\n"
                f"Description: {repo_summary.get('description', 'N/A')}\n"
                f"Created Date: {repo_summary.get('created_at', 'Unknown')}\n"
                f"Total Forks: {repo_summary.get('forks_count', 0)} | Total Stars: {repo_summary.get('stargazers_count', 0)}\n"
                f"Tech Stack: {stack_str}\n"
                f"Total Files: {repo_summary.get('total_files')} | Lines of Code: {repo_summary.get('total_lines')}\n"
                f"Main Entry Points: {', '.join(entries[:4])}\n"
            )

        system_prompt = (
            "You are RepoMind AI, an expert AI Pair Programmer and codebase analyst. "
            "Your job is to answer developer questions about a GitHub repository using the provided source code chunks and repository metadata.\n\n"
            "Guidelines:\n"
            "1. Give clear, well-structured markdown answers with code snippets.\n"
            "2. If asked about creation date, forks, stars, or owner details, use the repository metadata provided.\n"
            "3. If asked about the purpose, problem solved, or overview of the repo, synthesize the project's core functionality, main components, and key entry points.\n"
            "4. Always reference exact files and line ranges when explaining specific logic (e.g. `[src/auth.py:L12-L45]`).\n"
            "5. Be direct, professional, and developer-friendly."
        )

        user_prompt = f"Repository: {repo_info.get('owner')}/{repo_info.get('repo')}\nQuestion: {query}\n{summary_text}\nRetrieved Code Context:\n{context_text}"

        effective_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")

        if effective_key and effective_key.strip():
            key_clean = effective_key.strip()
            try:
                if api_provider.lower() == "openai" or key_clean.startswith("sk-"):
                    return cls._call_openai(system_prompt, user_prompt, key_clean, citations)
                elif api_provider.lower() == "groq" or key_clean.startswith("gsk_"):
                    return cls._call_groq(system_prompt, user_prompt, key_clean, citations)
                else:
                    return cls._call_gemini(system_prompt, user_prompt, key_clean, citations)
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    warning_head = "⚠️ **Gemini API Key Quota Reached (429)**: Your Gemini API Key has hit its rate limit."
                else:
                    warning_head = f"⚠️ **API Notice ({api_provider.upper()})**: {err_msg[:120]}"

                return {
                    "answer": f"{warning_head}\n\n"
                              f"Falling back to RepoMind Codebase Engine results below:\n\n" + 
                              cls._smart_local_synthesizer(query, context_chunks, repo_info, repo_summary, citations)["answer"],
                    "citations": citations,
                    "provider": f"{api_provider.upper()} (Error Fallback)"
                }

        return cls._smart_local_synthesizer(query, context_chunks, repo_info, repo_summary, citations)

    @classmethod
    def _call_gemini(cls, system_prompt: str, user_prompt: str, api_key: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        endpoints = [
            ("v1beta", "gemini-1.5-flash"),
            ("v1beta", "gemini-2.0-flash"),
            ("v1beta", "gemini-1.5-pro"),
            ("v1", "gemini-1.5-flash"),
            ("v1", "gemini-pro")
        ]
        errors = []

        for ver, model in endpoints:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
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
            try:
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    answer = data['candidates'][0]['content']['parts'][0]['text']
                    return {"answer": answer, "citations": citations, "provider": f"Google {model}"}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                errors.append(f"HTTP {e.code}: {e.reason}")
                if e.code == 429:
                    raise Exception("HTTP 429 Too Many Requests: Quota limit reached on Gemini API Key.")
            except Exception as e:
                errors.append(str(e))

        raise Exception("; ".join(errors) or "Gemini API endpoints failed. Please check API Key.")

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
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                answer = data['choices'][0]['message']['content']
                return {"answer": answer, "citations": citations, "provider": "OpenAI gpt-4o-mini"}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f"OpenAI HTTP {e.code}: {err_body[:150]}")

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
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                answer = data['choices'][0]['message']['content']
                return {"answer": answer, "citations": citations, "provider": "Groq (Llama 3.3)"}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f"Groq HTTP {e.code}: {err_body[:150]}")

    @classmethod
    def _smart_local_synthesizer(
        cls, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        repo_info: Dict[str, Any], 
        repo_summary: Optional[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        owner = repo_info.get('owner') or (repo_summary.get('owner') if repo_summary else 'owner')
        repo = repo_info.get('repo') or (repo_summary.get('repo') if repo_summary else 'repo')
        
        q_lower = query.lower()
        is_metadata_q = any(k in q_lower for k in ["created", "fork", "star", "date", "when", "owner", "author", "created_at", "issues"])
        is_overview_q = any(k in q_lower for k in ["purpose", "problem", "overview", "summarize", "summary", "about", "what is this", "what does", "how does"])

        answer_parts = []

        if is_metadata_q:
            created_at = repo_info.get("created_at") or (repo_summary.get("created_at") if repo_summary else "Unknown")
            forks = repo_info.get("forks_count") if repo_info.get("forks_count") is not None else (repo_summary.get("forks_count") if repo_summary else 0)
            stars = repo_info.get("stargazers_count") if repo_info.get("stargazers_count") is not None else (repo_summary.get("stargazers_count") if repo_summary else 0)
            desc = repo_info.get("description") or (repo_summary.get("description") if repo_summary else "")

            answer_parts.append(
                f"### 📊 Repository Details: `{owner}/{repo}`\n\n"
                f"- 📅 **Created At:** {created_at}\n"
                f"- 🍴 **Total Forks:** {forks}\n"
                f"- ⭐ **Total Stars:** {stars}\n"
                f"- 📝 **Description:** {desc or 'No description provided.'}\n"
                f"- 🔗 **GitHub URL:** [https://github.com/{owner}/{repo}](https://github.com/{owner}/{repo})\n"
            )

        elif is_overview_q and repo_summary:
            stack_str = ", ".join(repo_summary.get("tech_stack", [])) or "Standard Codebase"
            entries = [f"`{ep['path']}`" for ep in repo_summary.get("entry_points", [])]
            answer_parts.append(
                f"### 🎯 Project Overview & Purpose: `{owner}/{repo}`\n\n"
                f"**Repository:** `{owner}/{repo}`  \n"
                f"**Tech Stack:** {stack_str}  \n"
                f"**Scale:** {repo_summary.get('total_files', 0)} files ({repo_summary.get('total_lines', 0)} total lines)  \n"
                f"**Key Entry Points:** {', '.join(entries[:4]) or 'N/A'}\n\n"
                f"#### 💡 Core Overview\n"
                f"This repository `{repo}` is built using **{stack_str}**. "
                f"It is structured into primary entry points ({', '.join(entries[:3]) or 'core files'}) to execute the application workflow.\n"
            )

        if context_chunks:
            answer_parts.append(f"### 🔍 Retrieved Codebase Context for: *\"{query}\"*\n")
            for idx, chunk in enumerate(context_chunks[:4], 1):
                answer_parts.append(
                    f"#### {idx}. `{chunk['file_path']}` (Lines {chunk['start_line']}-{chunk['end_line']})\n"
                    f"```{chunk['language'].lower()}\n{chunk['content']}\n```\n"
                )

        if not answer_parts:
            answer_parts.append(f"I analyzed `{owner}/{repo}`, but couldn't find code snippets directly matching **\"{query}\"**.")

        answer_parts.append(
            "\n> 💡 **Tip**: Enter a valid **Gemini API Key** in top-right `[⚙️ Settings]` for deep ChatGPT-style conversational responses!"
        )

        return {
            "answer": "\n".join(answer_parts),
            "citations": citations,
            "provider": "RepoMind Offline RAG Engine"
        }
