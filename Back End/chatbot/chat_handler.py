from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from chatbot.chatbot_functions import (
    send_email_outlook,
    fetch_emails_outlook,
    book_meeting_outlook,
    get_all_work_items_devops,
    get_all_risk_items_devops,
    get_all_users_devops,
    get_total_priority_by_user_devops,
    update_work_item_assigned
)
from helper.chatgpt import send_chat_with_functions
from chatbot.chat_data_struc import ChatData


class ChatHandler:
    def __init__(self):
        self.chat_data = ChatData()
        self.chat_data.add_system_message(
            content="You are an intelligent assistant designed to support a project manager who utilizes Azure DevOps and Outlook. "
                    "You have access to tools that allow you to send emails, retrieve emails, schedule meetings, fetch work items, "
                    "retrieve risk items, list users, and calculate priority scores. Use these capabilities to provide comprehensive assistance "
                    "and streamline the project management process."
        )

        # Define tools as required by the new format
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "send_email_outlook",
                    "description": "Get a outlook deep link creating a draft for the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "The subject of the email."},
                            "body": {"type": "string", "description": "The content of the email."},
                            "to_recipients": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "A list of recipient email addresses."
                            }
                        },
                        "required": ["subject", "body", "to_recipients"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_emails",
                    "description": "Retrieve emails from the user's inbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "book_meeting",
                    "description": "Book a meeting using the Outlook API.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "The meeting subject."},
                            "start_time": {"type": "string", "description": "Start time in ISO 8601 format."},
                            "end_time": {"type": "string", "description": "End time in ISO 8601 format."},
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "A list of attendee email addresses."
                            },
                            "location": {"type": "string", "description": "The meeting location (optional)."},
                            "body": {"type": "string", "description": "The meeting agenda or details (optional)."},
                        },
                        "required": ["subject", "start_time", "end_time", "attendees"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_work_items",
                    "description": "Retrieve all work items from Azure DevOps.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_risk_items",
                    "description": "Retrieve all risk items from Azure DevOps.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_users",
                    "description": "Retrieve all Employee's from Azure DevOps and the number of tasks assigned to them..",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_priority_scores",
                    "description": "Retrieve the total priority score for each user based on their assigned work items.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
            },{
                "type": "function",
                "function": {
                    "name": "update_work_item_assignment",
                    "description": "Update the assigned user for a specific work item.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "work_item_id": {
                                "type": "integer",
                                "description": "The ID of the work item to be updated."
                            },
                            "user_email": {
                                "type": "string",
                                "description": "The email of the user to assign the work item to."
                            }
                        },
                        "required": ["work_item_id", "user_email"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

        # Map function names to their implementations
        self.function_mapping = {
            "send_email_outlook": send_email_outlook,
            "fetch_emails": fetch_emails_outlook,
            "book_meeting": book_meeting_outlook,
            "get_work_items": get_all_work_items_devops,
            "get_risk_items": get_all_risk_items_devops,
            "get_users": get_all_users_devops,
            "get_priority_scores": get_total_priority_by_user_devops,
            "update_work_item_assignment": update_work_item_assigned,

        }

    def handle_message(self, user_message, model="gpt-4o-mini"):
        """Handle user input, call tools if needed, and return a response."""
        self.chat_data.add_user_message(user_message)

        # Send chat with tools
        messages = self.chat_data.get_messages()
        response = send_chat_with_functions(messages, model=model, functions=self.tools)

        # Process tool calls (SDK uses .tool_calls list on the message object)
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            self.chat_data.add_assistant_tool_call(toolscall=tool_calls)
            return self._handle_tool_calls(tool_calls, depth=0)

        # Handle regular assistant responses
        assistant_message = response.content
        self.chat_data.add_assistant_message(content=assistant_message)
        return {"messages": self.chat_data.get_messages()}
    
    def _handle_tool_calls(self, tool_calls, depth=0):
        """Handle multiple tool calls in parallel and return the results."""
        if depth > 8:
            self.chat_data.add_assistant_message(
                content="Stopped after too many tool rounds. Please ask a simpler question."
            )
            return {"messages": self.chat_data.get_messages()}

        results = []
        
        # Debug: Log the total number of tool calls to process
        print(f"Processing {len(tool_calls)} tool calls...")

        # Process tool calls in parallel
        with ThreadPoolExecutor() as executor:
            future_to_tool_call = {
                executor.submit(self._execute_tool_call, tool_call): tool_call for tool_call in tool_calls
            }
            print(f"Submitted {len(future_to_tool_call)} tool calls for execution.")

            for future in as_completed(future_to_tool_call):
                tool_call = future_to_tool_call[future]
                try:
                    # Get the result of the tool call execution
                    result = future.result()
                    
                    # Debug: Log the result of the tool call
                    print(f"Tool call {tool_call.id} executed successfully. Result: {result}")

                    # Check if the result is None or unexpected
                    if result is None:
                        print(f"Warning: Tool call {tool_call.id} returned None.")
                    
                    results.append({
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                except Exception as e:
                    # Handle any exceptions and log errors
                    error_message = f"Error executing tool call {tool_call.id}: {str(e)}"
                    print(error_message)  # Debug: Log the error
                    results.append({
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"error": error_message}),  # Ensure content is JSON-formatted
                    })

        # Debug: Log the total results processed
        print(f"Processed {len(results)} tool call results.")

        # Append each tool response immediately after its corresponding tool call
        for result in results:
            # Debug: Log each result before appending
            print(f"Appending result for tool call {result['tool_call_id']}: {result['content']}")

            # Create the tool response message
            tool_response_message = {
                "role": "tool",
                "content": result["content"],
                "tool_call_id": result["tool_call_id"]
            }

            # Add the tool response message immediately after its tool call
            self.chat_data.add_tool_message(tool_response_message["tool_call_id"], tool_response_message["content"])

        # Debug: Log the updated conversation history before sending to the model
        print("Updated conversation history:")
        _messages = self.chat_data.get_messages()
        for message in _messages:
            print(message)

        # Send the updated conversation history back to the model for continuation
        response = send_chat_with_functions(messages=_messages, model="gpt-4o-mini", functions=self.tools)

        follow_tools = getattr(response, "tool_calls", None) or []
        if follow_tools:
            self.chat_data.add_assistant_tool_call(toolscall=follow_tools)
            return self._handle_tool_calls(follow_tools, depth=depth + 1)

        print("Model response received:")
        print(response.content)
        self.chat_data.add_assistant_message(content=response.content)
        return {"messages": self.chat_data.get_messages()}


    def _execute_tool_call(self, tool_call):
        try:
            # Log the tool call details for debugging
            print(f"Executing tool call {tool_call.id} with function: {tool_call.function.name} and arguments: {tool_call.function.arguments}")
            print(f"Raw tool call arguments: {tool_call.function.arguments}")

            # Access function name and arguments as attributes
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)  # Parse JSON string to dictionary

            # Retrieve the actual function from the mapping
            function = self.function_mapping.get(function_name)
            if not function:
                raise ValueError(f"Function '{function_name}' not found in function mapping.")

            # Call the function with the parsed arguments
            result = function(**arguments)  # Pass arguments as keyword arguments
            print(f"Result for tool call {tool_call.id}: {result}")
            return result

        except Exception as e:
            print(f"Error executing tool call {tool_call.id}: {str(e)}")
            return None


    def get_chat_history(self):
        """Return the current chat history."""
        return self.chat_data.get_messages()
