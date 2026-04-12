import json
class ChatData:
    def __init__(self):
        self.messages = []  # Stores the conversation history

    def add_system_message(self, content):
        """Add a system message."""
        self.messages.append({"role": "system", "content": content})

    def add_user_message(self, content):
        """Add a user message."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content, function_call=None):
        """Add an assistant message. Optionally include a function call."""
        message = {"role": "assistant", "content": content}
        if function_call:
            message.pop("content")  # Remove 'content' if there's a function call
            message["function_call"] = function_call
        self.messages.append(message)

    def add_assistant_tool_call(self, toolscall):
        """Append an assistant turn with tool_calls in OpenAI Chat Completions shape."""
        if not toolscall:
            return
        if not isinstance(toolscall, (list, tuple)):
            toolscall = [toolscall]
        formatted = []
        for tc in toolscall:
            formatted.append(
                {
                    "id": tc.id,
                    "type": getattr(tc, "type", None) or "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
            )
        self.messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": formatted,
            }
        )

    def add_tool_message(self, tool_call_id, content):
        """Add a function message with its name and result (OpenAI requires string content)."""
        if content is None:
            serialized_content = "null"
        elif isinstance(content, (dict, list)):
            serialized_content = json.dumps(content, default=str)
        elif isinstance(content, str):
            serialized_content = content
        else:
            serialized_content = json.dumps(content, default=str)
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": serialized_content,
            }
        )



    def get_messages(self):
        """Retrieve the current conversation history."""
        return self.messages

    def reset(self):
        """Keep the first message and delete everything else."""
        if self.messages:
            self.messages = [self.messages[0]]
        else:
            self.messages = []