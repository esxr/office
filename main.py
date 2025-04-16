import asyncio
import os
import argparse
import sys
import threading
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

from agents import SalesAgent, MarketingAgent, ProductAgent, InfraAgent
from office import OfficeChat
from check_ollama import check_ollama
from logging_config import setup_logging, get_logger
from debug_async import setup_debugging, monitor_task, dump_tasks
from models import ModelName


async def setup_office(model_name: str = None) -> Dict[str, Any]:
    """Set up the office environment with all agents.

    Args:
        model_name: The Ollama model to use for all agents

    Returns:
        Dict containing office components
    """
    logger = get_logger("setup")

    # If no model name specified, get the default from environment
    if model_name is None:
        model = ModelName.get_default()
        model_name = model.value
    else:
        # Convert string to enum if needed
        model = ModelName.from_string(model_name)
        model_name = model.value

    logger.info(f"Setting up office with model: {model_name}")

    # Create the global office chat
    logger.debug("Creating office chat")
    office_chat = OfficeChat()

    # Create the agents
    logger.info("Creating agents")
    agents = {}

    try:
        logger.debug("Creating Roger (Sales)")
        agents["roger"] = SalesAgent(
            name="Roger", office_chat=office_chat, model_name=model_name
        )

        logger.debug("Creating Peter (Marketing)")
        agents["peter"] = MarketingAgent(
            name="Peter", office_chat=office_chat, model_name=model_name
        )

        logger.debug("Creating Luke (Product)")
        agents["luke"] = ProductAgent(
            name="Luke", office_chat=office_chat, model_name=model_name
        )

        # logger.debug("Creating Diana (Infrastructure)")
        # agents["diana"] = InfraAgent(
        #     name="Diana", office_chat=office_chat, model_name=model_name
        # )

        logger.info(f"Created {len(agents)} agents successfully")
    except Exception as e:
        logger.error(f"Error creating agents: {str(e)}")
        raise

    return {"office_chat": office_chat, "agents": agents}


async def interactive_chat(office_components: Dict[str, Any]) -> None:
    """Run an interactive chat session with the office.

    Args:
        office_components: Dict containing office components
    """
    logger = get_logger("interactive_chat")
    logger.info("Starting regular interactive chat")

    office_chat = office_components["office_chat"]
    agents = office_components["agents"]

    print("\n===== Welcome to the Agent Office =====\n")
    print("Agents available:")
    for name, agent in agents.items():
        print(f"- {name} ({agent.role})")
    print("\nEnter your messages to the office chat below.")
    print("Type 'exit' to quit or 'help' for more commands.\n")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            logger.info("User exiting chat")
            print("Exiting the office chat. Goodbye!")
            break

        if user_input.lower() == "help":
            logger.debug("User requested help")
            print("\nAvailable commands:")
            print("- exit: Exit the chat")
            print("- help: Show this help message")
            print("- history: Show the chat history")
            print("- ask <agent_name> <question>: Ask a specific agent directly")
            continue

        if user_input.lower() == "history":
            logger.debug("User requested chat history")
            history = office_chat.get_chat_history()
            print("\n----- Chat History -----")
            for msg in history:
                print(f"{msg['sender']}: {msg['content']}")
            print("------------------------")
            continue

        if user_input.lower().startswith("ask "):
            parts = user_input.split(" ", 2)
            if len(parts) < 3:
                logger.debug("Invalid ask command format")
                print("Usage: ask <agent_name> <question>")
                continue

            agent_name = parts[1].lower()
            question = parts[2]

            if agent_name not in agents:
                logger.warning(f"Agent '{agent_name}' not found")
                print(
                    f"Agent '{agent_name}' not found. Available agents: {', '.join(agents.keys())}"
                )
                continue

            logger.info(
                f"Asking agent {agent_name} directly: {question[:50]}{'...' if len(question) > 50 else ''}"
            )
            print(f"\nAsking {agent_name}...")
            try:
                response = await agents[agent_name].ask(question)
                print(f"{agent_name.capitalize()}: {response}")
                logger.debug(f"Direct ask to {agent_name} completed")
            except Exception as e:
                logger.error(f"Error in direct ask to {agent_name}: {str(e)}")
                print(f"\nError asking {agent_name}: {str(e)}")
            continue

        # Post the message to the office chat
        logger.info(
            f"Posting user message to office chat: {user_input[:50]}{'...' if len(user_input) > 50 else ''}"
        )
        try:
            await office_chat.post_message(user_input, sender="User")
            logger.debug("User message posted to office chat")
        except Exception as e:
            logger.error(f"Error posting message to office chat: {str(e)}")
            print(f"\nError posting message: {str(e)}")

        # Wait a bit for agents to process and respond
        logger.debug("Waiting for agent responses")
        await asyncio.sleep(1)


