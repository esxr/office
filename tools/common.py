from typing import Any, Dict, Optional
from tools.base import BaseTool


class AskOfficeTool(BaseTool):
    """Tool for an agent to post a message to the office global chat."""

    def __init__(self, office_chat_callback):
        """
        Args:
            office_chat_callback: Function to call when posting to office chat
        """
        super().__init__(
            name="ask_office",
            description="Post a message to the office global chat for other agents to see and potentially respond to.",
        )
        self.office_chat_callback = office_chat_callback

    async def _run(self, message: str, **kwargs) -> str:
        """Post a message to the office chat.

        Args:
            message: The message to post to the office chat

        Returns:
            Confirmation that the message was posted
        """
        await self.office_chat_callback(message)
        return f"Message posted to office chat: {message}"

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to post to the office chat",
                }
            },
            "required": ["message"],
        }


class NoResponseTool(BaseTool):
    """Tool for an agent to explicitly not respond to an office chat message."""

    def __init__(self):
        super().__init__(
            name="no_response",
            description="Use this tool when you decide not to respond to the current office chat message.",
        )

    async def _run(self, reason: Optional[str] = None, **kwargs) -> str:
        """Execute the no_response tool.

        Args:
            reason: Optional reason for not responding

        Returns:
            Confirmation that no response will be given
        """
        if reason:
            return f"No response given: {reason}"
        return "No response given"

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Optional reason for not responding",
                }
            },
            "required": [],
        }
