# AI Company 🏢

Una "compagnia" di agenti AI che progetta, sviluppa, testa e prepara al
deploy — **in completa autonomia** — una startup software su misura per
un negozio, un ristorante, un'azienda di servizi o qualunque altra
attività in cui sia possibile digitalizzare catalogo, ordini e clienti.

L'unico intervento umano richiesto è rispondere a poche domande
iniziali (nome dell'attività, tipo, colore del brand, funzionalità
desiderate). Da quel momento la pipeline di agenti lavora da sola fino
a consegnare un progetto completo, testato e pronto per il deploy.

## I nove agenti

Ogni agente ha una responsabilità unica e passa il proprio output
all'agente successivo:

| # | Agente | Compito |
|---|--------|---------|
| 1 | **CEO Agent** | Unico punto di contatto con l'utente: raccoglie le preferenze iniziali e fissa l'obiettivo della company |
| 2 | **Business Analyst Agent** | Traduce il tipo di attività in requisiti funzionali concreti (terminologia, feature core, nice-to-have) |
| 3 | **Product Manager Agent** | Definisce l'MVP, il backlog e le user story |
| 4 | **Architect Agent** | Sceglie lo stack tecnico e progetta il modello dati |
| 5 | **Backend Developer Agent** | Genera un backend FastAPI + SQLAlchemy funzionante (API REST, modelli, persistenza) |
| 6 | **Frontend Developer Agent** | Genera i template Jinja2 e il tema grafico (colore del brand incluso) |
| 7 | **QA Engineer Agent** | Scrive una suite di test automatici e la esegue davvero contro il backend generato |
| 8 | **DevOps Agent** | Prepara Dockerfile, `docker-compose.yml`, `requirements.txt` e configurazione di deploy |
| 9 | **Marketing Agent** | Scrive branding, pitch e README del progetto finale |

L'orchestratore (`ai_company/orchestrator.py`, classe `AICompany`)
esegue questi nove passaggi in sequenza e produce un `CompanyReport`
con il log di ogni agente e l'esito dei test.

## Tipi di attività supportati

Il catalogo in `business_profiles.py` definisce come i concetti
generici del modello dati (catalogo / ordini / clienti) vengono
"etichettati" per ogni tipo di attività:

- **negozio** → Prodotti, Ordini, Clienti
- **ristorante** → Menù, Comande, Clienti
- **azienda** → Servizi, Richieste, Clienti
- **altro** → profilo generico di fallback

Aggiungere un nuovo tipo di attività richiede solo una nuova voce in
`BUSINESS_PROFILES`: il resto della pipeline (requisiti, user story,
codice generato) si adatta automaticamente.

## Utilizzo

### Modalità interattiva (consigliata)

```bash
pip install -r ai_company/requirements.txt
python -m ai_company.cli
```

Il CEO Agent farà alcune domande (nome attività, tipo, colore, se
abilitare ordini online e account clienti) e poi la company lavorerà
in autonomia, stampando il log di ogni agente e l'esito dei test.

### Modalità programmatica

```python
from pathlib import Path
from ai_company.models import Preferences
from ai_company.orchestrator import AICompany

preferences = Preferences(
    business_name="Trattoria da Marco",
    business_type="ristorante",       # negozio | ristorante | azienda | altro
    description="Trattoria a conduzione familiare.",
    primary_color="#b91c1c",
    output_dir=Path("generated_projects"),
)

report = AICompany().run(preferences)
print(report.pretty_print())
```

### Il progetto generato

Ogni startup generata è un'app FastAPI autonoma e pronta all'uso:

```bash
cd generated_projects/<slug>
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000
pytest tests/ -v                # suite generata dal QA Engineer Agent
docker compose up --build       # deploy containerizzato
```

Un esempio già generato (attività "ristorante") si trova in
[`examples/trattoria-da-marco`](../examples/trattoria-da-marco).

## Test del framework

```bash
pytest tests/test_ai_company.py -v
```

Verifica, per ciascun tipo di attività, che la pipeline produca tutti i
file attesi e che i test generati dal QA Engineer Agent passino
realmente contro il backend appena creato.
