"""DevOpsAgent — prepara il progetto per l'esecuzione e il deploy."""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.models import Preferences

REQUIREMENTS_TXT = """fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
jinja2==3.1.4
python-multipart==0.0.9
"""

DOCKERFILE = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _docker_compose(slug: str) -> str:
    return f"""services:
  {slug}:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
"""


ENV_EXAMPLE = """# Porta su cui esporre l'app (usata da alcuni host, es. Railway)
PORT=8000
"""

PROCFILE = "web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}\n"

GITIGNORE = """data/*.db
__pycache__/
*.pyc
.venv/
venv/
"""


class DevOpsAgent(BaseAgent):
    name = "DevOps Agent"
    role = "Prepara Dockerfile, dipendenze e configurazione di deploy"

    def build(self, project_dir: Path, preferences: Preferences) -> list[str]:
        written: list[str] = []
        files = {
            project_dir / "requirements.txt": REQUIREMENTS_TXT,
            project_dir / "Dockerfile": DOCKERFILE,
            project_dir / "docker-compose.yml": _docker_compose(preferences.slug()),
            project_dir / ".env.example": ENV_EXAMPLE,
            project_dir / "Procfile": PROCFILE,
            project_dir / ".gitignore": GITIGNORE,
        }
        for path, content in files.items():
            self._write(path, content)
            written.append(str(path.relative_to(project_dir)))

        return written
