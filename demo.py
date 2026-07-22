import sys
import os

# Set UTF-8 encoding for Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.github_service import GitHubService
from app.parser.code_parser import CodeParser
from app.rag.vector_store import VectorStore
from app.llm.llm_service import LLMService
from app.services.summary_service import SummaryService

def run_demo(target_repo="pallets/flask", sample_query="Where is the Flask app class defined and initialized?"):
    print("=" * 70)
    print(f"REPOVERSE - LIVE DEMO FOR REPOSITORY: '{target_repo}'")
    print("=" * 70)

    # 1. Download & Extract Repo
    print("\n[STEP 1] Downloading & extracting repository...")
    repo_info = GitHubService.download_and_extract_repo(target_repo)
    print(f"   -> Local Path: {repo_info['local_path']}")

    # 2. Parse & Chunk Code
    print("\n[STEP 2] Parsing files & generating line-aware code chunks...")
    chunks = CodeParser.parse_repository(repo_info['local_path'])
    print(f"   -> Total Semantic Code Chunks: {len(chunks)}")

    # 3. Build Vector Store
    print("\n[STEP 3] Building Vector Store index (TF-IDF & Cosine Embeddings)...")
    vector_store = VectorStore(repo_info['repo_id'])
    vector_store.build_index(chunks)
    print(f"   -> Vector Index ready!")

    # 4. Generate Repo Intelligence Summary
    print("\n[STEP 4] Detecting Tech Stack & Architecture Overview...")
    summary = SummaryService.generate_summary(repo_info['local_path'], repo_info)
    print(f"   -> Detected Tech Stack: {', '.join(summary['tech_stack'])}")
    print(f"   -> Total Files: {summary['total_files']} | Lines of Code: {summary['total_lines']}")
    print(f"   -> Important Entry Points: {[ep['path'] for ep in summary['entry_points']]}")

    # 5. Perform RAG Vector Search & Answer Generation
    print("\n[STEP 5] Running RAG Question Answering...")
    print(f"   Question: \"{sample_query}\"\n")
    top_chunks = vector_store.search(sample_query, top_k=4)
    
    result = LLMService.generate_answer(
        query=sample_query,
        context_chunks=top_chunks,
        repo_info=repo_info,
        api_provider="local"
    )

    print("=" * 70)
    print("REPOVERSE RESPONSE:")
    print("=" * 70)
    print(result['answer'])
    print("\nRETRIEVED SOURCE CITATIONS:")
    for cit in result['citations']:
        print(f"   - File: {cit['file_path']} (Lines {cit['start_line']}-{cit['end_line']}) | Language: {cit['language']} | Score: {cit['score']}")
    print("=" * 70)

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "pallets/flask"
    query = sys.argv[2] if len(sys.argv) > 2 else "Where is the Flask app class defined and initialized?"
    run_demo(repo, query)
