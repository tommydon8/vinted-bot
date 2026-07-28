"""Entry point interattivo: `python -m ai_company.cli`.

Raccoglie le preferenze dall'utente una sola volta (tramite il
CEOAgent), poi lascia che la company lavori in completa autonomia fino
a consegnare un progetto pronto all'uso.
"""

from __future__ import annotations

from ai_company.agents.ceo import CEOAgent
from ai_company.orchestrator import AICompany


def main() -> None:
    ceo = CEOAgent()
    preferences = ceo.collect_preferences_interactively()

    print("\n🚀 Le preferenze sono state raccolte. La company inizia a lavorare in autonomia...\n")

    company = AICompany()
    report = company.run(preferences)

    print("\n" + report.pretty_print())


if __name__ == "__main__":
    main()
