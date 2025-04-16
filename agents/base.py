from typing import Dict, List, Any, Callable, Awaitable, Optional, AsyncGenerator
import asyncio
import json
import os
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from tools.base import BaseTool
from tools.common import AskOfficeTool, NoResponseTool
from office.chat import OfficeChat
from logging_config import get_logger
from models import ModelName


class Agent:
    """Base class for all agents in the office."""

    def __init__(
        self,
        name: str,
        role: str,
        office_chat: OfficeChat,
        tools: List[BaseTool] = None,
        model_name: str = None,
        system_prompt: str = None,
    ):
        """
        Args:
            name: The name of the agent
            role: The role/department of the agent (e.g., Sales, Marketing)
            office_chat: The global office chat
            tools: List of tools available to this agent
            model_name: The Ollama model to use for this agent
            system_prompt: Custom system prompt for this agent
        """
        self.name = name
        self.role = role
        self.office_chat = office_chat

        # If no model name specified, get the default
        if model_name is None:
            model = ModelName.get_default()
            self.model_name = model.value
        else:
            # Convert string to enum if needed
            model = ModelName.from_string(model_name)
            self.model_name = model.value

        self.logger = get_logger(f"agent.{name.lower()}")
        self.logger.info(f"Initializing {name} agent with model {self.model_name}")

        # Create the Ollama-based LLM
        try:
            self.logger.debug(
                f"Creating ChatOllama instance with model {self.model_name}"
            )
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                temperature=0.7,
            )
            self.logger.debug("ChatOllama instance created successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChatOllama: {str(e)}")
            raise RuntimeError(
                f"Failed to initialize ChatOllama: {str(e)}. Make sure Ollama is running at {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}"
            ) from e

        # Set the default system prompt if none is provided
        if system_prompt is None:
            system_prompt = f"""You are {name}, who works in the {role} department. 
You have expertise in {role.lower()} topics. 
You are part of an office environment where multiple specialized agents collaborate.
When you receive a message in the office chat, you should only respond if it relates to your expertise.
If the question is outside your domain, use the no_response tool.
Always think carefully about whether you should respond or not.
"""

        self.system_prompt = system_prompt
        self.messages = [SystemMessage(content=system_prompt)]
        self.logger.debug("System prompt set")

        # Set up tools
        self.tools = tools or []

        # Add the common tools that all agents must have
        self._add_common_tools()

        # Subscribe to the office chat
        self.office_chat.subscribe(self._handle_chat_message)
        self.logger.info(f"{name} agent initialized with {len(self.tools)} tools")

    def _add_common_tools(self) -> None:
        """Add the common tools that all agents must have."""
        self.logger.debug("Adding common tools to agent")
        # Add ask_office tool
        self.tools.append(AskOfficeTool(self.office_chat.post_message))

        # Add no_response tool
        self.tools.append(NoResponseTool())
        self.logger.debug("Common tools added")

    def _format_tools_for_prompt(self) -> str:
        """Format the agent's tools as a string for the prompt."""
        self.logger.debug("Formatting tools for prompt")
        tools_str = "You have access to the following tools:\n\n"

        for tool in self.tools:
            schema = tool.get_schema()
            params_str = json.dumps(schema["parameters"], indent=2)
            tools_str += f"Tool: {schema['name']}\n"
            tools_str += f"Description: {schema['description']}\n"
            tools_str += f"Parameters: {params_str}\n\n"

        tools_str += """
To use a tool, respond with the following JSON schema:
{
  "tool": "tool_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "reasoning": "Your step-by-step reasoning for why this tool should be used"
}
"""
        return tools_str

    async def _handle_chat_message(self, message: Dict[str, Any]) -> None:
        """Handle a new message in the office chat.

        Args:
            message: The chat message to handle
        """
        # self.logger.info(
        #     f"Handling chat message from {message['sender']}: {message['content'][:50]}{'...' if len(message['content']) > 50 else ''}"
        # )

        # Skip messages sent by this agent
        if message["sender"] == self.name:
            self.logger.debug("Skipping message from self")
            return

        # Process the message
        self.logger.debug("Processing message")
        try:
            response = await self._process_message(message)

            # If we have a response, post it to the chat
            if response:
                self.logger.debug(
                    f"Posting response to office chat: {response[:50]}{'...' if len(response) > 50 else ''}"
                )
                await self.office_chat.post_message(response, sender=self.name)
            else:
                self.logger.debug("No response generated")
        except Exception as e:
            self.logger.error(f"Error handling chat message: {str(e)}")
            # Don't catch the error, let it propagate
            raise

    async def _process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Process a message and generate a response.

        Args:
            message: The message to process

        Returns:
            The response to post to the chat, or None if no response
        """
        self.logger.debug("Beginning message processing")
        # Format the message for the LLM
        content = f"{message['sender']}: {message['content']}"

        # Add the message to the agent's history
        self.messages.append(HumanMessage(content=content))

        # Create a prompt with the tools description
        tools_prompt = self._format_tools_for_prompt()
        self.messages.append(HumanMessage(content=tools_prompt))

        # Get a response from the LLM
        self.logger.debug(f"Calling LLM (model: {self.model_name})")
        try:
            response = await self.llm.ainvoke(self.messages)
            self.logger.debug(
                f"LLM response received: {response.content[:50]}{'...' if len(response.content) > 50 else ''}"
            )
            self.messages.append(response)
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            raise

        # Extract the tool call if any
        self.logger.debug("Extracting tool call from response")
        tool_call = self._extract_tool_call(response.content)

        if tool_call:
            self.logger.info(f"Tool call extracted: {tool_call.get('tool')}")
            tool_name = tool_call.get("tool")
            parameters = tool_call.get("parameters", {})

            # Find the tool by name
            tool = next((t for t in self.tools if t.name == tool_name), None)

            if tool:
                # Execute the tool
                self.logger.debug(
                    f"Executing tool {tool_name} with parameters: {parameters}"
                )
                try:
                    result = await tool.run(**parameters)
                    self.logger.debug(f"Tool execution completed: {result}")

                    # If the tool is no_response, don't respond to the chat
                    if tool_name == "no_response":
                        self.logger.info(
                            "Using no_response tool, not responding to chat"
                        )
                        return None

                    # If the tool is ask_office, the message has already been posted
                    if tool_name == "ask_office":
                        self.logger.info(
                            "Using ask_office tool, message already posted"
                        )
                        return None

                    # Return the tool result
                    tool_result = f"I used the {tool_name} tool and got: {json.dumps(result, indent=2)}"
                    self.logger.debug(
                        f"Returning tool result: {tool_result[:50]}{'...' if len(tool_result) > 50 else ''}"
                    )
                    return tool_result
                except Exception as e:
                    self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
                    raise
            else:
                self.logger.warning(f"Tool {tool_name} not found")

        # If no tool was called, return the response as is
        self.logger.debug("No tool call found, returning raw response")
        return response.content

    def _extract_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract a tool call from the LLM response content.

        Args:
            content: The LLM response content

        Returns:
            Dict containing tool call information, or None if no tool call
        """
        self.logger.debug("Attempting to extract tool call from content")
        try:
            # Try to parse the entire content as JSON
            self.logger.debug("Trying to parse entire content as JSON")
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON object between curly braces
            self.logger.debug("Trying to extract JSON between curly braces")
            try:
                start_idx = content.find("{")
                end_idx = content.rfind("}")

                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx : end_idx + 1]
                    self.logger.debug(
                        f"Extracted JSON string: {json_str[:50]}{'...' if len(json_str) > 50 else ''}"
                    )
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.debug(f"Failed to extract JSON: {str(e)}")

        self.logger.debug("No tool call found in content")
        return None

    async def ask(self, question: str) -> str:
        """Ask the agent a direct question.

        Args:
            question: The question to ask

        Returns:
            The agent's response
        """
        self.logger.info(
            f"Direct question to {self.name}: {question[:50]}{'...' if len(question) > 50 else ''}"
        )
        # Process the message as if it were sent to the agent directly
        message = {"sender": "User", "content": question, "timestamp": None}

        try:
            response = await self._process_message(message)
            self.logger.debug(
                f"Response generated: {response[:50] if response else 'None'}{'...' if response and len(response) > 50 else ''}"
            )
            return response or "No response"
        except Exception as e:
            self.logger.error(f"Error processing direct question: {str(e)}")
            raise

    async def _process_message_streaming(
        self, message: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Process a message and generate a streaming response.

        Args:
            message: The message to process

        Yields:
            Chunks of the response as they are generated
        """
        self.logger.debug("Beginning streaming message processing")
        # Format the message for the LLM
        content = f"{message['sender']}: {message['content']}"

        # Add the message to the agent's history
        self.messages.append(HumanMessage(content=content))

        # Create a prompt with the tools description
        tools_prompt = self._format_tools_for_prompt()
        self.messages.append(HumanMessage(content=tools_prompt))

        # Get a streaming response from the LLM
        self.logger.debug(
            f"Starting streaming response from LLM (model: {self.model_name})"
        )
        try:
            response_chunks = []
            self.logger.debug("Streaming response from LLM...")
            async for chunk in self.llm.astream(self.messages):
                if hasattr(chunk, "content") and chunk.content:
                    response_chunks.append(chunk.content)
                    self.logger.debug(f"Received chunk: {chunk.content}")
                    yield chunk.content

            # Combine all chunks to get the full response
            full_response = "".join(response_chunks)
            self.logger.debug(
                f"Full response received: {full_response[:50]}{'...' if len(full_response) > 50 else ''}"
            )

            # Save the full response to the message history
            self.messages.append(AIMessage(content=full_response))

            # Extract the tool call if any
            self.logger.debug("Extracting tool call from full response")
            tool_call = self._extract_tool_call(full_response)

            if tool_call:
                self.logger.info(f"Tool call extracted: {tool_call.get('tool')}")
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})

                # Find the tool by name
                tool = next((t for t in self.tools if t.name == tool_name), None)

                if tool:
                    # Execute the tool
                    self.logger.debug(
                        f"Executing tool {tool_name} with parameters: {parameters}"
                    )
                    try:
                        result = await tool.run(**parameters)
                        self.logger.debug(f"Tool execution completed: {result}")

                        # If the tool is no_response, don't respond to the chat
                        if tool_name == "no_response":
                            self.logger.info(
                                "Using no_response tool, not responding to chat"
                            )
                            return

                        # If the tool is ask_office, the message has already been posted
                        if tool_name == "ask_office":
                            self.logger.info(
                                "Using ask_office tool, message already posted"
                            )
                            return

                        # Return the tool result
                        tool_result = f"\n\nI used the {tool_name} tool and got: {json.dumps(result, indent=2)}"
                        self.logger.debug(
                            f"Yielding tool result: {tool_result[:50]}{'...' if len(tool_result) > 50 else ''}"
                        )
                        yield tool_result
                    except Exception as e:
                        self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        error_msg = f"\n\nError executing tool {tool_name}: {str(e)}"
                        yield error_msg
                        raise
                else:
                    self.logger.warning(f"Tool {tool_name} not found")
        except Exception as e:
            self.logger.error(f"Error during streaming: {str(e)}")
            error_msg = f"\n\nError during streaming: {str(e)}"
            yield error_msg
            raise

    async def ask_streaming(self, question: str) -> AsyncGenerator[str, None]:
        """Ask the agent a direct question with streaming response.

        Args:
            question: The question to ask

        Yields:
            Chunks of the response as they are generated
        """
        self.logger.info(
            f"Direct streaming question to {self.name}: {question[:50]}{'...' if len(question) > 50 else ''}"
        )
        # Process the message as if it were sent to the agent directly
        message = {"sender": "User", "content": question, "timestamp": None}

        try:
            self.logger.debug("Starting streaming response")
            async for chunk in self._process_message_streaming(message):
                yield chunk
            self.logger.debug("Streaming response completed")
        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}")
            raise
