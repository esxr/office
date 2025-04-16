import asyncio
import sys
from dotenv import load_dotenv
from main import setup_office
from check_ollama import check_ollama


async def handle_streaming_response(message, content_stream):
    """Handle streaming responses during testing."""
    sender = message["sender"]
    print(f"\n{sender}: ", end="", flush=True)

    async for chunk in content_stream:
        print(chunk, end="", flush=True)

    print()  # Add a newline at the end


async def handle_message(message):
    """Handle regular responses during testing."""
    # Skip user messages since we already printed them
    if message["sender"] == "User":
        return

    print(f"\n{message['sender']}: {message['content']}")


async def test_office():
    """Simple test for the Agent Office system."""
    # Load environment variables
    load_dotenv()

    # Check if Ollama is running
    if not check_ollama():
        print("Please fix the Ollama setup issues before running the test")
        sys.exit(1)

    print("Setting up the office environment for testing...")

    # Set up the office environment with a small model for faster testing
    office_components = await setup_office(
        model_name="deepseek-r1:8b-llama-distill-q8_0:8b-llama-distill-q8_0"
    )
    office_chat = office_components["office_chat"]

    # Subscribe to messages
    office_chat.subscribe_streaming(handle_streaming_response)
    office_chat.subscribe(handle_message)

    # Post some test messages
    messages = [
        "Hello, I need help with our sales strategy for the new product launch.",
        "What marketing channels should we focus on for our target demographic?",
        "Can someone help me set up a CI/CD pipeline for our application?",
        "What are the key metrics we should track for our product?",
    ]

    for message in messages:
        print(f"\nUser: {message}")
        await office_chat.post_message(message, sender="User")
        # Wait for agents to process and respond
        await asyncio.sleep(5)  # Give more time for responses in test mode

    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_office())
