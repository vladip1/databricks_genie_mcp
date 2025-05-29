# Databricks Genie MCP Docker Setup

This repository contains Docker configuration for running the Databricks Genie MCP server and Agent Manager as separate containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
- Databricks workspace access with appropriate permissions

## Configuration

1. Create a `.env` file in the root directory by copying the `.env.example` file:

```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in your Databricks credentials:

```
# Databricks Workspace URL
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Authentication Method 1: Personal Access Token (PAT)
DATABRICKS_TOKEN=your-token-here

# Authentication Method 2: OAuth with Service Principal
# DATABRICKS_CLIENT_ID=your-client-id
# DATABRICKS_CLIENT_SECRET=your-client-secret

# Databricks Genie Space ID
DATABRICKS_GENIE_SPACE_ID=your-space-id

# Databricks Warehouse ID
DATABRICKS_WORKHOUSE_ID=your-warehouse-id

# Path to the system prompt file
SYSTEM_PROMPT_PATH=promts/agent_system_promt.md

# Optional: If you need to customize the log level
# LOG_LEVEL=INFO
```

## Building and Running

### Using Docker Compose (Recommended)

1. Build and start the containers:

```bash
docker-compose up --build
```

2. To run in detached mode (background):

```bash
docker-compose up -d
```

3. To stop the containers:

```bash
docker-compose down
```

4. To run only the MCP server:

```bash
docker-compose up mcp-server
```

5. To run only the Agent Manager:

```bash
docker-compose up agent-manager
```

### Using Docker Directly

1. Build and run the MCP server:

```bash
# Build with build arguments from .env file
docker build -t databricks-mcp -f apps/databricks-mcp/Dockerfile \
  --build-arg DATABRICKS_HOST=$(grep DATABRICKS_HOST .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_TOKEN=$(grep DATABRICKS_TOKEN .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_GENIE_SPACE_ID=$(grep DATABRICKS_GENIE_SPACE_ID .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_WORKHOUSE_ID=$(grep DATABRICKS_WORKHOUSE_ID .env | cut -d '=' -f2) \
  .

# Run the container
docker run -p 8000:8000 --env-file .env databricks-mcp
```

2. Build and run the Agent Manager:

```bash
# Build with build arguments from .env file
docker build -t databricks-agent -f apps/agent/Dockerfile \
  --build-arg DATABRICKS_HOST=$(grep DATABRICKS_HOST .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_TOKEN=$(grep DATABRICKS_TOKEN .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_GENIE_SPACE_ID=$(grep DATABRICKS_GENIE_SPACE_ID .env | cut -d '=' -f2) \
  --build-arg DATABRICKS_WORKHOUSE_ID=$(grep DATABRICKS_WORKHOUSE_ID .env | cut -d '=' -f2) \
  --build-arg MCP_SERVER_URL=http://localhost:8000/sse \
  --build-arg SYSTEM_PROMPT_PATH=$(grep SYSTEM_PROMPT_PATH .env | cut -d '=' -f2) \
  .

# Run the container
docker run -p 8080:8080 --env-file .env databricks-agent
```

### About Build Arguments

The Dockerfiles use build arguments (ARG) to pass environment variables during the build process. This allows you to:

1. Customize the image at build time
2. Bake non-sensitive configuration into the image
3. Override defaults with environment variables at runtime

For sensitive information like tokens and secrets, we still recommend using environment variables at runtime rather than build arguments, as build arguments can be visible in the image history.

## Accessing the Services

- MCP Server: http://localhost:8000
  - Swagger UI: http://localhost:8000/docs
- Agent Manager: http://localhost:8080
  - Health check: http://localhost:8080/health

## Architecture

The Docker setup runs two main services as separate containers:

1. **MCP Server** (Port 8000)
   - Container name: mcp-server
   - Provides tools for interacting with Databricks Genie
   - Handles authentication with Databricks workspace

2. **Agent Manager** (Port 8080)
   - Container name: agent-manager
   - Provides an OpenAI-compatible API for interacting with Databricks Genie
   - Connects to the MCP Server to use its tools
   - Depends on the MCP Server container

## Troubleshooting

- **Authentication Issues**: Ensure your Databricks credentials in the `.env` file are correct and have the necessary permissions.
- **Connection Issues**: Check if your network allows connections to the Databricks workspace.
- **Container Startup Issues**: Check the logs with `docker-compose logs` or `docker logs <container-id>`.
- **Service Communication Issues**: If the Agent Manager cannot connect to the MCP Server, ensure the MCP Server is running and check the network configuration.
