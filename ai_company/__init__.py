"""
AI Company — una "azienda" di agenti AI che progetta, costruisce, testa e
prepara al deploy una startup software su misura per un negozio, un
ristorante, un'azienda di servizi o qualsiasi altra attività.

Ogni agente ha una responsabilità unica (analisi, architettura, sviluppo
backend/frontend, QA, DevOps, marketing) e passa il proprio output al
successivo. L'unico input umano richiesto sono le preferenze iniziali
raccolte dal CEOAgent: da lì in poi la pipeline procede in autonomia.
"""

from ai_company.orchestrator import AICompany
from ai_company.models import Preferences

__all__ = ["AICompany", "Preferences"]
