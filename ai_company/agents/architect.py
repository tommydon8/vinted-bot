"""ArchitectAgent — sceglie lo stack tecnico e progetta il modello dati."""

from __future__ import annotations

from ai_company.agents.base import BaseAgent
from ai_company.models import ArchitectureSpec, Preferences, ProductPlan


class ArchitectAgent(BaseAgent):
    name = "Architect Agent"
    role = "Sceglie lo stack tecnologico e progetta il modello dati"

    def design(self, preferences: Preferences, plan: ProductPlan) -> ArchitectureSpec:
        data_model = {
            "Item": ["id", "name", "description", "price", "category", "available"],
            "Customer": ["id", "name", "email", "phone"] if preferences.enable_customer_accounts else [],
            "Order": (
                ["id", "customer_id", "status", "created_at"]
                if preferences.enable_online_orders
                else []
            ),
            "OrderItem": (
                ["id", "order_id", "item_id", "quantity"]
                if preferences.enable_online_orders
                else []
            ),
        }
        data_model = {k: v for k, v in data_model.items() if v}

        return ArchitectureSpec(
            backend_stack=["Python 3.11+", "FastAPI", "SQLAlchemy", "SQLite"],
            frontend_stack=["Jinja2 server-rendered templates", "CSS custom (nessuna dipendenza esterna)"],
            data_model=data_model,
            deployment_target="Docker + Uvicorn (compatibile Railway/Render/Fly.io)",
        )
