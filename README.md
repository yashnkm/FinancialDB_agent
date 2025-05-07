# Financial Transaction Analysis System

A conversational AI agent for analyzing financial transaction data and providing insights through natural language interaction.

## Project Overview

This system provides a chat interface that allows users to analyze financial transaction data through natural language queries. The agent can retrieve general information about transaction types, interpret transaction status codes, and perform database queries to find and analyze specific transactions.

The project was adapted from a pharmaceutical distributor system to focus on financial transaction analysis, with custom components for handling transaction data and financial business logic.

## Key Features

- **Natural Language Querying**: Users can ask questions about transactions in plain English
- **Transaction Analysis**: Identify transaction types, status, and patterns
- **Financial Data Retrieval**: Query transaction records from a database
- **Transaction Status Interpretation**: Understand approval codes and transaction types
- **Interactive Web Interface**: User-friendly chat UI for interacting with the system

## System Architecture

The system consists of these main components:

1. **Web Interface**: A Flask-based web application providing a chat interface
2. **AI Agent**: LangChain-based ReAct agent powered by Google's Gemini model
3. **RAG System**: Retrieval-Augmented Generation for providing information about transactions
4. **Database Connection**: PostgreSQL database tools for querying transaction data
5. **Business Logic**: Rules for interpreting transaction codes and IDs

## Requirements

- Python 3.8+
- PostgreSQL database
- Google API Key (for Gemini model access)
- Chrome vector database for RAG

### Python Dependencies

- Flask
- langchain
- langchain-google-genai
- langchain-chroma
- psycopg2
- python-dotenv
- other dependencies specified in requirements.txt

## Installation

1. **Clone the repository**:
   ```
   git clone https://github.com/yourusername/financial-transaction-analysis.git
   cd financial-transaction-analysis
   ```

2. **Set up a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   ```

5. **Set up the database**:
   ```
   psql -U your_database_user -d your_database_name -f transactions.sql
   ```

6. **Initialize the RAG vector database**:
   ```
   python rag-setup.py
   ```

## Project Structure

```
financial-transaction-analysis/
│
├── start.py                 # Main application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
│
├── Postgres/                # Database utilities
│   ├── database.py          # Database connection and query functions
│   └── transaction_query.py # Transaction query tool
│
├── rag/                     # Retrieval-Augmented Generation
│   ├── information_retrieval_tool.py  # RAG query tool
│   └── db/                  # Vector store database
│
├── content.txt              # Knowledge base content for RAG
├── transactions.sql         # SQL setup for transaction database
│
├── templates/               # Flask templates
│   └── index.html           # Web interface
│
└── README.md                # This file
```

## Usage

1. **Start the application**:
   ```
   python start.py
   ```

2. **Access the web interface**:
   Open your browser and navigate to `http://localhost:5000`

3. **Interact with the agent**:
   - Ask questions about transaction types
   - Query specific transaction data
   - Analyze transaction patterns

### Example Queries

- "What are the different transaction types available?"
- "Show me all approved transactions"
- "Find transactions for account 12345678"
- "What do the action codes mean?"
- "Show me MegaStripe requests from yesterday"
- "How many declined transactions were there last week?"
- "What are the most common decline reasons?"

## Business Logic

The system interprets transaction data based on these rules:

1. **Action Codes**:
   - Codes 1, 2, 3: Approved transactions
   - Codes 8, 9, 0: Not approved transactions
   - Other codes: Declined transactions

2. **Transaction Types** (based on positional_ID):
   - First position 'a'/'b' + position 6 'c': MegaStripe requests
   - First position 'x'/'y' + position 6 'z': Internal requests
   - First position 'j'/'k' + position 6 'l': Phone requests

## Customization

### Adding New Transaction Types

1. Update the `financial_content.txt` file with new transaction type information
2. Run `python rag-setup.py` to rebuild the vector database

### Modifying Database Schema

1. Update the `transactions.sql` file with your schema changes
2. Update the schema description in `start.py` to match your changes
3. Rebuild the database with the new schema

### Changing the Agent Behavior

Edit the prompt template in `start.py` to modify how the agent responds to queries.

## Troubleshooting

### Agent Not Responding

- Check that your Gemini API key is valid and set correctly in the `.env` file
- Ensure you have sufficient API credits

### Database Connection Issues

- Verify that PostgreSQL is running
- Check that database credentials in `.env` are correct
- Ensure the database and tables exist

### RAG Not Returning Expected Information

- Make sure `rag-setup.py` was run to create the vector database
- Check that `content.txt` contains the information you expect
- Try rebuilding the vector database

