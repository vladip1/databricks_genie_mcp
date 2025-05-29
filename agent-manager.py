import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field

# Pydantic-AI imports
from pydantic_ai import Agent, CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import ToolCallPart, ToolReturnPart, FunctionToolCallEvent, FunctionToolResultEvent, TextPart
from pydantic_ai.usage import UsageLimits
from pydantic_ai.mcp import MCPServerHTTP
from pydantic_ai.models.bedrock import BedrockConverseModel

# Read system prompt from file
with open("agent_system_promt.md", "r") as f:
    SYSTEM_PROMPT = f.read()

# Debug flag - set to True to enable debug prints for all tools
DEBUG = False

# Initialize FastAPI app
app = FastAPI(
    title="Databricks Agent Manager",
    description="OpenAI-compatible API for Databricks Genie",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Databricks client (will be set in startup event)
databricks_client = None

# Initialize MCP server connection
mcp_server = MCPServerHTTP(url='http://localhost:8000/sse')

# Initialize Bedrock model
model_name = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
model = BedrockConverseModel(model_name)

# Create agent with MCP server
agent = Agent(
    model, 
    mcp_servers=[mcp_server],
    instructions=SYSTEM_PROMPT
)

# OpenAI API compatible models
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


def format_messages_for_agent(messages: List[ChatMessage]) -> str:
    """Format messages for the agent."""
    # For simplicity, we'll just use the last user message
    # In a more complex implementation, we would handle the full conversation history
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    
    # If no user message is found, raise an exception
    raise HTTPException(status_code=400, detail="No user message found in the request")

async def generate_streaming_response(prompt: str) -> AsyncGenerator[str, None]:
    """Generate streaming response from the agent."""
    try:
        async with agent.run_mcp_servers():
            async with agent.iter(prompt) as agent_run:
                async for node in agent_run:
                    # Handle different node types
                    if isinstance(node, UserPromptNode):
                        # Initial prompt, nothing to stream yet
                        pass
                    
                    elif isinstance(node, ModelRequestNode):
                        # Model request, nothing to stream yet
                        pass
                    
                    elif isinstance(node, CallToolsNode):
                        # Stream text parts from model response
                        text_parts = [part for part in node.model_response.parts if isinstance(part, TextPart)]
                        for part in text_parts:
                            chunk = {
                                "id": f"chatcmpl-{id(agent_run)}",
                                "object": "chat.completion.chunk",
                                "created": int(__import__('time').time()),
                                "model": model_name,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": part.content},
                                        "finish_reason": None
                                    }
                                ]
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"
                        
                        # Stream tool events
                        async with node.stream(agent_run.ctx) as event_stream:
                            async for event in event_stream:
                                if isinstance(event, FunctionToolCallEvent):
                                    # Tool call event
                                    tool_call = event.part
                                    tool_info = f"Using tool: {tool_call.tool_name}"
                                    
                                    chunk = {
                                        "id": f"chatcmpl-{id(agent_run)}",
                                        "object": "chat.completion.chunk",
                                        "created": int(__import__('time').time()),
                                        "model": model_name,
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": {"content": f"\n\n{tool_info}\n"},
                                                "finish_reason": None
                                            }
                                        ]
                                    }
                                    yield f"data: {json.dumps(chunk)}\n\n"
                                
                                elif isinstance(event, FunctionToolResultEvent):
                                    # Tool result event
                                    tool_result = event.result
                                    if hasattr(tool_result, 'content'):
                                        tool_name = tool_result.tool_name
                                        text_content = tool_result.content.content[0]
                                        if isinstance(text_content, TextPart):
                                            try:
                                                # Try to parse and format JSON content
                                                result_content = json.loads(text_content.text)
                                                result_str = f"\nResult from {tool_name}:\n{json.dumps(result_content, indent=2)}\n"
                                            except:
                                                # If not valid JSON, use as is
                                                result_str = f"\nResult from {tool_name}:\n{text_content.text}\n"
                                            
                                            chunk = {
                                                "id": f"chatcmpl-{id(agent_run)}",
                                                "object": "chat.completion.chunk",
                                                "created": int(__import__('time').time()),
                                                "model": model_name,
                                                "choices": [
                                                    {
                                                        "index": 0,
                                                        "delta": {"content": result_str},
                                                        "finish_reason": None
                                                    }
                                                ]
                                            }
                                            yield f"data: {json.dumps(chunk)}\n\n"
                    
                    elif agent.is_end_node(node):
                        # Final result
                        final_chunk = {
                            "id": f"chatcmpl-{id(agent_run)}",
                            "object": "chat.completion.chunk",
                            "created": int(__import__('time').time()),
                            "model": model_name,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }
                            ]
                        }
                        yield f"data: {json.dumps(final_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
    
    except Exception as e:
        # Handle exceptions
        error_chunk = {
            "id": f"chatcmpl-error",
            "object": "chat.completion.chunk",
            "created": int(__import__('time').time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": f"\n\nError: {str(e)}\n"},
                    "finish_reason": "error"
                }
            ]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"

async def generate_non_streaming_response(prompt: str) -> ChatCompletionResponse:
    """Generate non-streaming response from the agent."""
    try:
        async with agent.run_mcp_servers():
            result = await agent.run(prompt)
            
            # Create response
            return ChatCompletionResponse(
                id=f"chatcmpl-{id(result)}",
                created=int(__import__('time').time()),
                model=model_name,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=result.output
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=result.usage.usage.request_tokens,
                    completion_tokens=result.usage.usage.response_tokens,
                    total_tokens=result.usage.usage.total_tokens
                )
            )
    
    except Exception as e:
        # Handle exceptions
        return ChatCompletionResponse(
            id=f"chatcmpl-error",
            created=int(__import__('time').time()),
            model=model_name,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=f"Error: {str(e)}"
                    ),
                    finish_reason="error"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
        )

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint."""
    # Format messages for the agent
    prompt = format_messages_for_agent(request.messages)
    
    # Check if streaming is requested
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            generate_streaming_response(prompt),
            media_type="text/event-stream"
        )
    else:
        # Return non-streaming response
        return await generate_non_streaming_response(prompt)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting Databricks Genie Agent Manager...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
