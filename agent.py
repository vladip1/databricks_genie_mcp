import asyncio
from pydantic_ai import Agent, CallToolsNode, ModelRequestNode, UserPromptNode
from mcp.types import TextContent
from pydantic_ai.messages import ToolCallPart, ToolReturnPart, FunctionToolCallEvent, FunctionToolResultEvent, TextPart
from pydantic_ai.usage import UsageLimits
import json
from pydantic_ai.mcp import MCPServerHTTP
from history import get_chat_history, store_messages_in_history

server = MCPServerHTTP(url='http://localhost:8000/sse')  

from pydantic_ai.models.bedrock import BedrockConverseModel

# Debug flag - set to True to enable debug prints for all tools
DEBUG = False

model_name = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'

model = BedrockConverseModel(model_name)
agent = Agent(model, mcp_servers=[server],
            #   end_strategy='exhaustive',
              instructions="you are a helpful assistant that can answer questions about the database, " \
              "you can use the space_id=01f01e7ddb4a1b4fb03588c97339d272, " \
              "be resourcefull, be creative, be smart, be fast, " \
            #   "if you are not sure about the answer, ask user to clarify the question, "\
            #   "you should use not more than few tool calling iterations, " \
            #   "prepare plan and ask user to confirm it before starting execution, " \
            #   "share the answer you received from the tool activation and confirm next step execution" \
            #   "once you received the response of the get_message_attachment_query_result, you have to present the intermediate result to the user, " \
            #   "do not proceed before user confirmation",
   
              )  


async def main():
    print("Starting agent...")