async def handle_streaming_response(
    message: Dict[str, Any], content_stream: AsyncGenerator[str, None]
) -> None:
    """Handle a streaming response from an agent.

    Args:
        message: The message metadata
        content_stream: The streaming content
    """
    logger = get_logger("stream_handler")
    sender = message["sender"]
    logger.debug(f"Handling streaming response from {sender}")

    print(f"\n{sender}: ", end="", flush=True)

    try:
        async for chunk in content_stream:
            print(chunk, end="", flush=True)

        print()  # Add a newline at the end
        logger.debug("Streaming response completed")
    except Exception as e:
        logger.error(f"Error handling streaming response: {str(e)}")
        print(f"\nError in streaming response: {str(e)}")
        raise


async def handle_regular_response(message: Dict[str, Any]) -> None:
    """Handle a regular response from an agent.

    Args:
        message: The message
    """
    logger = get_logger("response_handler")
    # Skip User messages since we already printed them
    if message["sender"] == "User":
        return

    logger.debug(f"Handling regular response from {message['sender']}")
    print(f"\n{message['sender']}: {message['content']}")


async def streaming_interactive_chat(office_components: Dict[str, Any]) -> None:
    """Run an interactive chat session with the office using streaming responses.

    Args:
        office_components: Dict containing office components
    """
    logger = get_logger("interactive_chat")
    logger.info("Starting streaming interactive chat")

    office_chat = office_components["office_chat"]
    agents = office_components["agents"]

    # Subscribe to streaming and regular messages
    logger.debug("Subscribing to office chat messages")
    office_chat.subscribe_streaming(handle_streaming_response)
    office_chat.subscribe(handle_regular_response)

    print("\n===== Welcome to the Agent Office (Streaming Mode) =====\n")
    print("Agents available:")
    for name, agent in agents.items():
        print(f"- {name} ({agent.role})")
    print("\nEnter your messages to the office chat below.")
    print("Type 'exit' to quit or 'help' for more commands.\n")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            logger.info("User exiting chat")
            print("Exiting the office chat. Goodbye!")
            break

        if user_input.lower() == "help":
            logger.debug("User requested help")
            print("\nAvailable commands:")
            print("- exit: Exit the chat")
            print("- help: Show this help message")
            print("- history: Show the chat history")
            print("- ask <agent_name> <question>: Ask a specific agent directly")
            continue

        if user_input.lower() == "history":
            logger.debug("User requested chat history")
            history = office_chat.get_chat_history()
            print("\n----- Chat History -----")
            for msg in history:
                print(f"{msg['sender']}: {msg['content']}")
            print("------------------------")
            continue

        if user_input.lower().startswith("ask "):
            parts = user_input.split(" ", 2)
            if len(parts) < 3:
                logger.debug("Invalid ask command format")
                print("Usage: ask <agent_name> <question>")
                continue

            agent_name = parts[1].lower()
            question = parts[2]

            if agent_name not in agents:
                logger.warning(f"Agent '{agent_name}' not found")
                print(
                    f"Agent '{agent_name}' not found. Available agents: {', '.join(agents.keys())}"
                )
                continue

            logger.info(
                f"Asking agent {agent_name} directly: {question[:50]}{'...' if len(question) > 50 else ''}"
            )
            print(f"\nAsking {agent_name}...")
            try:
                # Use streaming response
                async for chunk in agents[agent_name].ask_streaming(question):
                    print(chunk, end="", flush=True)
                print()  # Add a newline at the end
                logger.debug(f"Direct ask to {agent_name} completed")
            except Exception as e:
                logger.error(f"Error in direct ask to {agent_name}: {str(e)}")
                print(f"\nError asking {agent_name}: {str(e)}")
            continue

        # Post the message to the office chat
        logger.info(
            f"Posting user message to office chat: {user_input[:50]}{'...' if len(user_input) > 50 else ''}"
        )
        try:
            await office_chat.post_message(user_input, sender="User")
            logger.debug("User message posted to office chat")
        except Exception as e:
            logger.error(f"Error posting message to office chat: {str(e)}")
            print(f"\nError posting message: {str(e)}")

        # Wait a bit for agents to process and respond
        logger.debug("Waiting for agent responses")
        await asyncio.sleep(0.5)


