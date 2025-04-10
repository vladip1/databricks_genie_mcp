import asyncio
import sys
import json
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from databricks.sdk import WorkspaceClient

class GenieClient:
    """Databricks Genie API client using MCP for tool interactions"""
    
    def __init__(self, llm_endpoint_name: str = "databricks-meta-llama-3-3-70b-instruct"):
        """Initialize the Genie client
        
        Args:
            llm_endpoint_name: Name of the Databricks LLM serving endpoint
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Context for selected space/conversation
        self.current_space_id: Optional[str] = None
        self.current_conversation_id: Optional[str] = None
        
        # Initialize Databricks client and get OpenAI-compatible client
        self.workspace = WorkspaceClient()
        self.llm_endpoint_name = llm_endpoint_name
        self.openai_client = self.workspace.serving_endpoints.get_open_ai_client()
        print(f"Initialized OpenAI-compatible client for {llm_endpoint_name}")

    async def connect_to_server(self, server_script_path: str):
        """Connect to the Genie MCP server
        
        Args:
            server_script_path: Path to the server script
        """
        # Validate script path
        if not server_script_path.endswith('.py'):
            raise ValueError("Server script must be a Python file")
            
        # Set up server parameters
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )
        
        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        
        # Display tool descriptions
        print("\nAvailable Tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        return tools
    
    def _convert_schema_to_openai_format(self, tool):
        """Convert MCP tool schema to OpenAI function format"""
        # Extract the input schema from the tool
        schema = tool.inputSchema
        
        # Create the function definition
        function_def = {
            "name": tool.name,
            "description": tool.description,
            "parameters": schema
        }
        
        # Return in the OpenAI tool format
        return {
            "type": "function",
            "function": function_def
        }

    async def start_conversation(self, space_id: str, initial_message: str) -> Dict[str, Any]:
        """Start a new conversation in a Genie space
        
        Args:
            space_id: ID of the Genie space
            initial_message: First message to start the conversation
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "start_conversation", 
                {"space_id": space_id, "content": initial_message}
            )
            
            content = result.content
            
            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error starting conversation: {str(e)}")
            return {"error": str(e)}

    async def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get details of a Genie Space
        
        Args:
            space_id: ID of the Genie space to retrieve details for
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "get_space", 
                {"space_id": space_id}
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error retrieving space details: {str(e)}")
            return {"error": str(e)}

    async def create_message(self, space_id: str, conversation_id: str, content: str) -> Dict[str, Any]:
        """Create a new message in an existing conversation
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation
            content: Message content
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "create_message", 
                {"space_id": space_id, "conversation_id": conversation_id, "content": content}
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error creating message: {str(e)}")
            return {"error": str(e)}

    async def get_message(self, space_id: str, conversation_id: str, message_id: str) -> Dict[str, Any]:
        """Get a message from a conversation
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation
            message_id: ID of the message to retrieve
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "get_message", 
                {"space_id": space_id, "conversation_id": conversation_id, "message_id": message_id}
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error retrieving message: {str(e)}")
            return {"error": str(e)}

    async def get_message_attachment_query_result(
        self, 
        space_id: str, 
        conversation_id: str, 
        message_id: str, 
        attachment_id: str
    ) -> Dict[str, Any]:
        """Get the SQL query result from a message attachment
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation
            message_id: ID of the message
            attachment_id: ID of the query attachment
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "get_message_attachment_query_result", 
                {
                    "space_id": space_id, 
                    "conversation_id": conversation_id, 
                    "message_id": message_id,
                    "attachment_id": attachment_id
                }
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error getting query result: {str(e)}")
            return {"error": str(e)}

    async def execute_message_attachment_query(
        self, 
        space_id: str, 
        conversation_id: str, 
        message_id: str, 
        attachment_id: str
    ) -> Dict[str, Any]:
        """Execute the SQL query for a message attachment
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation
            message_id: ID of the message
            attachment_id: ID of the query attachment
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "execute_message_attachment_query", 
                {
                    "space_id": space_id, 
                    "conversation_id": conversation_id, 
                    "message_id": message_id,
                    "attachment_id": attachment_id
                }
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return {"error": str(e)}

    async def generate_download_full_query_result(
        self, 
        space_id: str, 
        conversation_id: str, 
        message_id: str, 
        attachment_id: str
    ) -> Dict[str, Any]:
        """Generate full query result download
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation
            message_id: ID of the message
            attachment_id: ID of the attachment
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "generate_download_full_query_result", 
                {
                    "space_id": space_id, 
                    "conversation_id": conversation_id, 
                    "message_id": message_id, 
                    "attachment_id": attachment_id
                }
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error generating download for query result: {str(e)}")
            return {"error": str(e)}
    
    async def poll_message_until_complete(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
        timeout_seconds: int = 600,
        poll_interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """Poll a message until its status is COMPLETED, ERROR, or FAILED
        
        Args:
            space_id: ID of the Genie space
            conversation_id: ID of the conversation 
            message_id: ID of the message
            timeout_seconds: Maximum time to poll (default: 10 minutes)
            poll_interval_seconds: Time between polls (default: 5 seconds)
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")
        
        try:
            result = await self.session.call_tool(
                "poll_message_until_complete", 
                {
                    "space_id": space_id, 
                    "conversation_id": conversation_id, 
                    "message_id": message_id,
                    "timeout_seconds": timeout_seconds,
                    "poll_interval_seconds": poll_interval_seconds
                }
            )
            
            content = result.content

            # Handle list[TextContent] structure
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    try:
                        return json.loads(first_item.text)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from content[0].text: {e}")
                        return {"error": "Failed to decode server response", "raw_response": first_item.text}
                else:
                    print(f"Warning: Response list item does not have .text attribute. Type: {type(first_item)}")
                    return {"error": "Unexpected item format in server response list", "raw_response": str(first_item)}
            else:
                # Fallback for unexpected structure
                print(f"Warning: Unexpected response format. Expected list, got: {type(content)}")
                return {"error": "Unexpected response format from server", "raw_response": str(content)}
                
        except Exception as e:
            print(f"Error polling message: {str(e)}")
            return {"error": str(e)}
    
    async def process_natural_language_query(self, query: str) -> str:
        """Process a natural language query using Meta Llama and Genie tools
        
        Args:
            query: Natural language query to process
        """
        if not self.session:
            raise ValueError("Not connected to a server. Call connect_to_server first.")

        # Initialize conversation with user query
        messages = [
            {"role": "user", "content": query}
        ]

        # Get available tools and convert to OpenAI format
        response = await self.session.list_tools()
        available_tools = [self._convert_schema_to_openai_format(tool) for tool in response.tools]

        final_text = []
        
        try:
            # Make initial LLM API call
            print("Sending query to LLM with tools...")
            llm_response = self.openai_client.chat.completions.create(
                model=self.llm_endpoint_name,
                messages=messages,
                tools=available_tools,
                max_tokens=1000
            )
            
            # Get the assistant's response
            assistant_message = llm_response.choices[0].message
            
            # Add any content from the assistant to our output
            if assistant_message.content:
                final_text.append(assistant_message.content)
            
            # Check for tool calls
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                # Process each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args_str = tool_call.function.arguments
                    
                    # Parse the arguments string to a dict
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError as e:
                        final_text.append(f"\nError parsing tool arguments: {e}")
                        continue
                    
                    # Execute tool call
                    try:
                        final_text.append(f"\n[Calling tool: {tool_name}]")
                        result = await self.session.call_tool(tool_name, tool_args)
                        
                        # Format the result
                        if hasattr(result.content, 'text'):
                            result_text = result.content.text
                        else:
                            result_text = str(result.content)
                        
                        final_text.append(f"\nResult:\n{result_text}")
                        
                    except Exception as e:
                        final_text.append(f"\nError calling tool {tool_name}: {str(e)}")
                        continue
            
            # Return the result
            return "\n".join([t for t in final_text if t])
            
        except Exception as e:
            print(f"LLM API Error: {str(e)}")
            return f"Error: {str(e)}"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nDatabricks Genie MCP Client Started!")
        print("Interact with Genie spaces and conversations.")
        print("\nAvailable Commands:")
        print("- use_space <space_id>       Select a Genie space by ID")
        print("- info_space <space_id>      Get details about a Genie space")
        print("- start <Your question>      Start a new conversation in the active space")
        print("- reply <conv_id> <message>  Reply to a conversation in the active space")
        print("- get <conv_id> <msg_id>     Get a message from a conversation")
        print("- poll <conv_id> <msg_id>    Poll a message until it's complete")
        print("- query <conv_id> <msg_id> <attach_id>  Get query results from a message attachment")
        print("- execute <conv_id> <msg_id> <attach_id>  Re-execute a query from a message attachment")
        print("- download <conv_id> <msg_id> <attach_id> Generate full query result download")
        print("- ask <natural language query> Process a query using LLM and Genie tools")
        print("- quit                       Exit the client")
        
        while True:
            # Construct prompt indicating current context
            context_prompt = ""
            if self.current_space_id:
                context_prompt += f" [Space: {self.current_space_id}]"
            if self.current_conversation_id:
                 context_prompt += f" [Conv: {self.current_conversation_id}]"
            
            prompt = f"\nQuery{context_prompt}: "
            
            try:
                user_input = input(prompt).strip()
                
                if user_input.lower() == 'quit':
                    break
                
                parts = user_input.split()
                if not parts:
                    continue
                
                command = parts[0].lower()
                
                if command == 'info_space' and len(parts) == 2:
                    space_id = parts[1]
                    print(f"\nGetting details for space {space_id}...")
                    result = await self.get_space(space_id)
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                    
                    if "id" in result:
                        set_as_active = input("\nSet this as your active space? (y/n): ").strip().lower()
                        if set_as_active == 'y':
                            self.current_space_id = space_id
                            self.current_conversation_id = None
                            print(f"\nSet active space to: {self.current_space_id}")
                
                elif command == 'use_space' and len(parts) == 2:
                    space_id_to_use = parts[1]
                    self.current_space_id = space_id_to_use
                    self.current_conversation_id = None
                    print(f"\nSet active space to: {self.current_space_id}")
                
                elif command == 'start' and len(parts) >= 2:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    message = ' '.join(parts[1:])
                    print(f"\nStarting conversation in space {self.current_space_id}...")
                    result = await self.start_conversation(self.current_space_id, message)
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                    
                    if isinstance(result, dict) and 'conversation_id' in result:
                        self.current_conversation_id = result['conversation_id']
                        print(f"\nCurrent conversation: {self.current_conversation_id} in space {self.current_space_id}")
                
                elif command == 'reply' and len(parts) >= 3:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message = ' '.join(parts[2:])
                    
                    print(f"\nReplying to conversation {conversation_id} in space {self.current_space_id}...")
                    result = await self.create_message(self.current_space_id, conversation_id, message)
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                    
                    if conversation_id == self.current_conversation_id:
                        pass
                    else:
                        self.current_conversation_id = conversation_id
                        print(f"\nSwitched active conversation to: {self.current_conversation_id}")
                
                elif command == 'get' and len(parts) == 3:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message_id = parts[2]
                    
                    print(f"\nGetting message {message_id} from conversation {conversation_id} in space {self.current_space_id}...")
                    result = await self.get_message(self.current_space_id, conversation_id, message_id)
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                
                elif command == 'poll' and len(parts) == 3:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message_id = parts[2]
                    
                    print(f"\nPolling message {message_id} from conversation {conversation_id} until complete...")
                    result = await self.poll_message_until_complete(
                        self.current_space_id, 
                        conversation_id, 
                        message_id
                    )
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                    
                    # If there are attachments in the completed message, display them
                    if result.get("status") == "COMPLETED" and result.get("attachments"):
                        print("\nAttachments found in the completed message:")
                        for i, attachment in enumerate(result["attachments"]):
                            if "attachment_id" in attachment:
                                print(f"  {i+1}. ID: {attachment['attachment_id']}")
                            if "query" in attachment and "description" in attachment["query"]:
                                print(f"     Description: {attachment['query']['description']}")
                            if "query" in attachment and "query" in attachment["query"]:
                                print(f"     SQL: {attachment['query']['query']}")
                        
                        print("\nTo get query results, use: query <conv_id> <msg_id> <attach_id>")
                
                elif command == 'query' and len(parts) == 4:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message_id = parts[2]
                    attachment_id = parts[3]
                    
                    print(f"\nGetting query results for message {message_id}, attachment {attachment_id}...")
                    result = await self.get_message_attachment_query_result(
                        self.current_space_id, 
                        conversation_id, 
                        message_id, 
                        attachment_id
                    )
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                
                elif command == 'execute' and len(parts) == 4:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message_id = parts[2]
                    attachment_id = parts[3]
                    
                    print(f"\nRe-executing query for message {message_id}, attachment {attachment_id}...")
                    result = await self.execute_message_attachment_query(
                        self.current_space_id, 
                        conversation_id, 
                        message_id, 
                        attachment_id
                    )
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                
                elif command == 'download' and len(parts) == 4:
                    if not self.current_space_id:
                        print("\nError: No active space selected. Use 'use_space <space_id>' or 'info_space <space_id>' first.")
                        continue
                        
                    conversation_id = parts[1]
                    message_id = parts[2]
                    attachment_id = parts[3]
                    
                    print(f"\nGenerating download for query results from message {message_id}, attachment {attachment_id}...")
                    result = await self.generate_download_full_query_result(
                        self.current_space_id, 
                        conversation_id, 
                        message_id, 
                        attachment_id
                    )
                    print("\nResponse:")
                    print(json.dumps(result, indent=2))
                
                elif command == 'ask':
                    query = ' '.join(parts[1:])
                    print("\nProcessing natural language query...")
                    response = await self.process_natural_language_query(query)
                    print("\nResponse:")
                    print(response)
                
                else:
                    print("Unknown command or incorrect arguments. Try 'use_space', 'info_space', 'start', 'reply', 'get', 'poll', 'query', 'execute', 'download', 'ask', or 'quit'.")
                    
            except Exception as e:
                print(f"\nError in chat loop: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # Get the server script path from command line or use default
    server_script_path = sys.argv[1] if len(sys.argv) > 1 else "../genie_api/server.py"
    
    # Optional second argument for the LLM endpoint name
    llm_endpoint_name = sys.argv[2] if len(sys.argv) > 2 else "databricks-meta-llama-3-3-70b-instruct"
        
    client = GenieClient(llm_endpoint_name)
    try:
        print(f"Connecting to server: {server_script_path}")
        await client.connect_to_server(server_script_path)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 