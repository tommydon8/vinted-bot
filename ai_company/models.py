"""Strutture dati condivise tra tutti gli agenti della company."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Preferences:
    """Le uniche informazioni che l'utente deve fornire.

    Tutto il resto della pipeline (analisi, architettura, codice, test,
    deploy, branding) viene prodotto in autonomia dagli agenti.
    """

    business_name: str
    business_type: str  # "negozio" | "ristorante" | "azienda" | "altro"
    description: str = ""
    primary_color: str = "#2563eb"
    languages: tuple[str, ...] = ("it",)
    enable_online_orders: bool = True
    enable_customer_accounts: bool = True
    output_dir: Path = Path("generated_projects")

    def slug(self) -> str:
        import re

        slug = re.sub(r"[^a-z0-9]+", "-", self.business_name.lower()).strip("-")
        return slug or "startup"


@dataclass
class RequirementsSpec:
    """Output del BusinessAnalystAgent."""

    business_type: str
    entity_labels: dict[str, str]
    core_features: list[str]
    nice_to_have_features: list[str]


@dataclass
class ProductPlan:
    """Output del ProductManagerAgent."""

    mvp_features: list[str]
    backlog: list[str]
    user_stories: list[str]


@dataclass
class ArchitectureSpec:
    """Output dell'ArchitectAgent."""

    backend_stack: list[str]
    frontend_stack: list[str]
    data_model: dict[str, list[str]]
    deployment_target: str


@dataclass
class AgentLogEntry:
    agent: str
    summary: str
    details: list[str] = field(default_factory=list)


@dataclass
class CompanyReport:
    """Riepilogo finale prodotto dalla pipeline, agente per agente."""

    project_dir: Path
    log: list[AgentLogEntry] = field(default_factory=list)
    qa_passed: bool | None = None
    qa_output: str = ""

    def add(self, agent: str, summary: str, details: list[str] | None = None) -> None:
        self.log.append(AgentLogEntry(agent=agent, summary=summary, details=details or []))

    def pretty_print(self) -> str:
        lines = [f"📁 Progetto generato in: {self.project_dir}", ""]
        for entry in self.log:
            lines.append(f"✅ {entry.agent}: {entry.summary}")
            for d in entry.details:
                lines.append(f"    - {d}")
        if self.qa_passed is not None:
            status = "PASSATI ✅" if self.qa_passed else "FALLITI ❌"
            lines.append("")
            lines.append(f"🧪 Test QA: {status}")
        return "\n".join(lines)
