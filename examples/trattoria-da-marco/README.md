# Trattoria da Marco

> Menù digitale e prenotazioni/ordini per il tuo ristorante

Trattoria a conduzione familiare nel centro di Bologna.

Questo progetto e' stato generato in autonomia da **AI Company**, una
pipeline di agenti AI specializzati (analisi, prodotto, architettura,
sviluppo, QA, DevOps, marketing).

## Funzionalita' incluse (MVP)

- menù digitale con categorie (antipasti, primi, secondi, dolci)
- gestione comande con stato (ricevuta, in cucina, servita)
- anagrafica clienti e prenotazioni

## Prossimi passi suggeriti (backlog)

- prenotazione tavoli
- menù allergeni
- asporto e delivery

## Stack tecnico

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite
- Jinja2 server-rendered templates
- CSS custom (nessuna dipendenza esterna)

## Avvio in locale

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Apri http://localhost:8000 nel browser.

## Test

```bash
pytest tests/ -v
```

## Deploy con Docker

```bash
docker compose up --build
```
