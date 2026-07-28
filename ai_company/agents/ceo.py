"""CEOAgent — unico punto di contatto con l'utente umano.

Raccoglie le preferenze iniziali (interattivamente da CLI, oppure
programmaticamente) e le trasforma in un oggetto Preferences che guida
il resto della pipeline. Nessun altro agente interagisce con l'utente:
da qui in poi la company procede in autonomia.
"""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.business_profiles import BUSINESS_PROFILES
from ai_company.models import Preferences


class CEOAgent(BaseAgent):
    name = "CEO Agent"
    role = "Raccoglie le preferenze dell'utente e fissa l'obiettivo della company"

    def collect_preferences_interactively(self) -> Preferences:
        print("=== 🏢 AI Company — costruiamo la tua startup software ===\n")

        business_name = input("Nome dell'attività/startup: ").strip() or "La Mia Attività"

        types = list(BUSINESS_PROFILES.keys())
        print("\nTipo di attività:")
        for i, t in enumerate(types, 1):
            print(f"  {i}. {t} ({BUSINESS_PROFILES[t]['display_name']})")
        choice = input(f"Scegli [1-{len(types)}] (default: altro): ").strip()
        try:
            business_type = types[int(choice) - 1]
        except (ValueError, IndexError):
            business_type = "altro"

        description = input("\nBreve descrizione dell'attività (opzionale): ").strip()
        primary_color = input("Colore principale del brand, es. #2563eb (invio per default): ").strip() or "#2563eb"

        online_orders = input("Abilitare ordini/richieste online? [S/n]: ").strip().lower()
        enable_online_orders = online_orders != "n"

        accounts = input("Abilitare account clienti? [S/n]: ").strip().lower()
        enable_customer_accounts = accounts != "n"

        return Preferences(
            business_name=business_name,
            business_type=business_type,
            description=description,
            primary_color=primary_color,
            enable_online_orders=enable_online_orders,
            enable_customer_accounts=enable_customer_accounts,
        )

    def kickoff(self, preferences: Preferences) -> str:
        """Definisce l'obiettivo che verrà comunicato a tutti gli altri agenti."""
        return (
            f"Costruire in autonomia una startup software per "
            f"'{preferences.business_name}' ({preferences.business_type}), "
            f"pronta per essere mostrata e messa in produzione."
        )
