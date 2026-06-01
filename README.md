Here's a complete README.md file for your SQL Agent application:

```markdown
# SQL Agent - Natural Language to SQL Assistant

An intelligent web application that converts natural language questions into SQL queries and executes them against a MySQL database. Powered by LLM (GPT-3.5-turbo) with self-correction capabilities.

## Features

- 🔄 **Natural Language to SQL**: Convert plain English questions into SQL queries
- 🤖 **LLM Integration**: Uses GPT-3.5-turbo for intelligent query generation
- 🔧 **Self-Correction**: Automatically fixes SQL errors with up to 3 retry attempts
- 📊 **Real-time Streaming**: Server-Sent Events (SSE) for live query generation updates
- 🗄️ **MySQL Support**: Full MySQL database integration with schema introspection
- 📦 **Demo Database**: Automatic sample data initialization for testing
- 🎨 **Web Interface**: Clean, responsive HTML interface
- 🔌 **REST API**: Programmatic access to SQL generation and execution

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **LLM API**: ChatAnywhere API (OpenAI-compatible)
- **Frontend**: HTML, CSS, JavaScript (EventSource for SSE)

## Prerequisites

- Python 3.8+
- MySQL Server 5.7+
- ChatAnywhere API key (or any OpenAI-compatible API)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sql-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Database

Create a database and user:

```sql
CREATE DATABASE EmployeeDB;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'app_password123';
GRANT ALL PRIVILEGES ON EmployeeDB.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
# ChatAnywhere API Configuration
CHATANYWHERE_API_KEY=your-api-key-here
CHATANYWHERE_API_URL=https://api.chatanywhere.tech/v1/chat/completions

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password123
MYSQL_DATABASE=EmployeeDB
MYSQL_PORT=3306
```

### 6. Database Schema Setup

The application will automatically create and populate the following tables with sample data on first run:

- **customers**: Customer information (id, name, email, city, joined_date)
- **products**: Product catalog (id, name, category, price, stock)
- **orders**: Order transactions (id, customer_id, product_id, quantity, total_amount, status, order_date)

## Running the Application

```bash
python app.py
```

The application will:
1. Connect to MySQL database
2. Initialize sample data if tables are empty
3. Start Flask server on `http://localhost:5000`

## Usage

### Web Interface

Open your browser and navigate to `http://localhost:5000`

Example questions to try:
- "Show all customers from Bengaluru"
- "What is the total sales amount for each product?"
- "List orders with customer names and product details"
- "Which customer has spent the most money?"
- "Show all products with stock less than 50"

### API Endpoints

#### 1. Generate SQL from Natural Language (Streaming)

```bash
curl -N "http://localhost:5000/query?q=Show all customers"
```

Response (Server-Sent Events):
```json
data: {"type": "step", "msg": "🤔 Generating SQL from your question...", "llm_call": 1}

data: {"type": "sql", "sql": "SELECT * FROM customers", "attempt": 1}

data: {"type": "result", "rows": [...], "count": 5, "total_llm_calls": 1}
```

#### 2. Execute Raw SQL

```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM customers"}'
```

Response:
```json
{
  "success": true,
  "rows": [...],
  "count": 5
}
```

#### 3. Get Database Schema

```bash
curl http://localhost:5000/schema
```

## Architecture

### Core Components

1. **Database Layer** (`get_db_connection()`, `execute_sql()`)
   - Manages MySQL connections
   - Executes queries with proper error handling
   - Handles data type serialization (Decimal, Date objects)

2. **Schema Introspection** (`get_schema()`)
   - Retrieves table structures
   - Fetches column definitions and data types
   - Identifies foreign key relationships

3. **LLM Integration** (`call_llm()`)
   - Communicates with ChatAnywhere API
   - Configurable model and temperature settings
   - Error handling and retry logic

4. **SQL Agent** (`nl_to_sql_agent()`)
   - Core logic for NL to SQL conversion
   - Self-correction loop with up to 3 attempts
   - Streaming events for real-time feedback

5. **Flask Routes**
   - `GET /` - Web interface
   - `GET /query` - NL to SQL conversion
   - `POST /execute` - Raw SQL execution
   - `GET /schema` - Database schema

### Self-Correction Flow

1. User submits natural language question
2. LLM generates initial SQL query
3. System attempts to execute the query
4. If successful → Return results
5. If error → Send error to LLM with original question
6. LLM generates corrected SQL
7. Repeat steps 3-6 up to 3 times

## Configuration Options

| Environment Variable | Default Value | Description |
|---------------------|---------------|-------------|
| `CHATANYWHERE_API_KEY` | `sk-ejE` | API key for LLM service |
| `CHATANYWHERE_API_URL` | `https://api.chatanywhere.tech/v1/chat/completions` | LLM API endpoint |
| `MYSQL_HOST` | `localhost` | MySQL server host |
| `MYSQL_USER` | `app_user` | MySQL username |
| `MYSQL_PASSWORD` | `app_password123` | MySQL password |
| `MYSQL_DATABASE` | `EmployeeDB` | Database name |
| `MYSQL_PORT` | `3306` | MySQL port |

## Customization

### Changing the LLM Model

Modify the `MODEL` variable in `app.py`:

```python
MODEL = "gpt-4"  # or any other supported model
```

### Adjusting Retry Attempts

Change the `MAX_RETRIES` variable:

```python
MAX_RETRIES = 5  # Increase retry attempts
```

### Custom System Prompt

Modify the `SYSTEM_PROMPT` to change SQL generation behavior:

```python
SYSTEM_PROMPT = """Your custom prompt here..."""
```

## Troubleshooting

### Database Connection Issues

```bash
# Test MySQL connection
mysql -h localhost -u app_user -p
```

### LLM API Errors

- Verify API key is valid
- Check API endpoint URL
- Ensure internet connectivity

### Sample Data Not Loading

The `init_demo_db()` function checks if tables have data. To force re-initialization:

```sql
TRUNCATE customers;
TRUNCATE products;
TRUNCATE orders;
```

Then restart the application.

## Security Considerations

⚠️ **Important**: This application is designed for development and educational purposes. For production:

1. **Disable debug mode**: Set `debug=False` in `app.run()`
2. **Use environment variables**: Never hardcode credentials
3. **Add authentication**: Implement user authentication
4. **Rate limiting**: Add request throttling
5. **SQL injection**: Although queries are generated by LLM, consider adding validation
6. **HTTPS**: Use HTTPS in production
7. **API key rotation**: Regularly rotate API keys

## Project Structure

```
sql-agent/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── templates/
│   └── index.html     # Web interface
└── README.md          # Documentation
```

## Dependencies

```
flask
mysql-connector-python
requests
python-dotenv
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ChatAnywhere for providing LLM API access
- Flask framework for web capabilities
- MySQL for database management

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Open an issue on GitHub

---

**Note**: This application uses external LLM APIs which may incur costs. Monitor your API usage accordingly.
```

Additionally, create a `requirements.txt` file:

```txt
Flask==2.3.3
mysql-connector-python==8.1.0
requests==2.31.0
python-dotenv==1.0.0
```

And a simple `templates/index.html` file is expected by the Flask application. You can create a basic HTML interface that uses EventSource to connect to `/query` endpoint and display results.

This README provides comprehensive documentation covering installation, usage, architecture, customization, and troubleshooting for your SQL Agent application.