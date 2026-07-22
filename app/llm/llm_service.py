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
        api_provider: str = "gemini",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded natural language answers using RAG context chunks.
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

        system_prompt = (
            "You are RepoMind AI, an expert AI Pair Programmer and codebase analyst. "
            "Your job is to answer developer questions about a GitHub repository using ONLY the provided source code chunks.\n\n"
            "Guidelines:\n"
            "1. Give clear, well-structured markdown answers with code snippets.\n"
            "2. Always reference exact files and line ranges when explaining logic (e.g. `[src/auth.py:L12-L45]`).\n"
            "3. If the code context contains the answer, explain the implementation step-by-step.\n"
            "4. Be direct, professional, and developer-friendly."
        )

        user_prompt = f"Repository: {repo_info.get('owner')}/{repo_info.get('repo')}\nQuestion: {query}\n\nRetrieved Code Context:\n{context_text}"

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

        return cls._smart_local_synthesizer(query, context_chunks, repo_info, citations)

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
    def _smart_local_synthesizer(cls, query: str, context_chunks: List[Dict[str, Any]], repo_info: Dict[str, Any], citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not context_chunks:
            return {
                "answer": f"I analyzed `{repo_info.get('owner')}/{repo_info.get('repo')}`, but couldn't find code snippets directly matching **\"{query}\"**. Try rephrasing your search or exploring the directory tree.",
                "citations": [],
                "provider": "RepoMind Offline RAG Engine"
            }

        answer_parts = [
            f"### 🤖 Analysis of: *\"{query}\"*\n",
            f"Based on semantic retrieval from **{repo_info.get('owner')}/{repo_info.get('repo')}**, here is where and how this feature is implemented:\n"
        ]

        for idx, chunk in enumerate(context_chunks[:4], 1):
            answer_parts.append(
                f"#### {idx}. `{chunk['file_path']}` (Lines {chunk['start_line']}-{chunk['end_line']})\n"
                f"```{chunk['language'].lower()}\n{chunk['content']}\n```\n"
            )

        answer_parts.append("\n> 💡 *Note: To unlock interactive multi-turn AI reasoning, add your Gemini/OpenAI API key in the top-right Settings modal!*")

        return {
            "answer": "\n".join(answer_parts),
            "citations": citations,
            "provider": "RepoMind Offline RAG Engine"
        }
