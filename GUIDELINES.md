# architecture
## 2  Processes
- OpenWebUI (acts as a ChatBot)
- Agent-Manager
- Databricks MCP

# Agent-Manager
- will expose OpenAI interface
- will be enabled to work with MCP
- Will be implemented using pydentic-ai (https://deepwiki.com/pydantic/pydantic-ai)
- will stream all the intermediate output back to the caller

# Databricks MCP
- knows to invoke databricks APIs
