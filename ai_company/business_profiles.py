"""Catalogo dei profili di business.

Ogni profilo definisce come i concetti generici del modello dati
(Item / Customer / Order) vengono "etichettati" e quali funzionalità
sono rilevanti per quel tipo di attività. Aggiungere un nuovo tipo di
attività richiede solo una nuova voce in questo dizionario: il resto
della pipeline si adatta automaticamente.
"""

from __future__ import annotations

BUSINESS_PROFILES: dict[str, dict] = {
    "negozio": {
        "display_name": "Negozio",
        "tagline": "Vetrina online e gestione ordini per il tuo negozio",
        "entity_labels": {
            "item": "Prodotto",
            "item_plural": "Prodotti",
            "order": "Ordine",
            "order_plural": "Ordini",
            "customer": "Cliente",
            "customer_plural": "Clienti",
        },
        "core_features": [
            "catalogo prodotti con foto, prezzo e disponibilità",
            "gestione ordini con stato (ricevuto, in preparazione, spedito)",
            "anagrafica clienti",
        ],
        "nice_to_have_features": [
            "gestione magazzino/scorte",
            "codici sconto",
            "recensioni prodotto",
        ],
    },
    "ristorante": {
        "display_name": "Ristorante",
        "tagline": "Menù digitale e prenotazioni/ordini per il tuo ristorante",
        "entity_labels": {
            "item": "Piatto",
            "item_plural": "Menù",
            "order": "Comanda",
            "order_plural": "Comande",
            "customer": "Cliente",
            "customer_plural": "Clienti",
        },
        "core_features": [
            "menù digitale con categorie (antipasti, primi, secondi, dolci)",
            "gestione comande con stato (ricevuta, in cucina, servita)",
            "anagrafica clienti e prenotazioni",
        ],
        "nice_to_have_features": [
            "prenotazione tavoli",
            "menù allergeni",
            "asporto e delivery",
        ],
    },
    "azienda": {
        "display_name": "Azienda di servizi",
        "tagline": "Catalogo servizi e gestione richieste per la tua azienda",
        "entity_labels": {
            "item": "Servizio",
            "item_plural": "Servizi",
            "order": "Richiesta",
            "order_plural": "Richieste",
            "customer": "Cliente",
            "customer_plural": "Clienti",
        },
        "core_features": [
            "catalogo servizi con descrizione e listino prezzi",
            "gestione richieste/preventivi con stato",
            "anagrafica clienti",
        ],
        "nice_to_have_features": [
            "calendario appuntamenti",
            "fatturazione",
            "portale clienti con storico richieste",
        ],
    },
    "altro": {
        "display_name": "Attività generica",
        "tagline": "Piattaforma su misura per la tua attività",
        "entity_labels": {
            "item": "Articolo",
            "item_plural": "Catalogo",
            "order": "Ordine",
            "order_plural": "Ordini",
            "customer": "Cliente",
            "customer_plural": "Clienti",
        },
        "core_features": [
            "catalogo articoli/offerte",
            "gestione ordini/richieste con stato",
            "anagrafica clienti",
        ],
        "nice_to_have_features": [
            "notifiche email",
            "reportistica vendite",
        ],
    },
}


def get_profile(business_type: str) -> dict:
    return BUSINESS_PROFILES.get(business_type.lower().strip(), BUSINESS_PROFILES["altro"])
