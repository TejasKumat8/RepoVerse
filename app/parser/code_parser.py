import os
from pathlib import Path
from typing import List, Dict, Any

# Directories to ignore
IGNORED_DIRS = {
    '.git', '.github', 'node_modules', 'dist', 'build', 'out', '__pycache__',
    'venv', '.venv', 'env', '.env', '.idea', '.vscode', 'coverage', '.pytest_cache',
    'target', 'bin', 'obj', 'vendor', '.next', '.nuxt'
}

# Files to ignore
IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
    'Pipfile.lock', 'Cargo.lock', '.DS_Store', 'thumbs.db'
}

# Supported code extensions and language mappings
EXTENSION_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript (React)',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (React)',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.cs': 'C#',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.kt': 'Kotlin',
    '.swift': 'Swift',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.md': 'Markdown',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    '.dockerfile': 'Docker',
    'dockerfile': 'Docker'
}

class CodeParser:
    @staticmethod
    def is_text_file(filepath: Path) -> bool:
        if filepath.name in IGNORED_FILES:
            return False
        ext = filepath.suffix.lower()
        if ext in EXTENSION_MAP or filepath.name.lower() in EXTENSION_MAP:
            return True
        # Exclude common binaries
        binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.pyc', '.wasm', '.svg', '.ttf', '.woff', '.woff2'}
        if ext in binary_exts:
            return False
        return False

    @classmethod
    def parse_repository(cls, repo_dir: str, max_chunk_lines: int = 40, overlap_lines: int = 5) -> List[Dict[str, Any]]:
        root = Path(repo_dir)
        chunks = []

        for path in root.rglob('*'):
            if not path.is_file():
                continue
                
            # Check if any parent directory is ignored
            relative_parts = path.relative_to(root).parts
            if any(part in IGNORED_DIRS for part in relative_parts[:-1]):
                continue

            if not cls.is_text_file(path):
                continue

            try:
                rel_path = str(path.relative_to(root)).replace('\\', '/')
                ext = path.suffix.lower()
                language = EXTENSION_MAP.get(ext, EXTENSION_MAP.get(path.name.lower(), 'Text'))
                
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                if not lines:
                    continue

                total_lines = len(lines)
                step = max_chunk_lines - overlap_lines
                if step <= 0:
                    step = max_chunk_lines

                for start_idx in range(0, total_lines, step):
                    end_idx = min(start_idx + max_chunk_lines, total_lines)
                    chunk_lines = lines[start_idx:end_idx]
                    chunk_content = "".join(chunk_lines).strip()
                    
                    if not chunk_content:
                        continue

                    chunk_id = f"{rel_path}:L{start_idx + 1}-L{end_idx}"
                    
                    chunks.append({
                        "id": chunk_id,
                        "file_path": rel_path,
                        "start_line": start_idx + 1,
                        "end_line": end_idx,
                        "content": chunk_content,
                        "language": language,
                        "line_count": len(chunk_lines)
                    })

            except Exception as e:
                # Silently skip unreadable files
                continue

        return chunks
