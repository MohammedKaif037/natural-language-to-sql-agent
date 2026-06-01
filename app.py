import os
import json
import mysql.connector
from mysql.connector import Error
import requests
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
CHATANYWHERE_API_KEY = os.getenv("CHATANYWHERE_API_KEY", "sk-ejE")
CHATANYWHERE_API_URL = os.getenv("CHATANYWHERE_API_URL", "https://api.chatanywhere.tech/v1/chat/completions")
MODEL = "gpt-3.5-turbo"
MAX_RETRIES = 3

# MySQL Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'app_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'app_password123'),
    'database': os.getenv('MYSQL_DATABASE', 'EmployeeDB'),
    'port': int(os.getenv('MYSQL_PORT', 3306))
}

# ── Database Functions ───────────────────────────────────────────────────────
def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_schema():
    """Get database schema information"""
    connection = get_db_connection()
    if not connection:
        return "Unable to connect to database"
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get all tables - MySQL uses uppercase column names
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
        """, (MYSQL_CONFIG['database'],))
        
        tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        
        schema_parts = []
        for table in tables:
            # Get column information
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ORDINAL_POSITION
            """, (MYSQL_CONFIG['database'], table))
            
            columns = cursor.fetchall()
            col_defs = ", ".join([f"{col['COLUMN_NAME']} {col['DATA_TYPE']}" for col in columns])
            
            # Get foreign key information
            cursor.execute("""
                SELECT 
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE kcu
                WHERE kcu.CONSTRAINT_SCHEMA = %s 
                AND kcu.TABLE_NAME = %s
                AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """, (MYSQL_CONFIG['database'], table))
            
            foreign_keys = cursor.fetchall()
            fk_defs = []
            for fk in foreign_keys:
                fk_defs.append(f"FOREIGN KEY ({fk['COLUMN_NAME']}) REFERENCES {fk['REFERENCED_TABLE_NAME']}({fk['REFERENCED_COLUMN_NAME']})")
            
            if fk_defs:
                col_defs += ", " + ", ".join(fk_defs)
            
            schema_parts.append(f"  {table}({col_defs})")
        
        cursor.close()
        connection.close()
        return "Tables:\n" + "\n".join(schema_parts)
    
    except Error as e:
        cursor.close()
        connection.close()
        return f"Error getting schema: {e}"

def execute_sql(sql):
    """Execute SQL query and return results"""
    connection = get_db_connection()
    if not connection:
        return {"success": False, "error": "Database connection failed"}
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(sql)
        
        # Check if it's a SELECT query
        if sql.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            # Convert Decimal and Date objects to serializable types
            for row in rows:
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):  # Handle date/datetime objects
                        row[key] = str(value)
                    elif hasattr(value, 'to_eng_string'):  # Handle Decimal objects
                        row[key] = float(value)
            connection.close()
            return {"success": True, "rows": rows, "count": len(rows)}
        else:
            # For INSERT, UPDATE, DELETE queries
            connection.commit()
            affected_rows = cursor.rowcount
            connection.close()
            return {"success": True, "message": f"Query executed successfully", "affected_rows": affected_rows}
    
    except Error as e:
        connection.close()
        return {"success": False, "error": str(e)}

