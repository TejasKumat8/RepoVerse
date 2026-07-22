import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "RepoVerse — Understand Any GitHub Repository with AI"
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    STORAGE_DIR: Path = BASE_DIR / "storage"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # RAG Settings
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 6

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
