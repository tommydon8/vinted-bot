"""BusinessAnalystAgent — traduce il tipo di attività in requisiti concreti."""

from __future__ import annotations

from ai_company.agents.base import BaseAgent
from ai_company.business_profiles import get_profile
from ai_company.models import Preferences, RequirementsSpec


class BusinessAnalystAgent(BaseAgent):
    name = "Business Analyst Agent"
    role = "Analizza il tipo di attività e definisce i requisiti funzionali"

    def analyze(self, preferences: Preferences) -> RequirementsSpec:
        profile = get_profile(preferences.business_type)

        core = list(profile["core_features"])
        nice_to_have = list(profile["nice_to_have_features"])

        if not preferences.enable_online_orders:
            core = [f for f in core if "ordini" not in f and "comande" not in f and "richieste" not in f]
        if not preferences.enable_customer_accounts:
            core = [f for f in core if "clienti" not in f and "account" not in f]

        return RequirementsSpec(
            business_type=preferences.business_type,
            entity_labels=profile["entity_labels"],
            core_features=core,
            nice_to_have_features=nice_to_have,
        )
