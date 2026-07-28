"""Classe base per tutti gli agenti della company.

Ogni agente ha un nome, un ruolo (usato nei log) e implementa un unico
metodo pubblico specifico al proprio compito. La classe base fornisce
solo utility comuni (creazione directory, scrittura file) cosi' da
evitare duplicazione tra gli agenti "developer".
"""

from __future__ import annotations

from pathlib import Path


class BaseAgent:
    name: str = "Agente"
    role: str = "Compito generico"

    def _write(self, path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}' — {self.role}>"
