"""AICompany — orchestra la pipeline di agenti dal brief alla startup pronta.

Flusso:
  CEO -> Business Analyst -> Product Manager -> Architect
       -> Backend Developer -> Frontend Developer
       -> QA Engineer -> DevOps -> Marketing

L'utente interagisce solo con il CEOAgent (preferenze iniziali). Tutti
gli altri passaggi avvengono in autonomia; il risultato e' un
CompanyReport con il log di ogni agente e l'esito dei test.
"""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.analyst import BusinessAnalystAgent
from ai_company.agents.architect import ArchitectAgent
from ai_company.agents.backend_dev import BackendDeveloperAgent
from ai_company.agents.ceo import CEOAgent
from ai_company.agents.devops import DevOpsAgent
from ai_company.agents.frontend_dev import FrontendDeveloperAgent
from ai_company.agents.marketing import MarketingAgent
from ai_company.agents.product_manager import ProductManagerAgent
from ai_company.agents.qa import QAEngineerAgent
from ai_company.models import CompanyReport, Preferences


class AICompany:
    """La "compagnia" di agenti AI, pronta a eseguire l'intera pipeline."""

    def __init__(self) -> None:
        self.ceo = CEOAgent()
        self.analyst = BusinessAnalystAgent()
        self.product_manager = ProductManagerAgent()
        self.architect = ArchitectAgent()
        self.backend_dev = BackendDeveloperAgent()
        self.frontend_dev = FrontendDeveloperAgent()
        self.qa = QAEngineerAgent()
        self.devops = DevOpsAgent()
        self.marketing = MarketingAgent()

    def run(self, preferences: Preferences, run_tests: bool = True) -> CompanyReport:
        project_dir = Path(preferences.output_dir) / preferences.slug()
        project_dir.mkdir(parents=True, exist_ok=True)

        report = CompanyReport(project_dir=project_dir)

        goal = self.ceo.kickoff(preferences)
        report.add(self.ceo.name, goal)

        requirements = self.analyst.analyze(preferences)
        report.add(
            self.analyst.name,
            f"Requisiti definiti per attivita' di tipo '{requirements.business_type}'",
            requirements.core_features,
        )

        plan = self.product_manager.plan(preferences, requirements)
        report.add(
            self.product_manager.name,
            f"MVP definito con {len(plan.mvp_features)} funzionalita' e {len(plan.user_stories)} user story",
            plan.user_stories,
        )

        architecture = self.architect.design(preferences, plan)
        report.add(
            self.architect.name,
            "Stack tecnico e modello dati progettati",
            architecture.backend_stack + architecture.frontend_stack,
        )

        backend_files = self.backend_dev.build(project_dir, preferences, requirements, architecture)
        report.add(self.backend_dev.name, f"Backend generato ({len(backend_files)} file)", backend_files)

        frontend_files = self.frontend_dev.build(project_dir, preferences)
        report.add(self.frontend_dev.name, f"Frontend generato ({len(frontend_files)} file)", frontend_files)

        devops_files = self.devops.build(project_dir, preferences)
        report.add(self.devops.name, f"Configurazione di deploy pronta ({len(devops_files)} file)", devops_files)

        test_file = self.qa.write_tests(project_dir, preferences, requirements)
        details = [str(test_file.relative_to(project_dir))]

        if run_tests:
            passed, output = self.qa.run_tests(project_dir)
            report.qa_passed = passed
            report.qa_output = output
            details.append("Test eseguiti: " + ("PASSATI" if passed else "FALLITI"))

        report.add(self.qa.name, "Suite di test scritta ed eseguita", details)

        readme = self.marketing.build(project_dir, preferences, requirements, plan, architecture)
        report.add(self.marketing.name, "Branding e README pronti", [str(readme.relative_to(project_dir))])

        return report
