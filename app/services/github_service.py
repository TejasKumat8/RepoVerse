import os
import re
import shutil
import zipfile
import io
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple
from app.core.config import settings

class GitHubService:
    @staticmethod
    def parse_repo_url(url_or_slug: str) -> Tuple[str, str, str]:
        """
        Parses inputs like:
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/dev
        - owner/repo
        Returns: (owner, repo, branch)
        """
        clean_input = url_or_slug.strip().rstrip('/')
        
        # Match github.com URL pattern
        url_pattern = r'github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?'
        match = re.search(url_pattern, clean_input)
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            branch = match.group(3) or 'main'
            return owner, repo, branch

        # Match slug pattern "owner/repo"
        parts = clean_input.split('/')
        if len(parts) == 2:
            return parts[0], parts[1].replace('.git', ''), 'main'
        elif len(parts) == 3:
            return parts[0], parts[1], parts[2]
            
        raise ValueError(f"Invalid GitHub URL or repository slug: '{url_or_slug}'")

    @classmethod
    def download_and_extract_repo(cls, url_or_slug: str, custom_token: str = None) -> Dict[str, Any]:
        owner, repo, default_branch = cls.parse_repo_url(url_or_slug)
        repo_id = f"{owner}_{repo}"
        target_dir = settings.STORAGE_DIR / "repos" / repo_id
        
        token = custom_token or settings.GITHUB_TOKEN
        
        # Try downloading branches: default_branch, then main, master
        branches_to_try = [default_branch]
        if default_branch not in ['main', 'master']:
            branches_to_try.extend(['main', 'master'])
        else:
            branches_to_try.append('master' if default_branch == 'main' else 'main')
            
        headers = {
            "User-Agent": "RepoMind-AI-App",
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            headers["Authorization"] = f"token {token}"
            
        downloaded = False
        used_branch = default_branch

        for branch in branches_to_try:
            zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
            req = urllib.request.Request(zip_url, headers=headers)
            try:
                with urllib.request.urlopen(req) as response:
                    zip_data = response.read()
                    
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                        z.extractall(target_dir)
                        
                    # GitHub zip zipballs extract into a top-level directory like owner-repo-hash/
                    extracted_subdirs = [d for d in target_dir.iterdir() if d.is_dir()]
                    if len(extracted_subdirs) == 1:
                        # Move all items up one level
                        inner_dir = extracted_subdirs[0]
                        for item in inner_dir.iterdir():
                            shutil.move(str(item), str(target_dir / item.name))
                        inner_dir.rmdir()
                        
                    downloaded = True
                    used_branch = branch
                    break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
                elif e.code == 401 or e.code == 403:
                    raise Exception(f"GitHub Authorization Failed (Status {e.code}). Please check your GitHub token.")
                else:
                    raise Exception(f"Failed to fetch GitHub repository: HTTP {e.code} - {e.reason}")
            except Exception as e:
                raise Exception(f"Failed to download repository: {str(e)}")

        if not downloaded:
            raise Exception(f"Could not download repository '{owner}/{repo}'. Please check if it's public and valid.")

        return {
            "repo_id": repo_id,
            "owner": owner,
            "repo": repo,
            "branch": used_branch,
            "local_path": str(target_dir),
            "html_url": f"https://github.com/{owner}/{repo}"
        }
