import os
import json
from pathlib import Path
from typing import Dict, Any, List
from app.parser.code_parser import IGNORED_DIRS, IGNORED_FILES, EXTENSION_MAP

class SummaryService:
    @classmethod
    def generate_summary(cls, repo_path: str, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        root = Path(repo_path)
        
        tech_stack = set()
        file_counts = {}
        languages_count = {}
        entry_points = []
        total_files = 0
        total_lines = 0

        manifest_files = {
            'package.json': cls._inspect_package_json,
            'requirements.txt': cls._inspect_requirements_txt,
            'pyproject.toml': lambda p: tech_stack.add('Python (pyproject)'),
            'go.mod': lambda p: tech_stack.add('Go'),
            'Cargo.toml': lambda p: tech_stack.add('Rust'),
            'pom.xml': lambda p: tech_stack.add('Java (Maven)'),
            'build.gradle': lambda p: tech_stack.add('Java/Kotlin (Gradle)'),
            'Dockerfile': lambda p: tech_stack.add('Docker'),
            'docker-compose.yml': lambda p: tech_stack.add('Docker Compose'),
            'tsconfig.json': lambda p: tech_stack.add('TypeScript'),
            'tailwind.config.js': lambda p: tech_stack.add('Tailwind CSS')
        }

        # Tree structure accumulator
        folder_tree = {"name": repo_info.get("repo", "root"), "type": "directory", "children": []}

        for path in root.rglob('*'):
            rel_parts = path.relative_to(root).parts
            if any(part in IGNORED_DIRS for part in rel_parts[:-1]):
                continue
            if path.name in IGNORED_FILES:
                continue

            rel_str = str(path.relative_to(root)).replace('\\', '/')

            if path.is_file():
                total_files += 1
                ext = path.suffix.lower()
                lang = EXTENSION_MAP.get(ext, EXTENSION_MAP.get(path.name.lower(), 'Other'))
                languages_count[lang] = languages_count.get(lang, 0) + 1
                
                # Tech stack inspection
                if path.name in manifest_files:
                    try:
                        manifest_files[path.name](path)
                    except Exception:
                        pass
                elif ext in ['.py']:
                    tech_stack.add('Python')
                elif ext in ['.js', '.jsx']:
                    tech_stack.add('JavaScript')
                elif ext in ['.ts', '.tsx']:
                    tech_stack.add('TypeScript')
                elif ext in ['.go']:
                    tech_stack.add('Go')
                elif ext in ['.rs']:
                    tech_stack.add('Rust')
                elif ext in ['.java']:
                    tech_stack.add('Java')

                # Entry point detection
                lower_rel = rel_str.lower()
                if lower_rel in ['main.py', 'app.py', 'server.js', 'index.js', 'src/main.rs', 'src/main.go', 'src/index.js', 'src/index.tsx', 'src/app.tsx', 'dockerfile', 'readme.md']:
                    entry_points.append({"path": rel_str, "language": lang})

                # Count lines for small text files
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass

        # Sort top languages
        top_languages = sorted(languages_count.items(), key=lambda x: x[1], reverse=True)[:6]

        # Build clean directory tree (top 2 levels for crisp UI rendering)
        tree_children = cls._build_tree(root, root, max_depth=3)

        return {
            "repo_id": repo_info.get("repo_id"),
            "owner": repo_info.get("owner"),
            "repo": repo_info.get("repo"),
            "branch": repo_info.get("branch"),
            "html_url": repo_info.get("html_url"),
            "tech_stack": sorted(list(tech_stack)),
            "total_files": total_files,
            "total_lines": total_lines,
            "top_languages": top_languages,
            "entry_points": entry_points[:8],
            "folder_tree": tree_children
        }

    @staticmethod
    def _inspect_package_json(path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                if 'react' in deps:
                    return 'React'
                if 'vue' in deps:
                    return 'Vue'
                if 'next' in deps:
                    return 'Next.js'
                if 'express' in deps:
                    return 'Express.js'
        except Exception:
            pass

    @staticmethod
    def _inspect_requirements_txt(path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    return 'FastAPI'
                if 'django' in content:
                    return 'Django'
                if 'flask' in content:
                    return 'Flask'
                if 'torch' in content or 'tensorflow' in content:
                    return 'PyTorch/TensorFlow'
        except Exception:
            pass

    @classmethod
    def _build_tree(cls, current_dir: Path, root: Path, depth: int = 0, max_depth: int = 3) -> List[Dict[str, Any]]:
        if depth >= max_depth:
            return []

        children = []
        try:
            items = sorted(list(current_dir.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.name in IGNORED_DIRS or item.name in IGNORED_FILES or item.name.startswith('.'):
                    continue

                rel_path = str(item.relative_to(root)).replace('\\', '/')
                if item.is_dir():
                    sub_children = cls._build_tree(item, root, depth + 1, max_depth)
                    children.append({
                        "name": item.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": sub_children
                    })
                else:
                    children.append({
                        "name": item.name,
                        "path": rel_path,
                        "type": "file"
                    })
        except Exception:
            pass

        return children