def init_demo_db():
    """Initialize the database with sample data"""
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to MySQL database")
        return False
    
    cursor = connection.cursor()
    
    try:
        # Check if tables exist and have data
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        customer_count = cursor.fetchone()[0]
        
        if customer_count == 0:
            print("📊 Inserting sample data...")
            # Insert customers
            customers_data = [
                (1, 'Priya Sharma', 'priya@example.com', 'Bengaluru', '2023-01-10'),
                (2, 'Rahul Verma', 'rahul@example.com', 'Mumbai', '2023-03-22'),
                (3, 'Ananya Nair', 'ananya@example.com', 'Mysuru', '2022-11-05'),
                (4, 'Kiran Patel', 'kiran@example.com', 'Ahmedabad', '2024-02-14'),
                (5, 'Sneha Rao', 'sneha@example.com', 'Hyderabad', '2023-07-30')
            ]
            
            cursor.executemany("""
                INSERT IGNORE INTO customers (id, name, email, city, joined_date) 
                VALUES (%s, %s, %s, %s, %s)
            """, customers_data)
            
            # Insert products
            products_data = [
                (1, 'Laptop Pro 15', 'Electronics', 85000, 12),
                (2, 'Wireless Earbuds', 'Electronics', 3500, 200),
                (3, 'Office Chair', 'Furniture', 12000, 45),
                (4, 'Standing Desk', 'Furniture', 25000, 20),
                (5, 'Notebook Set', 'Stationery', 450, 500),
                (6, 'Mechanical Keyboard', 'Electronics', 6500, 80)
            ]
            
            cursor.executemany("""
                INSERT IGNORE INTO products (id, name, category, price, stock) 
                VALUES (%s, %s, %s, %s, %s)
            """, products_data)
            
            # Insert orders
            orders_data = [
                (1, 1, 1, 1, 85000, 'delivered', '2024-01-15'),
                (2, 1, 2, 2, 7000, 'delivered', '2024-01-20'),
                (3, 2, 3, 1, 12000, 'shipped', '2024-02-10'),
                (4, 3, 1, 1, 85000, 'pending', '2024-03-01'),
                (5, 3, 6, 1, 6500, 'delivered', '2024-03-05'),
                (6, 4, 5, 10, 4500, 'delivered', '2024-03-10'),
                (7, 5, 4, 1, 25000, 'shipped', '2024-03-15'),
                (8, 2, 2, 3, 10500, 'cancelled', '2024-03-20'),
                (9, 1, 4, 1, 25000, 'pending', '2024-04-01'),
                (10, 5, 6, 2, 13000, 'delivered', '2024-04-05')
            ]
            
            cursor.executemany("""
                INSERT IGNORE INTO orders (id, customer_id, product_id, quantity, total_amount, status, order_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, orders_data)
            
            connection.commit()
            print("✅ Sample data inserted successfully")
        
        cursor.close()
        connection.close()
        return True
    
    except Error as e:
        print(f"❌ Error initializing database: {e}")
        cursor.close()
        connection.close()
        return False

# ── LLM call ─────────────────────────────────────────────────────────────────
def call_llm(messages):
    """Call the LLM API"""
    resp = requests.post(
        CHATANYWHERE_API_URL,
        headers={"Authorization": f"Bearer {CHATANYWHERE_API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

# ── Core agent ────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SQL assistant for a MySQL database.

{schema}

Rules:
- Return ONLY the raw SQL query, no markdown, no explanation, no backticks.
- Use standard MySQL syntax.
- Always use table aliases when joining.
- Use CONCAT for string concatenation if needed.
- For LIMIT, use proper MySQL syntax.
- Use DATE_FORMAT for date formatting if needed.
- For aggregations, always alias columns (e.g. COUNT(*) AS total).
- If the question is ambiguous, write the most reasonable query."""

FIX_PROMPT = """The SQL query below failed with an error. Fix it and return ONLY the corrected SQL.

Original question: {question}

Failed SQL:
{sql}

Error:
{error}

Return ONLY the fixed SQL query, nothing else."""

def nl_to_sql_agent(question: str):
    """
    Core agent loop — returns a generator of SSE-style events.
    """
    schema = get_schema()
    system = SYSTEM_PROMPT.format(schema=schema)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question}
    ]

    def event(kind, data):
        return f"data: {json.dumps({'type': kind, **data})}\n\n"

    # Step 1: Generate initial SQL
    yield event("step", {"msg": "🤔 Generating SQL from your question...", "llm_call": 1})
    try:
        sql = call_llm(messages)
    except Exception as e:
        yield event("error", {"msg": f"LLM error: {e}"})
        return

    # Strip accidental markdown fences
    sql = sql.strip().lstrip("```sql").lstrip("```").rstrip("```").strip()
    yield event("sql", {"sql": sql, "attempt": 1})

    # Step 2: Execute & self-correct loop
    for attempt in range(1, MAX_RETRIES + 1):
        yield event("step", {"msg": f"⚡ Executing SQL (attempt {attempt})..."})
        result = execute_sql(sql)

        if result["success"]:
            yield event("result", {
                "rows": result.get("rows", []),
                "count": result.get("count", 0),
                "total_llm_calls": attempt
            })
            return

        # Failed — ask LLM to fix it
        error_msg = result["error"]
        yield event("error_sql", {"error": error_msg, "attempt": attempt})

        if attempt == MAX_RETRIES:
            yield event("fatal", {"msg": f"❌ Failed after {MAX_RETRIES} attempts.", "last_error": error_msg})
            return

        yield event("step", {"msg": f"🔧 Asking LLM to fix error (LLM call #{attempt + 1})...", "llm_call": attempt + 1})
        fix_messages = [
            {"role": "system", "content": "You are an expert SQL debugger. Return ONLY fixed SQL."},
            {"role": "user", "content": FIX_PROMPT.format(question=question, sql=sql, error=error_msg)}
        ]
        try:
            sql = call_llm(fix_messages)
            sql = sql.strip().lstrip("```sql").lstrip("```").rstrip("```").strip()
        except Exception as e:
            yield event("fatal", {"msg": f"LLM error during fix: {e}"})
            return

        yield event("sql", {"sql": sql, "attempt": attempt + 1})

# ── Flask Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/schema")
def schema():
    return jsonify({"schema": get_schema()})

@app.route("/query")
def query():
    question = request.args.get("q", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    def generate():
        for chunk in nl_to_sql_agent(question):
            yield chunk

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/execute", methods=["POST"])
def execute():
    sql = request.json.get("sql", "").strip()
    if not sql:
        return jsonify({"error": "No SQL provided"}), 400
    return jsonify(execute_sql(sql))

if __name__ == "__main__":
    # Test database connection
    if init_demo_db():
        print("✅ MySQL database initialized/verified")
    else:
        print("❌ Failed to initialize MySQL database")
        exit(1)
    
    print("🚀 Starting SQL Agent on http://localhost:5000")
    app.run(debug=True, port=5000)