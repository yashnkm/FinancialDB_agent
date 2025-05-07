from flask import Flask, render_template, request, jsonify
import os
import time
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Import the information retrieval tool
from rag.information_retrieval_tool import information_retrieval_tool

# Import the transaction query tool
from Postgres.transaction_query import transaction_query_tool

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)
# Initialize the LLM using API key from environment variable
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.6,
    # max_retries=2,  # Limit retries to avoid excessive API calls
    # timeout=30  # Set a timeout
)

# Define the tools list
tools = [
    Tool(
        name="information_retrieval",
        func=information_retrieval_tool,
        description="Use this tool for any general questions about financial transactions, transaction types, status codes, action codes, merchant category codes, or any other general information about our payment processing services. This tool returns raw information from our knowledge base."
    ),
    Tool(
        name="transaction_query",
        func=transaction_query_tool,
        description="""Execute SQL queries to analyze transaction data. You can construct complex SQL queries based on the database schema.

You can send your input in any of these formats:
1. As a plain JSON string:
{"query_type": "select", "sql_query": "SELECT * FROM transactions WHERE action_code = '1' LIMIT 5"}

2. As a JSON code block:
```json
{
    "query_type": "select",
    "sql_query": "SELECT * FROM transactions WHERE action_code = '1' LIMIT 5"
}
```

3. Or as a direct SQL query:
SELECT * FROM transactions WHERE action_code = '1' LIMIT 5

The query_type can be "select", "insert", "update", or "delete", though "select" is most common for analysis."""
    )
]

# Define the prompt template
template = '''You are a helpful financial transaction analysis chatbot assisting users with:
1. Information about financial transactions, approvals, and declines
2. Transaction status queries and analysis

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

WHEN TO USE EACH TOOL:
- Use the information_retrieval tool when you need general information about transaction types, status codes, and company policies
- Use the transaction_query tool when you need to query transaction data from the database

QUERY GUIDELINES:
- Be flexible and adaptive with your queries
- If a user asks for account information with minimal details, make a best effort to provide relevant information without asking for too many additional details
- For account-specific queries, use any available identifiers (account_number, UID, traceNo)
- For transaction status queries, filter by action_code 
- Infer the user's needs based on context and previous messages

DATABASE SCHEMA:
Our transaction database has this table:

transactions (
    UID VARCHAR(100) PRIMARY KEY,
    account_number VARCHAR(50),
    transDate DATE,
    transaction_time TIME,
    issues VARCHAR(100),
    acquirer VARCHAR(100),
    traceNo VARCHAR(50),
    requested_amount DECIMAL(15, 2),
    currency_code VARCHAR(3),
    issuer_amount DECIMAL(15, 2),
    dollar_amount DECIMAL(15, 2),
    approval_code VARCHAR(20),
    mcc VARCHAR(10),
    action_code VARCHAR(10),
    funncode VARCHAR(20),
    add_resp TEXT,
    responseTime DECIMAL(10, 2),
    swout_indicator VARCHAR(10),
    positional_ID VARCHAR(20),
    forwall_C VARCHAR(20),
    merchant_NUM VARCHAR(50),
    mName VARCHAR(100),
    mAdd TEXT,
    mCity VARCHAR(100),
    mGeo VARCHAR(50),
    authType VARCHAR(20),
    mti VARCHAR(20)
)

TRANSACTION BUSINESS LOGIC TIPS:
- Action codes 1, 2, 3 = approved transactions
- Action codes 8, 9, 0 = not approved transactions
- All other action codes = declined transactions
- Positional_ID starting with 'a'/'b' and having 'c' in position 6 = MegaStripe request
- Positional_ID starting with 'x'/'y' and having 'z' in position 6 = Internal request
- Positional_ID starting with 'j'/'k' and having 'l' in position 6 = Phone request

SUGGESTIONS FOR EFFECTIVE RESPONSES:
- Keep explanations concise
- Format query results in a readable way
- Highlight important information
- Provide insights based on the data, not just raw results
- Ask for additional information only when absolutely necessary
- If partial information is provided (like partial account numbers), try to work with it

Chat History:
{chat_history}

Begin!

Question: {input}
{agent_scratchpad}'''

# Create a function to format chat history as a string
def format_chat_history(messages):
    if not messages:
        return "No previous messages."
    
    history_str = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            history_str += f"Human: {message.content}\n"
        elif isinstance(message, AIMessage):
            history_str += f"AI: {message.content}\n"
        elif isinstance(message, SystemMessage):
            # Optionally include system messages
            pass  # Skip system messages in the formatted history
    
    return history_str.strip()

# Update the prompt template to include chat_history
prompt = PromptTemplate.from_template(template)
prompt = prompt.partial(chat_history="")  # Default empty chat history

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True,  # Add error handling
    max_iterations=8 # Increased iterations for complex queries with multiple steps
)

# Initialize chat history
chat_history = []

# Set an initial system message
system_message = SystemMessage(content="""You are a financial transaction analysis chatbot. 
When users ask about transaction types or general information, you will use the information_retrieval tool 
to get relevant documents, then craft a helpful response based on that information.

For transaction queries and analysis, you'll use the transaction_query tool to execute SQL queries. Make educated guesses when information is incomplete - don't ask too many follow-up questions.""")

# Store the welcome message
welcome_message = """
Welcome to FinTech Analytics, your financial transaction assistant!

I can help you with:
1. Information about transaction types, status codes, and processing
2. Searching and analyzing your transaction data

How can I assist you today?
"""

# Initialize chat history with system message
chat_history.append(system_message)
# Add AI welcome message to history
ai_welcome = AIMessage(content=welcome_message.strip())
chat_history.append(ai_welcome)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    global chat_history
    
    # Get user input from request
    data = request.json
    query = data.get('message', '')
    
    try:
        # Add user message to chat history
        chat_history.append(HumanMessage(content=query))
        
        # Format chat history for the prompt
        formatted_history = format_chat_history(chat_history[:-1])  # Exclude the latest message
        
        # Process with agent
        result = agent_executor.invoke({
            "input": query,  # Pass only the current query as input
            "chat_history": formatted_history  # Pass formatted history separately
        })
        
        response = result.get("output", "I'm sorry, I couldn't process that request.")
        
        # Add AI response to chat history
        chat_history.append(AIMessage(content=response))
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
        
        return jsonify({
            'message': response,
            'timestamp': time.strftime('%H:%M')
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        error_message = "I'm having some technical difficulties. Please try again."
        return jsonify({
            'message': error_message,
            'timestamp': time.strftime('%H:%M'),
            'error': True
        })

# API endpoint to reset the chat
@app.route('/api/reset', methods=['POST'])
def reset_chat():
    global chat_history
    # Reset chat history
    chat_history = [system_message, ai_welcome]
    return jsonify({'success': True, 'message': 'Chat history has been reset'})

if __name__ == '__main__':
    app.run(debug=True)