async def main():
    """Main entry point for the Agent Office application."""
    # Load environment variables
    load_dotenv()

    # Get default model from environment
    default_model = ModelName.get_default().value

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Agent Office - A multi-agent collaboration system"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        help=f"Ollama model to use (default: {default_model})",
        choices=[model.value for model in ModelName],
    )
    parser.add_argument("--skip-check", action="store_true", help="Skip Ollama check")
    parser.add_argument(
        "--no-streaming", action="store_true", help="Disable streaming responses"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )
    parser.add_argument("--debug", action="store_true", help="Enable async debugging")
    parser.add_argument(
        "--debug-interval",
        type=int,
        default=30,
        help="Interval for task dumps in debug mode",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for monitored operations in debug mode",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit",
    )
    args = parser.parse_args()

    # If --list-models is specified, print available models and exit
    if args.list_models:
        print("Available models:")
        for model in ModelName:
            print(f"  {model.value}")
        sys.exit(0)

    # Set up logging
    setup_logging(args.log_level)
    logger = get_logger("main")
    logger.info(f"Starting Agent Office with model: {args.model}")

    # Set up debugging if requested
    if args.debug:
        logger.info(f"Setting up async debugging with interval {args.debug_interval}s")
        setup_debugging(args.debug_interval)

    # Check if Ollama is running
    if not args.skip_check:
        logger.info("Checking if Ollama is running")
        if not check_ollama():
            logger.error("Ollama check failed")
            print("Please fix the Ollama setup issues before running Agent Office")
            sys.exit(1)
        logger.info("Ollama check passed")
    else:
        logger.info("Skipping Ollama check")

    print(f"Using model: {args.model}")
    print("Setting up the office environment...")

    # Set up the office environment
    try:
        logger.info("Setting up office environment")
        if args.debug:
            office_components = await monitor_task(
                setup_office(model_name=args.model), timeout=args.timeout
            )
        else:
            office_components = await setup_office(model_name=args.model)

        logger.info("Office environment set up successfully")
    except Exception as e:
        logger.critical(f"Failed to set up office environment: {str(e)}")
        print(f"Error setting up office environment: {str(e)}")
        sys.exit(1)

    # Post a welcome message
    try:
        logger.info("Posting welcome message to office chat")
        if args.debug:
            await monitor_task(
                office_components["office_chat"].post_message(
                    "Welcome to the Agent Office! Ask a question that any of our agents can help with. You don't need to respond to this message. Use the `no_response` tool to avoid responding to this message.",
                    sender="System",
                ),
                timeout=args.timeout,
            )
        else:
            await office_components["office_chat"].post_message(
                "Welcome to the Agent Office! Ask a question that any of our agents can help with. You don't need to respond to this message. Use the `no_response` tool to avoid responding to this message.",
                sender="System",
            )
        logger.debug("Welcome message posted successfully")
    except Exception as e:
        logger.error(f"Error posting welcome message: {str(e)}")
        print(f"Error posting welcome message: {str(e)}")
        # If we couldn't post the welcome message, we should dump the tasks
        if args.debug:
            dump_tasks()

    # Run the interactive chat
    try:
        if args.no_streaming:
            logger.info("Starting interactive chat without streaming")
            await interactive_chat(office_components)
        else:
            logger.info("Starting interactive chat with streaming")
            await streaming_interactive_chat(office_components)
    except Exception as e:
        logger.critical(f"Error in interactive chat: {str(e)}")
        print(f"Fatal error: {str(e)}")
        # If something went wrong, dump the tasks
        if args.debug:
            dump_tasks()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
