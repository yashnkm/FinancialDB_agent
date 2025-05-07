from Postgres.database import execute_select_query, execute_dml_query
import json
import re

def transaction_query_tool(query_string: str) -> str:
    """
    Execute database queries constructed by the LLM for transaction analysis with fewer restrictions.
    
    Args:
        query_string: A JSON string containing query type and SQL query
            
    Returns:
        A string response with the results of the database operation
    """
    try:
        # Clean up the input string to handle markdown code blocks
        cleaned_input = query_string.strip()
        
        # Remove markdown code block syntax if present
        code_block_pattern = r'^```(?:json)?\s*([\s\S]*?)```$'
        code_block_match = re.match(code_block_pattern, cleaned_input)
        
        if code_block_match:
            cleaned_input = code_block_match.group(1).strip()
        
        # Parse the JSON input
        query_data = json.loads(cleaned_input)
        query_type = query_data.get("query_type", "").lower()
        sql_query = query_data.get("sql_query", "")
        
        if not sql_query:
            return "Error: No SQL query provided."
        
        # Execute the appropriate query type with fewer restrictions
        if query_type == "select":
            result = execute_select_query(sql_query)
        elif query_type in ["insert", "update", "delete"]:
            result = execute_dml_query(sql_query)
        else:
            return f"Error: Unsupported query type '{query_type}'. Use 'select', 'insert', 'update', or 'delete'."
        
        # Format the response
        if result.get("success", False):
            if query_type == "select":
                # For SELECT queries, return the data
                if result.get("row_count", 0) > 0:
                    return json.dumps(result.get("data", []), indent=2)
                else:
                    return "No results found for your query."
            else:
                # For DML queries, return information about the operation
                response = f"{query_type.upper()} operation successful. {result.get('affected_rows', 0)} row(s) affected."
                
                # Include returned data if available
                if result.get("returned_data"):
                    response += f"\nReturned data: {json.dumps(result.get('returned_data', []), indent=2)}"
                
                return response
        else:
            # Return error message
            return f"Database error: {result.get('error', 'Unknown error')}"
            
    except json.JSONDecodeError as e:
        # Check if the input might be a direct SQL query
        if cleaned_input.strip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
            try:
                # Determine query type from the first word
                query_type = cleaned_input.strip().split()[0].lower()
                
                # Execute based on type
                if query_type == "select":
                    result = execute_select_query(cleaned_input)
                    if result.get("success", False):
                        if result.get("row_count", 0) > 0:
                            return json.dumps(result.get("data", []), indent=2)
                        else:
                            return "No results found for your query."
                    else:
                        return f"Database error: {result.get('error', 'Unknown error')}"
                elif query_type in ["insert", "update", "delete"]:
                    result = execute_dml_query(cleaned_input)
                    if result.get("success", False):
                        return f"{query_type.upper()} operation successful. {result.get('affected_rows', 0)} row(s) affected."
                    else:
                        return f"Database error: {result.get('error', 'Unknown error')}"
                else:
                    return "Error: Unsupported query type. Use SELECT, INSERT, UPDATE, or DELETE."
            except Exception as e:
                return f"Error executing direct SQL query: {str(e)}"
        
        # Provide more detailed error information for JSON parsing issues
        return f"Error: Invalid JSON format. Details: {str(e)}\nReceived input: {query_string[:100]}{'...' if len(query_string) > 100 else ''}"
    except Exception as e:
        return f"Error executing query: {str(e)}"