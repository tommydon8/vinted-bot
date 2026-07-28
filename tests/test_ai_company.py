"""Verifica end-to-end della pipeline AI Company.

Per ciascun tipo di attivita' supportato, esegue l'intera catena di
agenti e controlla che il progetto generato sia completo e che i test
del QA Engineer Agent passino davvero contro il backend generato.
"""

from pathlib import Path

import pytest

from ai_company.models import Preferences
from ai_company.orchestrator import AICompany


@pytest.mark.parametrize("business_type", ["negozio", "ristorante", "azienda", "altro"])
def test_company_generates_working_project(tmp_path: Path, business_type: str) -> None:
    preferences = Preferences(
        business_name=f"Demo {business_type}",
        business_type=business_type,
        description="Attivita' di test generata automaticamente.",
        output_dir=tmp_path,
    )

    company = AICompany()
    report = company.run(preferences, run_tests=True)

    project_dir = report.project_dir
    assert project_dir.exists()

    expected_files = [
        "app/main.py",
        "app/models.py",
        "app/schemas.py",
        "app/crud.py",
        "app/database.py",
        "app/templates/base.html",
        "app/templates/index.html",
        "app/static/style.css",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        "tests/test_api.py",
    ]
    for rel_path in expected_files:
        assert (project_dir / rel_path).exists(), f"file mancante: {rel_path}"

    assert report.qa_passed is True, report.qa_output
    assert len(report.log) >= 8


def test_disabling_features_removes_related_endpoints(tmp_path: Path) -> None:
    preferences = Preferences(
        business_name="Solo Catalogo",
        business_type="negozio",
        enable_online_orders=False,
        enable_customer_accounts=False,
        output_dir=tmp_path,
    )

    company = AICompany()
    report = company.run(preferences, run_tests=True)

    main_py = (report.project_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "/api/orders" not in main_py
    assert "/api/customers" not in main_py
    assert report.qa_passed is True, report.qa_output


def test_slug_generation() -> None:
    preferences = Preferences(business_name="Caffè Città!", business_type="ristorante")
    assert preferences.slug() == "caff-citt"
