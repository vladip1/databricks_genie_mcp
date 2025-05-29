from typing import Any, Dict, List, Optional
import os
import json
import time
import logging
# from fastapi import FastAPI
# from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from fastmcp import FastMCP
from databricks.sdk import WorkspaceClient

# Import authentication utilities
from auth import get_workspace_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# A FastAPI app
app = FastAPI(    name="Databricks MCP Server",
    port=int(os.getenv('DATABRICKS_MCP_PORT', 8000)),
    docs_url="/docs",  # Enable Swagger UI at /docs
    openapi_url="/openapi.json",  # Path for OpenAPI schema
)

# Create an MCP server from your FastAPI app
mcp = FastMCP.from_fastapi(app=app)


# SQL tools
@mcp.tool(
    name="fetch-from-datalake",
    description="Execute a SQL statement with parameters: statement (required)",
)
def execute_sql(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Executing SQL with params: {params}")
    try:
        import requests

        # Replace with your actual Databricks workspace URL and personal access token
        TOKEN = os.getenv('DATABRICKS_TOKEN')

        # Define the endpoint URL
        url = f"{os.getenv('DATABRICKS_HOST')}/api/2.0/sql/statements"

        # Set up headers for authentication and content type
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }

        statement = params['statement']
        # Define the payload for the SQL statement
        payload = {
            "statement": statement,
            "warehouse_id": os.getenv('DATABRICKS_WORKHOUSE_ID'),
            "wait_timeout": "50s",
            "on_wait_timeout": "CANCEL"
        }

        # Make the POST request
        response = requests.post(url, headers=headers, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Response: %s", response.json())
        else:
            logger.error("Request failed with status code %s: %s", response.status_code, response.text)

        return response.json()
    except Exception as e:
        logger.error("Error executing SQL: %s", str(e))
        return response.json()

if __name__ == "__main__":
    logger.info("Initializing Databricks MCP Server...")
    
    # Initialize the Databricks client with authentication
    mcp.run(transport='sse')  # Enable HTTP for Swagger UI access
