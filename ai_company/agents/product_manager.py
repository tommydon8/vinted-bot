"""ProductManagerAgent — trasforma i requisiti in un piano prodotto (MVP + backlog)."""

from __future__ import annotations

from ai_company.agents.base import BaseAgent
from ai_company.models import Preferences, ProductPlan, RequirementsSpec


class ProductManagerAgent(BaseAgent):
    name = "Product Manager Agent"
    role = "Definisce l'MVP, il backlog e le user story"

    def plan(self, preferences: Preferences, requirements: RequirementsSpec) -> ProductPlan:
        labels = requirements.entity_labels

        user_stories = [
            f"Come visitatore, voglio consultare {labels['item_plural'].lower()} disponibili "
            f"cosi' da valutare cosa acquistare/richiedere.",
        ]
        if preferences.enable_online_orders:
            user_stories.append(
                f"Come cliente, voglio creare {labels['order_plural'].lower()} online "
                f"e vederne lo stato di avanzamento."
            )
        if preferences.enable_customer_accounts:
            user_stories.append(
                f"Come titolare, voglio consultare l'anagrafica {labels['customer_plural'].lower()} "
                f"per contattarli."
            )
        user_stories.append(
            f"Come titolare, voglio gestire (creare/modificare/rimuovere) i "
            f"{labels['item_plural'].lower()} dal pannello."
        )

        return ProductPlan(
            mvp_features=requirements.core_features,
            backlog=requirements.nice_to_have_features,
            user_stories=user_stories,
        )
