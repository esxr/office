#!/usr/bin/env python3
"""
Check if Ollama is properly installed and running.
"""

import os
import sys
import requests
import subprocess
from dotenv import load_dotenv
from models import ModelName


def check_ollama():
    """Check if Ollama is installed and running."""
    # Load environment variables from .env file
    load_dotenv()

    # Get default model from environment
    default_model = ModelName.get_default().value

    # Get Ollama host from environment variables or use default
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    print(f"Checking Ollama at {ollama_host}...")

    # Check if ollama binary exists in PATH
    try:
        subprocess.run(["which", "ollama"], capture_output=True, check=True)
        print("✅ Ollama is installed")
    except subprocess.CalledProcessError:
        print("❌ Ollama binary not found in PATH")
        print("Please install Ollama first: https://ollama.ai/download")
        return False

    # Check if Ollama server is running
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama server is running with {len(models)} models available:")
            for model in models:
                print(f"  - {model.get('name')}")

            # Check if we have the required models
            model_names = [model.get("name") for model in models]

            if default_model not in model_names:
                print(f"\n⚠️ {default_model} model not found, downloading...")
                print(f"Run: ollama pull {default_model}")
                return False

            return True
        else:
            print(f"❌ Ollama server responded with status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Failed to connect to Ollama server at {ollama_host}")
        print(
            "Make sure Ollama is running. You can start it with the command: ollama serve"
        )
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {str(e)}")
        return False


if __name__ == "__main__":
    if check_ollama():
        print("\n✅ Ollama is properly set up and running")
        sys.exit(0)
    else:
        print(
            "\n❌ There are issues with your Ollama setup. Please fix them before running the Agent Office"
        )
        sys.exit(1)
