from typing import Dict, List, Callable, Awaitable, Any, AsyncGenerator
import asyncio
from datetime import datetime
from logging_config import get_logger


class OfficeChat:
    """Central office chat where all agents can communicate."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self._subscribers: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._streaming_subscribers: List[
            Callable[[Dict[str, Any], AsyncGenerator[str, None]], Awaitable[None]]
        ] = []
        self.logger = get_logger("office.chat")
        self.logger.info("OfficeChat initialized")

    def subscribe(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Subscribe to chat messages.

        Args:
            callback: Function to call when a new message is posted
        """
        self.logger.debug(f"New subscriber added: {callback.__qualname__}")
        self._subscribers.append(callback)

    def subscribe_streaming(
        self,
        callback: Callable[
            [Dict[str, Any], AsyncGenerator[str, None]], Awaitable[None]
        ],
    ) -> None:
        """Subscribe to streaming chat messages.

        Args:
            callback: Function to call when a new streaming message is posted
        """
        self.logger.debug(f"New streaming subscriber added: {callback.__qualname__}")
        self._streaming_subscribers.append(callback)

    async def post_message(self, content: str, sender: str = "System") -> None:
        """Post a message to the chat.

        Args:
            content: The message content
            sender: The name of the sender
        """
        self.logger.info(
            f"Message posted by {sender}: {content[:50]}{'...' if len(content) > 50 else ''}"
        )
        message = {
            "sender": sender,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        self.messages.append(message)

        # Notify all subscribers
        self.logger.debug(
            f"Notifying {len(self._subscribers)} subscribers about message from {sender}"
        )
        await self._notify_subscribers(message)

    async def post_streaming_message(
        self, content_stream: AsyncGenerator[str, None], sender: str = "System"
    ) -> None:
        """Post a streaming message to the chat.

        Args:
            content_stream: The message content as an async generator
            sender: The name of the sender
        """
        self.logger.info(f"Streaming message posted by {sender}")
        # Create a placeholder message
        message = {
            "sender": sender,
            "content": "",
            "timestamp": datetime.now().isoformat(),
            "is_streaming": True,
        }

        # Add message to the history
        self.messages.append(message)

        # Collect all chunks to build the final message
        chunks = []

        # Notify streaming subscribers
        self.logger.debug(
            f"Notifying {len(self._streaming_subscribers)} streaming subscribers"
        )
        await self._notify_streaming_subscribers(message, content_stream)

        # Collect chunks for the final message
        self.logger.debug("Collecting content chunks for final message")
        collected_content_stream = content_stream.__aiter__()
        try:
            while True:
                chunk = await collected_content_stream.__anext__()
                chunks.append(chunk)
        except StopAsyncIteration:
            self.logger.debug("Finished collecting content chunks")

        # Update the message with the complete content
        message["content"] = "".join(chunks)
        message["is_streaming"] = False
        self.logger.debug(
            f"Complete streaming message from {sender}: {message['content'][:50]}{'...' if len(message['content']) > 50 else ''}"
        )

    async def _notify_subscribers(self, message: Dict[str, Any]) -> None:
        """Notify all subscribers of a new message.

        Args:
            message: The message to notify subscribers about
        """
        # Create tasks for all subscribers
        tasks = [subscriber(message) for subscriber in self._subscribers]

        # Wait for all subscribers to process the message
        if tasks:
            self.logger.debug(f"Awaiting {len(tasks)} subscriber tasks")
            try:
                await asyncio.gather(*tasks)
                self.logger.debug("All subscriber tasks completed")
            except Exception as e:
                self.logger.error(f"Error notifying subscribers: {str(e)}")
                raise

    async def _notify_streaming_subscribers(
        self, message: Dict[str, Any], content_stream: AsyncGenerator[str, None]
    ) -> None:
        """Notify all streaming subscribers of a new streaming message.

        Args:
            message: The message metadata to notify subscribers about
            content_stream: The streaming content
        """
        # Create tasks for all streaming subscribers
        tasks = [
            subscriber(message, content_stream)
            for subscriber in self._streaming_subscribers
        ]

        # Wait for all subscribers to process the message
        if tasks:
            self.logger.debug(f"Awaiting {len(tasks)} streaming subscriber tasks")
            try:
                await asyncio.gather(*tasks)
                self.logger.debug("All streaming subscriber tasks completed")
            except Exception as e:
                self.logger.error(f"Error notifying streaming subscribers: {str(e)}")
                raise

    def get_chat_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get the chat history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        self.logger.debug(f"Getting chat history (limit: {limit})")
        if limit:
            return self.messages[-limit:]
        return self.messages
