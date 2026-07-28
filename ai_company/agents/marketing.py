"""MarketingAgent — genera branding, pitch e README del progetto finale."""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.business_profiles import get_profile
from ai_company.models import ArchitectureSpec, Preferences, ProductPlan, RequirementsSpec


class MarketingAgent(BaseAgent):
    name = "Marketing Agent"
    role = "Definisce branding, pitch e documentazione utente"

    def build(
        self,
        project_dir: Path,
        preferences: Preferences,
        requirements: RequirementsSpec,
        plan: ProductPlan,
        architecture: ArchitectureSpec,
    ) -> Path:
        profile = get_profile(preferences.business_type)
        tagline = profile["tagline"]
        description = preferences.description or tagline

        features_md = "\n".join(f"- {f}" for f in plan.mvp_features)
        backlog_md = "\n".join(f"- {f}" for f in plan.backlog)
        stack_md = "\n".join(f"- {s}" for s in architecture.backend_stack + architecture.frontend_stack)

        content = f"""# {preferences.business_name}

> {tagline}

{description}

Questo progetto e' stato generato in autonomia da **AI Company**, una
pipeline di agenti AI specializzati (analisi, prodotto, architettura,
sviluppo, QA, DevOps, marketing).

## Funzionalita' incluse (MVP)

{features_md}

## Prossimi passi suggeriti (backlog)

{backlog_md}

## Stack tecnico

{stack_md}

## Avvio in locale

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Apri http://localhost:8000 nel browser.

## Test

```bash
pytest tests/ -v
```

## Deploy con Docker

```bash
docker compose up --build
```
"""
        return self._write(project_dir / "README.md", content)
