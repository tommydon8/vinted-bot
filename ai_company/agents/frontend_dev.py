"""FrontendDeveloperAgent — genera i template Jinja2 e il CSS del sito.

Il tema (colore primario) e la terminologia (nome dell'entita' "item")
vengono passati dal backend al momento del render, quindi i template
generati qui sono statici: si adattano runtime tramite le variabili di
contesto che FastAPI passa a Jinja2.
"""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.models import Preferences

BASE_HTML = """<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ business_name }}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="topbar">
    <h1>{{ business_name }}</h1>
  </header>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
  <footer class="footer">
    <p>Generato automaticamente da AI Company 🏢</p>
  </footer>
</body>
</html>
"""

INDEX_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>{{ item_label_plural }}</h2>
  {% if items %}
    <div class="grid">
      {% for item in items %}
        <article class="card">
          <h3>{{ item.name }}</h3>
          <p class="muted">{{ item.category }}</p>
          <p>{{ item.description }}</p>
          <p class="price">{{ "%.2f"|format(item.price) }} €</p>
          {% if not item.available %}<p class="badge">Non disponibile</p>{% endif %}
        </article>
      {% endfor %}
    </div>
  {% else %}
    <p class="muted">Nessun {{ item_label|lower }} ancora disponibile.</p>
  {% endif %}
{% endblock %}
"""


def _style_css(primary_color: str) -> str:
    return f""":root {{
  --primary: {primary_color};
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --text: #0f172a;
  --muted: #64748b;
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
}}

.topbar {{
  background: var(--primary);
  color: white;
  padding: 1.25rem 1.5rem;
}}

.topbar h1 {{
  margin: 0;
  font-size: 1.5rem;
}}

.container {{
  max-width: 1024px;
  margin: 0 auto;
  padding: 1.5rem;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}}

.card {{
  background: var(--card-bg);
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1rem;
}}

.card h3 {{
  margin: 0 0 0.25rem 0;
}}

.price {{
  font-weight: bold;
  color: var(--primary);
}}

.muted {{
  color: var(--muted);
  font-size: 0.9rem;
}}

.badge {{
  display: inline-block;
  background: #fee2e2;
  color: #991b1b;
  padding: 0.15rem 0.5rem;
  border-radius: 0.5rem;
  font-size: 0.8rem;
}}

.footer {{
  text-align: center;
  color: var(--muted);
  padding: 2rem 1rem;
  font-size: 0.85rem;
}}
"""


class FrontendDeveloperAgent(BaseAgent):
    name = "Frontend Developer Agent"
    role = "Genera i template Jinja2 e il tema grafico del sito"

    def build(self, project_dir: Path, preferences: Preferences) -> list[str]:
        written: list[str] = []
        app_dir = project_dir / "app"

        files = {
            app_dir / "templates" / "base.html": BASE_HTML,
            app_dir / "templates" / "index.html": INDEX_HTML,
            app_dir / "static" / "style.css": _style_css(preferences.primary_color),
        }
        for path, content in files.items():
            self._write(path, content)
            written.append(str(path.relative_to(project_dir)))

        return written
