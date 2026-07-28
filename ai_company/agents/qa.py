"""QAEngineerAgent — scrive ed esegue i test automatici sul progetto generato.

E' l'agente che da' l'ultima parola sulla qualita': genera una suite
pytest basata sulle funzionalita' abilitate, la esegue realmente contro
il backend appena generato (in un sottoprocesso, con la stessa working
directory dell'app) e riporta l'esito nel CompanyReport.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.models import Preferences, RequirementsSpec

TEST_HEADER = '''"""Test automatici generati dal QA Engineer Agent."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_homepage_renders():
    resp = client.get("/")
    assert resp.status_code == 200


def test_item_crud_flow():
    resp = client.post(
        "/api/items",
        json={"name": "Articolo di test", "description": "demo", "price": 9.99, "category": "test"},
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["name"] == "Articolo di test"

    resp = client.get("/api/items")
    assert resp.status_code == 200
    assert any(i["id"] == item["id"] for i in resp.json())

    item_id = item["id"]
    resp = client.get(f"/api/items/{item_id}")
    assert resp.status_code == 200

    resp = client.delete(f"/api/items/{item_id}")
    assert resp.status_code == 204
'''

CUSTOMER_TESTS = '''

def test_customer_crud_flow():
    resp = client.post("/api/customers", json={"name": "Mario Rossi", "email": "mario@example.com"})
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["name"] == "Mario Rossi"

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert any(c["id"] == customer["id"] for c in resp.json())
'''

ORDER_TESTS = '''

def test_order_flow():
    resp = client.post(
        "/api/items",
        json={"name": "Articolo ordine", "description": "demo", "price": 5.0, "category": "test"},
    )
    item_id = resp.json()["id"]

    resp = client.post(
        "/api/orders",
        json={"customer_name": "Cliente Test", "items": [{"item_id": item_id, "quantity": 2}]},
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["customer_name"] == "Cliente Test"
    assert order["status"] == "ricevuto"

    resp = client.get("/api/orders")
    assert resp.status_code == 200
    assert any(o["id"] == order["id"] for o in resp.json())

    order_id = order["id"]
    resp = client.patch(f"/api/orders/{order_id}/status", params={"status": "in preparazione"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in preparazione"


def test_order_rejects_unknown_item():
    resp = client.post(
        "/api/orders",
        json={"customer_name": "Cliente Test", "items": [{"item_id": 999999, "quantity": 1}]},
    )
    assert resp.status_code == 400
'''


class QAEngineerAgent(BaseAgent):
    name = "QA Engineer Agent"
    role = "Scrive ed esegue i test automatici sul backend generato"

    def write_tests(
        self, project_dir: Path, preferences: Preferences, requirements: RequirementsSpec
    ) -> Path:
        content = TEST_HEADER
        if preferences.enable_customer_accounts:
            content += CUSTOMER_TESTS
        if preferences.enable_online_orders:
            content += ORDER_TESTS

        return self._write(project_dir / "tests" / "test_api.py", content)

    def run_tests(self, project_dir: Path) -> tuple[bool, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(project_dir) + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            cwd=project_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        output = result.stdout + "\n" + result.stderr
        return passed, output
