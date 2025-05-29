# Databricks Genie Agent Manager

This is an OpenAI-compatible API interface for the Databricks Genie MCP tools. It allows you to interact with Databricks Genie using the OpenAI API format.

## Architecture

The agent-manager.py file implements:
- An OpenAI-compatible API interface using FastAPI
- A pydantic-ai agent for processing requests
- Connection to the MCP server for Databricks Genie tools
- Streaming of intermediate outputs back to the caller

## Prerequisites

- Python 3.8+
- Required packages (see requirements.txt)
- Databricks authentication credentials (set in .env file)
- Running MCP server (server.py)

## Setup

1. Make sure you have all the required environment variables set in your .env file:
   ```
   DATABRICKS_HOST=your_databricks_host
   DATABRICKS_TOKEN=your_databricks_token
   DATABRICKS_GENIE_SPACE_ID=your_genie_space_id
   DATABRICKS_WORKHOUSE_ID=your_warehouse_id
   ```

2. Ensure the MCP server is running:
   ```
   python server.py
   ```

3. Run the agent-manager:
   ```
   python agent-manager.py
   ```

## API Endpoints

### Chat Completions

```
POST /v1/chat/completions
```

This endpoint is compatible with the OpenAI chat completions API. It accepts the following parameters:

- `model`: The model to use (currently only supports the configured Bedrock model)
- `messages`: An array of messages in the conversation
- `temperature`: Controls randomness (default: 0.7)
- `stream`: Whether to stream the response (default: false)
- `max_tokens`: Maximum number of tokens to generate (optional)
- `user`: A unique identifier for the user (optional)

Example request:

```json
{
  "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Analyze the usage of analytics dashboards that are hosted by EP."
    }
  ],
  "stream": true
}
```

### Health Check

```
GET /health
```

Returns the health status of the agent-manager.

## Integration with OpenWebUI

To integrate with OpenWebUI, configure it to use the agent-manager as an OpenAI-compatible API endpoint:

1. Set the API URL to `http://localhost:8080/v1`
2. Use the chat completions endpoint for interactions

## Limitations

- Currently only supports the last user message in the conversation
- Limited support for OpenAI API parameters
- Uses a fixed model (Bedrock Claude)

## Troubleshooting

If you encounter issues:

1. Check that the MCP server is running on port 8000
2. Verify your Databricks authentication credentials
3. Check the logs for error messages
