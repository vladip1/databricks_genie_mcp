w.genie: Genie
class databricks.sdk.service.dashboards.GenieAPI
Genie provides a no-code experience for business users, powered by AI/BI. Analysts set up spaces that business users can use to ask questions using natural language. Genie uses data registered to Unity Catalog and requires at least CAN USE permission on a Pro or Serverless SQL warehouse. Also, Databricks Assistant must be enabled.

create_message(space_id: str, conversation_id: str, content: str) → Wait[GenieMessage]
Create conversation message.

Create new message in a [conversation](:method:genie/startconversation). The AI response uses all previously created messages in the conversation to respond.

Parameters:
space_id – str The ID associated with the Genie space where the conversation is started.

conversation_id – str The ID associated with the conversation.

content – str User message content.

Returns:
Long-running operation waiter for GenieMessage. See :method:wait_get_message_genie_completed for more details.

create_message_and_wait(space_id: str, conversation_id: str, content: str, timeout: datetime.timedelta = 0:20:00) → GenieMessage
execute_message_attachment_query(space_id: str, conversation_id: str, message_id: str, attachment_id: str) → GenieGetMessageQueryResultResponse
Execute message attachment SQL query.

Execute the SQL for a message query attachment. Use this API when the query attachment has expired and needs to be re-executed.

Parameters:
space_id – str Genie space ID

conversation_id – str Conversation ID

message_id – str Message ID

attachment_id – str Attachment ID

Returns:
GenieGetMessageQueryResultResponse

execute_message_query(space_id: str, conversation_id: str, message_id: str) → GenieGetMessageQueryResultResponse
[Deprecated] Execute SQL query in a conversation message.

Execute the SQL query in the message.

Parameters:
space_id – str Genie space ID

conversation_id – str Conversation ID

message_id – str Message ID

Returns:
GenieGetMessageQueryResultResponse

generate_download_full_query_result(space_id: str, conversation_id: str, message_id: str, attachment_id: str) → GenieGenerateDownloadFullQueryResultResponse
Generate full query result download.

Initiate full SQL query result download and obtain a transient ID for tracking the download progress. This call initiates a new SQL execution to generate the query result.

Parameters:
space_id – str Space ID

conversation_id – str Conversation ID

message_id – str Message ID

attachment_id – str Attachment ID

Returns:
GenieGenerateDownloadFullQueryResultResponse

get_message(space_id: str, conversation_id: str, message_id: str) → GenieMessage
Get conversation message.

Get message from conversation.

Parameters:
space_id – str The ID associated with the Genie space where the target conversation is located.

conversation_id – str The ID associated with the target conversation.

message_id – str The ID associated with the target message from the identified conversation.

Returns:
GenieMessage

get_message_attachment_query_result(space_id: str, conversation_id: str, message_id: str, attachment_id: str) → GenieGetMessageQueryResultResponse
Get message attachment SQL query result.

Get the result of SQL query if the message has a query attachment. This is only available if a message has a query attachment and the message status is EXECUTING_QUERY OR COMPLETED.

Parameters:
space_id – str Genie space ID

conversation_id – str Conversation ID

message_id – str Message ID

attachment_id – str Attachment ID

Returns:
GenieGetMessageQueryResultResponse

get_message_query_result(space_id: str, conversation_id: str, message_id: str) → GenieGetMessageQueryResultResponse
[Deprecated] Get conversation message SQL query result.

Get the result of SQL query if the message has a query attachment. This is only available if a message has a query attachment and the message status is EXECUTING_QUERY.

Parameters:
space_id – str Genie space ID

conversation_id – str Conversation ID

message_id – str Message ID

Returns:
GenieGetMessageQueryResultResponse

get_message_query_result_by_attachment(space_id: str, conversation_id: str, message_id: str, attachment_id: str) → GenieGetMessageQueryResultResponse
[Deprecated] Get conversation message SQL query result.

Get the result of SQL query if the message has a query attachment. This is only available if a message has a query attachment and the message status is EXECUTING_QUERY OR COMPLETED.

Parameters:
space_id – str Genie space ID

conversation_id – str Conversation ID

message_id – str Message ID

attachment_id – str Attachment ID

Returns:
GenieGetMessageQueryResultResponse

get_space(space_id: str) → GenieSpace
Get Genie Space.

Get details of a Genie Space.

Parameters:
space_id – str The ID associated with the Genie space

Returns:
GenieSpace

start_conversation(space_id: str, content: str) → Wait[GenieMessage]
Start conversation.

Start a new conversation.

Parameters:
space_id – str The ID associated with the Genie space where you want to start a conversation.

content – str The text of the message that starts the conversation.

Returns:
Long-running operation waiter for GenieMessage. See :method:wait_get_message_genie_completed for more details.

start_conversation_and_wait(space_id: str, content: str, timeout: datetime.timedelta = 0:20:00) → GenieMessage
wait_get_message_genie_completed(conversation_id: str, message_id: str, space_id: str, timeout: datetime.timedelta = 0:20:00, callback: Optional[Callable[[GenieMessage], None]]) → GenieMessage