# ⚡ SQL Query Agent — Self-Correcting NL → SQL

A Flask web app that converts natural language to SQL, executes it, and self-corrects on failure — with a minimal number of LLM calls.

## Architecture

```
User Question
     │
     ▼
 LLM Call #1 ──► Generate SQL
     │
     ▼
 Execute SQL ──► Success? ──► Return results (1 LLM call)
     │
   Error
     │
     ▼
 LLM Call #2 ──► Fix SQL (sends original question + failed SQL + error)
     │
     ▼
 Execute SQL ──► Success? ──► Return results (2 LLM calls)
     │
   Error (repeat up to MAX_RETRIES=3)
```

**LLM call budget:**
- Best case: **1 call** (correct SQL first try)
- Worst case: **1 + MAX_RETRIES = 4 calls**

## Features

- 🧠 NL → SQL via GPT-3.5-turbo (compatible with ChatAnywhere API)
- 🔁 Self-correction loop with error feedback passed back to LLM
- 📡 Server-Sent Events (SSE) for real-time streaming of each step
- 🗃️ SQLite (drop-in, no setup) — swap `DB_PATH` for Postgres with `psycopg2`
- 🎨 Terminal-aesthetic UI with syntax-highlighted SQL

## Quick Start

```bash
# Set your API key
export CHATANYWHERE_API_KEY=sk-your-key-here

# Run
bash start.sh
```

Then open **http://localhost:5000**

## Using Your Own Database

Edit `DB_PATH` in `app.py`:
```python
DB_PATH = "/path/to/your.db"  # SQLite
```

For Postgres, replace `execute_sql()` with `psycopg2`:
```python
import psycopg2
conn = psycopg2.connect("postgresql://user:pass@localhost/dbname")
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHATANYWHERE_API_KEY` | `sk-ejE` | Your API key |
| `CHATANYWHERE_API_URL` | `https://api.chatanywhere.tech/v1/chat/completions` | API endpoint |

## Demo Schema

The built-in demo includes:
- `customers` — 5 customers with cities and join dates
- `products` — 6 products across Electronics, Furniture, Stationery
- `orders` — 10 orders linking customers and products with statuses

Try these queries:
- "Top 3 customers by total spending"
- "Which products have never been ordered?"
- "Monthly revenue trend in 2024"
- "Show cancelled orders with customer emails"
