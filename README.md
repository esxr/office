# Agent Office

A collaborative multi-agent system where specialized agents communicate through a global chat to solve tasks.

![](/office.png)

## Overview

Agent Office creates a virtual office environment where multiple specialized AI agents can collaborate to solve problems. Each agent has:

1. Domain-specific expertise (Sales, Marketing, Product, Infrastructure)
2. Specialized tools related to their domain
3. Common tools that allow them to communicate with other agents

The system leverages ChatOllama to power each agent, making it easy to run locally on your machine.

## Features

- **Multiple Specialized Agents**: Each with unique expertise and tools
- **Global Chat**: Central communication channel for all agents
- **Domain-Specific Tools**: Tools tailored to each agent's expertise
- **Common Communication Tools**: All agents have `ask_office` and `no_response` tools
- **Interactive Interface**: Chat with the agents directly through a command-line interface
- **Streaming Responses**: See agent responses in real-time as they are generated

## Agent Roles

- **Sales Agent (Roger)**: Specializes in sales strategies, CRM, and business development
- **Marketing Agent (Peter)**: Expert in marketing strategies, brand management, and digital marketing
- **Product Agent (Luke)**: Focuses on product management, development, UX/UI design, and market requirements
- **Infrastructure Agent (Diana)**: Specializes in cloud infrastructure, DevOps, and system administration

## Tools

Each agent has access to various tools:

### Common Tools (All Agents)

- **ask_office**: Posts messages to the global chat
- **no_response**: Allows agents to explicitly not respond to a message

### Domain-Specific Tools

- **Google Search**: Web search via SerpAPI
- **Python Runner**: Executes Python code
- **Notepad (Read/Write)**: Manages files in agent-specific directories

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/agent-office.git
   cd agent-office
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:

   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file to add your API keys:

   ```
   SERPAPI_API_KEY=your_serpapi_key_here
   OLLAMA_HOST=http://localhost:11434
   ```

5. Install and run Ollama:
   - Follow instructions at [Ollama.ai](https://ollama.ai) to install
   - Pull the default model: `ollama pull deepseek-r1:8b-llama-distill-q8_0:8b-llama-distill-q8_0`

## Usage

Run the main application with streaming responses (default):

```bash
python main.py
```

Or run without streaming responses:

```bash
python main.py --no-streaming
```

Specify a different Ollama model:

```bash
python main.py --model mistral
```

### Interactive Commands

- `help`: Display available commands
- `history`: Show chat history
- `ask <agent_name> <question>`: Ask a specific agent directly
- `exit`: Quit the application

### Testing

Run the test script to quickly test the system:

```bash
python test_office.py
```

## Project Structure

```
agent-office/
├── agents/             # Agent implementations
│   ├── __init__.py
│   ├── base.py         # Base Agent class
│   └── specialized.py  # Specialized agent implementations
├── office/             # Office chat implementation
│   ├── __init__.py
│   └── chat.py         # Office chat system
├── tools/              # Tool implementations
│   ├── __init__.py
│   ├── base.py         # Base Tool class
│   ├── common.py       # Common tools
│   ├── google_search.py
│   ├── notepad.py
│   └── python_runner.py
├── notes/              # Directory for agent notes
├── .env.example        # Environment variables example
├── .env                # Your environment variables (create this)
├── main.py             # Main application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── test_office.py      # Test script
```

## Requirements

- Python 3.8+
- Ollama installed locally
- SerpAPI key (for Google Search tool)

## Customization

- Add new tools by extending the `BaseTool` class
- Create new agent types by extending the `Agent` class
- Modify existing agent prompts to specialize them further
