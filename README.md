# ⚡ SQL Query Agent — Self-Correcting NL → SQL (MySQL)

A Flask web app that converts natural language to SQL, executes it against your MySQL database, and **automatically self-corrects on failure** — with minimal LLM calls.

---

## How It Works

```
Your Question
      │
      ▼
 LLM Call #1 ──► Generate SQL
      │
      ▼
 Execute on MySQL ──► ✅ Success → Return results       (1 LLM call total)
      │
    ❌ Error
      │
      ▼
 LLM Call #2 ──► Fix SQL
 (sends: original question + failed SQL + error message)
      │
      ▼
 Execute on MySQL ──► ✅ Success → Return results       (2 LLM calls total)
      │
    ❌ Error  (repeats up to MAX_RETRIES = 3)
      │
      ▼
    Fatal — give up after 4 total LLM calls max
```

**LLM call budget:**

| Scenario | Calls Used |
|---|---|
| SQL correct first try | **1** |
| 1 correction needed | **2** |
| 2 corrections needed | **3** |
| Max retries exhausted | **4** |

---

## Features

- 🧠 Natural language → MySQL SQL via `gpt-3.5-turbo`
- 🔁 Self-correction loop — error + failed SQL sent back to LLM for fixing
- 📡 Real-time step-by-step streaming via **Server-Sent Events (SSE)**
- 🗄️ Connects to any existing **MySQL** database
- 🔐 Environment variable config via `.env` + `python-dotenv`
- 📊 Auto-serializes MySQL `Decimal` and `Date`/`Datetime` types to JSON
- 🎨 Terminal-aesthetic UI with syntax-highlighted SQL

---

## Project Structure

```
sql-agent/
├── app.py               # Flask app + agent + DB logic
├── templates/
│   └── index.html       # Frontend UI  ← must be inside templates/
├── requirements.txt     # Python dependencies
├── start.sh             # One-command startup script
├── .env                 # Your secrets (create this, don't commit it)
└── README.md
```

> ⚠️ `index.html` **must** be inside the `templates/` folder or Flask will throw `TemplateNotFound`.

---

## Prerequisites

- Python 3.8+
- A running **MySQL** server
- Database already created with tables present

---

## Setup

### 1. Create your `.env` file

Create a file named `.env` in the project root:

```env
CHATANYWHERE_API_KEY=sk-your-key-here
CHATANYWHERE_API_URL=https://api.chatanywhere.tech/v1/chat/completions

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password123
MYSQL_DATABASE=EmployeeDB
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python app.py
```

Or use the startup script (installs deps + runs):

```bash
bash start.sh
```

Open **http://localhost:5000**

---

## Requirements

```
flask
requests
mysql-connector-python
python-dotenv
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CHATANYWHERE_API_KEY` | `sk-ejE` | Your API key |
| `CHATANYWHERE_API_URL` | `https://api.chatanywhere.tech/...` | LLM API endpoint |
| `MYSQL_HOST` | `localhost` | MySQL server hostname |
| `MYSQL_PORT` | `3306` | MySQL server port |
| `MYSQL_USER` | `app_user` | MySQL username |
| `MYSQL_PASSWORD` | `app_password123` | MySQL password |
| `MYSQL_DATABASE` | `EmployeeDB` | Target database name |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `GET` | `/schema` | Returns full DB schema as JSON |
| `GET` | `/query?q=your+question` | SSE stream — runs the NL→SQL agent |
| `POST` | `/execute` | Runs raw SQL directly — body: `{"sql": "SELECT ..."}` |

---

## Schema Detection

On every query, the app auto-reads your database schema including:

- All table names, column names, and data types
- Foreign key relationships

This schema is injected into the LLM system prompt so it understands your data without you having to describe it manually.

---

## Demo Data (EmployeeDB)

If your `customers` table is empty on startup, the app inserts sample data automatically via `init_demo_db()`.

**Tables seeded:**

| Table | Rows | Description |
|---|---|---|
| `customers` | 5 | Name, email, city, join date |
| `products` | 6 | Electronics, Furniture, Stationery |
| `orders` | 10 | Links customers + products, with status |

**Order statuses:** `pending` · `shipped` · `delivered` · `cancelled`

**Sample queries to try:**
- *"Top 3 customers by total spending"*
- *"All pending orders with customer names"*
- *"Products with stock under 20"*
- *"Revenue by product category"*
- *"Customers who have never placed an order"*
- *"Monthly order count in 2024"*

---

## Troubleshooting

**`❌ Failed to connect to MySQL`**
→ Check `.env` credentials and confirm MySQL is running:
```bash
mysql -h localhost -u app_user -p
```

**`TemplateNotFound: index.html`**
→ `index.html` must be inside a `templates/` subfolder next to `app.py`:
```bash
mkdir templates && mv index.html templates/
```

**`ModuleNotFoundError`**
→ Run `pip install -r requirements.txt`

**LLM returns SQL wrapped in backticks**
→ Handled automatically — markdown fences are stripped before execution.

**`init_demo_db()` fails with table not found**
→ The tables (`customers`, `products`, `orders`) must already exist in MySQL. Create them first, then the app will populate them with sample data.

---

## Windows

```cmd
set CHATANYWHERE_API_KEY=sk-your-key
set MYSQL_HOST=localhost
set MYSQL_DATABASE=EmployeeDB
python app.py
```

Or create the `.env` file — `python-dotenv` loads it automatically on all platforms.