###########
    # user_message = input(">> ")
    # while not user_message.strip():
    #     user_message = input(">> ")
    #     if user_message.lower() == "exit":
    #         break
    user_session_id = 'id'
    while True:
        chat_history = get_chat_history(user_session_id)
        # async with agent.run_mcp_servers():  
            # result = await agent.run(user_prompt=user_message, message_history=chat_history)
        # nodes = []
        # prompt = 'Analyze the usage of analytics dashboards that are hosted by EP, provide statistics about the usage of the dashboards per event, which are most used what are they used for and by which partners'
        
        prompt = 'provide inforamation about the usage of document entries in KMS. Include information about partners that are using it, adoption patterns, usage trends etc.'
        async with agent.run_mcp_servers():
            # async with agent.iter(prompt, usage_limits=UsageLimits(request_limit=3)) as agent_run:
            async with agent.iter(prompt) as agent_run:
                async for node in agent_run:
                    # Print the node type
                    print(f"Node: {type(node).__name__}")
                    
                    # Handle each node type
                    if isinstance(node, UserPromptNode):
                        # UserPromptNode just contains the initial prompt, already printed above
                        pass
                        
                    elif isinstance(node, ModelRequestNode):
                        # ModelRequestNode contains the request to the model
                        print("  Sending request to model...")
                        
                    elif isinstance(node, CallToolsNode):
                        # CallToolsNode processes the model's response

                        # Print token usage information
                        usage = agent_run.ctx.state.usage
                        print(f"  Token Usage: {usage.request_tokens} prompt + {usage.response_tokens} completion = {usage.total_tokens} total tokens")

                        # Print only the text parts of the model response
                        text_parts = [part for part in node.model_response.parts if isinstance(part, TextPart)]
                        if text_parts:
                            print("  Model Response Text:")
                            for part in text_parts:
                                print(f"    {part.content}")
                        
                        # Stream tool events to see inputs and outputs
                        async with node.stream(agent_run.ctx) as event_stream:
                            async for event in event_stream:
                                if isinstance(event, FunctionToolCallEvent):
                                    # Tool input
                                    tool_call = event.part
                                    tool_name = tool_call.tool_name
                                    # args = json.loads(tool_call.args_as_json_str())
                                    
                                    # # Always print for create_message
                                    # if tool_name == "create_message":
                                    #     print(f"  LLM INTENT: {tool_name}")
                                    #     print(f"  QUERY GENERATED:")
                                    #     print(f"    {json.dumps(args, indent=2)}")
                                    # # For other tools, print only if debug is enabled
                                    # elif DEBUG or tool_name == "get_message_attachment_query_result":
                                    #     args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                                    #     print(f"    Tool Input: {tool_name}({args_str})")
                                        
                                elif isinstance(event, FunctionToolResultEvent):
                                    # Tool output
                                    tool_result = event.result
                                    if hasattr(tool_result, 'content'):
                                        tool_name = tool_result.tool_name
                                        text_content = tool_result.content.content[0]
                                        if isinstance(text_content, TextContent):


                                            print(f"Tool name: {tool_name}")
                                            # Print the tool name and its output
                                            

                                            
                                            # Always print for get_message_attachment_query_result
                                            if tool_name == "get_message_attachment_query_result" or \
                                                tool_name == "create_message" or \
                                                tool_name == "start_conversation" or \
                                                tool_name == "get_space":
                                                print(f" MCP SERVER RESULT:")
                                                try:
                                                    # Try to parse and pretty print the JSON content
                                                    result_content = json.loads(text_content.text)
                                                    print(f"    {json.dumps(result_content, indent=2)}")
                                                except:
                                                    # If not valid JSON, print as is
                                                    print(f"    {tool_result.content}")
                                            # Always print for create_message
                                            # elif tool_name == "create_message":
                                            #     print(f"  CREATE_MESSAGE RESULT:")
                                            #     try:
                                            #         # Try to parse and pretty print the JSON content
                                            #         result_content = json.loads(text_content.text)
                                            #         print(f"    {json.dumps(result_content, indent=2)}")
                                            #     except:
                                            #         # If not valid JSON, print as is
                                            #         print(f"    {tool_result.content.text}")
                                            # elif tool_name == "start_conversation":
                                            #     print(f"  START_CONVERSATION RESULT:")
                                                
                                            #     try:
                                            #         # Try to parse and pretty print the JSON content
                                            #         result_content = json.loads(text_content.text) 
                                            #         print(f"    {json.dumps(result_content, indent=2)}")
                                            #     except:
                                            #         # If not valid JSON, print as is
                                            #         print(f"    {tool_result.content.text}")
                                            # For other tools, print only if debug is enabled
                                            elif DEBUG:
                                                print(f"    Tool Output: {tool_name} → {text_content.text}")
                    
                    elif agent.is_end_node(node):
                        # End node contains the final result
                        print(f"  Final Result: {node.data.output}")
                    
                    print()  # Add a blank line between nodes
            
            print("Agent run complete!")
            print(f"Final Output: {agent_run.result.output}")
            print(f"Final Usage: {agent_run.result.usage.usage}")
            exit()

        #     nodes = []
        #     # Iterate through the run, recording each node along the way:
        #     async with agent.iter('I would like to know if to invest more effort into the EP page builder. Provide information about the EP page builder and the pages that were created with it.') as agent_run:
        #         async for node in agent_run:
        #             nodes.append(node)
        #             print(node)
        #             if isinstance(node, CallToolsNode):
        #                 model_response = node.model_response  # This is usually a Pydantic model
        #                 print(model_response)
                    
        #             # ask for user confirmation
        #             user_message = input("if continue (y/n) >> ")

                    

        #     print(nodes)
        #     # async for node in agent_run:
                # nodes.append(node)
            # result = await agent.iter(user_prompt=user_message, message_history=chat_history)
            # print(result.output)
            # print(result.usage.usage)
        
        # store_messages_in_history(user_session_id, result)

        
        user_message = input(
            "Please enter your question (or type 'exit' or Enter to quit): "
        )
        if user_message.lower() == "exit" or not user_message.strip():
            exit()
###########


    async with agent.run_mcp_servers():  
        result = await agent.run('ask genie to tell me how much entry view page loads were counted in the last 30 days in bloomberg internal production account')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.

asyncio.run(main())
