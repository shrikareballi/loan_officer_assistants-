# Ledgerwise Accounts Payable Agent

Ledgerwise reviews supplier invoices against purchase orders and vendor history. It uses explicit, explainable checks for duplicate invoices, purchase-order variance, payment-term changes, past-due invoices, and recurring vendor exceptions. Hindsight retrieves and reflects on vendor-specific, human-confirmed cases; cited memories can influence the risk score and review guidance.

The prototype never releases or schedules a payment. A person records the final decision and the resolution that the agent can learn from.

## Hackathon story

Use the Northstar Office Supply demo cases to show the learning loop:

1. The demo workspace starts with two fictional, resolved Northstar invoice exceptions. If Hindsight is running at startup, these cases are also retained in the `accounts-payable-demo` bank under strict AP and vendor tags.
2. Submit a new Northstar invoice for `$5,320` against a `$5,000` purchase order. The agent compares the 6.4% variance with the configured 2% tolerance, reads the local case history, and asks Hindsight to reflect only on Northstar's tagged memories.
3. Review the risk factors, Hindsight summary, and the source cases used for that summary.
4. Record what the AP reviewer decided and why. The confirmed resolution is saved in SQLite and retained in Hindsight for later reviews.

This gives the demo a clear before-and-after: the first case is resolved by a person; a later case can use that accumulated vendor experience.

## Features

- React and Recharts dashboard for the AP queue, portfolio summary, invoice history, and vendor profiles.
- FastAPI service with validated request models and documented endpoints at `/docs`.
- SQLite audit log with duplicate protection, stored rule factors, decisions, and resolutions.
- Explainable risk score from purchase-order variance, duplicate detection, changed vendor terms, late due dates, repeat local exceptions, and grounded Hindsight patterns.
- Hindsight `reflect` is filtered with strict AP and vendor tags. Its structured recommendation affects the review score only when Hindsight returns source memories; the UI shows those sources.
- Human decisions are retained as memories with an invoice document ID, supporting repeatable demo runs.
- Synthetic data only. No live accounting, payment, or bank integration.

## Project structure

```text
backend/app/
  main.py                 FastAPI routes and startup flow
  database.py             SQLite schema, demo history, and repository functions
  schemas.py              Validated API input and response models
  services/
    memory.py             Hindsight retain and vendor-scoped reflect
    review.py              Explainable risk scoring and recommendations
frontend/src/
  App.jsx                  Portfolio dashboard and navigation
  api.js                   Frontend API client
  components/              Invoice table and review forms
  index.css                Responsive dashboard styling
```

## Requirements

- Python 3.10+
- Node.js 18 or newer and npm
- A Hindsight server with an LLM provider configured, or a Hindsight Cloud endpoint and API key

## Local setup on Windows

From this project folder, create the backend environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Start a local Hindsight server in another PowerShell window. This example uses Docker and an OpenAI key for Hindsight's memory extraction and reflection:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
docker run -it --pull always --name hindsight -p 8888:8888 -p 9999:9999 `
  -e HINDSIGHT_API_LLM_API_KEY=$env:OPENAI_API_KEY `
  -v hindsight-data:/home/hindsight/.pg0 `
  ghcr.io/vectorize-io/hindsight:latest
```

For other providers and hosted memory, use the [official Hindsight quick start](https://github.com/vectorize-io/hindsight#quick-start). Set `HINDSIGHT_URL` and, when needed, `HINDSIGHT_API_KEY` in `.env`. Keep the bank ID stable between runs so the agent can recall its prior cases.

Run the API in a second terminal from the project folder:

```powershell
.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Install and run the React dashboard in a third terminal:

```powershell
cd frontend
npm install
npm run dev
```

The included `pnpm-lock.yaml` can also be used with `pnpm install`.

Open `http://127.0.0.1:5173`. The API documentation is at `http://127.0.0.1:8000/docs`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `HINDSIGHT_URL` | `http://localhost:8888` | Hindsight API address |
| `HINDSIGHT_API_KEY` | empty | Optional API key for hosted Hindsight |
| `HINDSIGHT_BANK_ID` | `accounts-payable-demo` | Isolated memory bank for this workspace |
| `AP_DATABASE_PATH` | `backend/data/ap_agent.db` | SQLite audit log location |
| `AP_AMOUNT_TOLERANCE_PCT` | `2.0` | Allowed invoice/PO variance before a flag |

Use fictional invoice data for a hackathon demo. Do not retain bank credentials or unnecessary personal information in the memory bank.

## API overview

- `GET /api/health` — backend and memory-bank configuration
- `GET /api/dashboard` — portfolio metrics and recent invoices
- `GET /api/invoices` — invoice review queue
- `POST /api/invoices/review` — review and record a new invoice
- `GET /api/invoices/{id}` — one invoice with its evidence
- `POST /api/invoices/{id}/resolve` — record a human outcome and retain it in Hindsight
- `GET /api/vendors` — vendor history profiles
- `GET /api/vendors/{vendor}/memory` — scoped Hindsight reflection with source facts

## Scope and judging demo notes

This is a hackathon prototype, not a production accounting system. It does not perform OCR, connect to ERP or bank software, or authorize payments. Before a live demo, start Hindsight and use a fresh demo database so the sample learning sequence is easy to follow. The app keeps risk scoring deterministic and visible; Hindsight adds grounded historical context rather than silently deciding whether an invoice is payable.
