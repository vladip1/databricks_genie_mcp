import asyncio
from pydantic_ai import Agent, CallToolsNode, ModelRequestNode, UserPromptNode
from pydantic_ai.messages import ToolCallPart, ToolReturnPart, FunctionToolCallEvent, FunctionToolResultEvent, TextPart
import json
from pydantic_ai.mcp import MCPServerHTTP
from history import get_chat_history, store_messages_in_history

server = MCPServerHTTP(url='http://localhost:8000/sse')  

from pydantic_ai.models.bedrock import BedrockConverseModel


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
        prompt = 'Analyze the usage of analytics dashboards that are hosted by EP, provide statistics about the usage of the dashboards per event, which are most used what are they used for and by which partners'
        
        async with agent.run_mcp_servers():
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
                        print("  Model responded, processing tool calls...")

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
                                    args = json.loads(tool_call.args_as_json_str())
                                    args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                                    print(f"    Tool Input: {tool_call.tool_name}({args_str})")
                                        
                                elif isinstance(event, FunctionToolResultEvent):
                                    # Tool output
                                    tool_result = event.result
                                    if hasattr(tool_result, 'content'):
                                        print(f"    Tool Output: {tool_result.tool_name} → {tool_result.content}")
                    
                    elif agent.is_end_node(node):
                        # End node contains the final result
                        print(f"  Final Result: {node.data.output}")
                    
                    print()  # Add a blank line between nodes
            
            print("Agent run complete!")
            print(f"Final Output: {agent_run.result.output}")

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