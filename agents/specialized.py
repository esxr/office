from typing import List

from agents.base import Agent
from office.chat import OfficeChat
from tools.base import BaseTool
from tools.google_search import GoogleSearchTool
from tools.python_runner import PythonRunnerTool
from tools.notepad import NotepadWriteTool, NotepadReadTool


class SalesAgent(Agent):
    """Sales specialist agent."""

    def __init__(
        self,
        name: str,
        office_chat: OfficeChat,
        additional_tools: List[BaseTool] = None,
        model_name: str = None,
    ):
        """
        Args:
            name: The name of the agent
            office_chat: The global office chat
            additional_tools: Additional tools to add to this agent
            model_name: The Ollama model to use for this agent
        """
        system_prompt = f"""You are {name}, a sales specialist.
You have expertise in sales strategies, customer relationship management, and business development.
You should respond to questions about:
- Sales strategies and techniques
- Customer acquisition and retention
- Sales metrics and KPIs
- CRM systems and processes
- Pricing strategies
- Sales forecasting

If a question is outside your domain of expertise, use the no_response tool.
Always think carefully about whether you should respond or not.
"""

        # Set up sales-specific tools
        tools = [
            GoogleSearchTool(),
            NotepadWriteTool("./notes/sales"),
            NotepadReadTool("./notes/sales"),
        ]

        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)

        super().__init__(
            name=name,
            role="Sales",
            office_chat=office_chat,
            tools=tools,
            model_name=model_name,
            system_prompt=system_prompt,
        )


class MarketingAgent(Agent):
    """Marketing specialist agent."""

    def __init__(
        self,
        name: str,
        office_chat: OfficeChat,
        additional_tools: List[BaseTool] = None,
        model_name: str = None,
    ):
        """
        Args:
            name: The name of the agent
            office_chat: The global office chat
            additional_tools: Additional tools to add to this agent
            model_name: The Ollama model to use for this agent
        """
        system_prompt = f"""You are {name}, a marketing specialist.
You have expertise in marketing strategies, brand management, digital marketing, and market analysis.
You should respond to questions about:
- Marketing campaigns and strategies
- Brand positioning and management
- Digital marketing channels (social media, email, content)
- Market research and analysis
- Customer segmentation
- Marketing metrics and ROI
- SEO and SEM

If a question is outside your domain of expertise, use the no_response tool.
Always think carefully about whether you should respond or not.
"""

        # Set up marketing-specific tools
        tools = [
            GoogleSearchTool(),
            NotepadWriteTool("./notes/marketing"),
            NotepadReadTool("./notes/marketing"),
        ]

        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)

        super().__init__(
            name=name,
            role="Marketing",
            office_chat=office_chat,
            tools=tools,
            model_name=model_name,
            system_prompt=system_prompt,
        )


class ProductAgent(Agent):
    """Product specialist agent."""

    def __init__(
        self,
        name: str,
        office_chat: OfficeChat,
        additional_tools: List[BaseTool] = None,
        model_name: str = None,
    ):
        """
        Args:
            name: The name of the agent
            office_chat: The global office chat
            additional_tools: Additional tools to add to this agent
            model_name: The Ollama model to use for this agent
        """
        system_prompt = f"""You are {name}, a product specialist.
You have expertise in product management, product development, UX/UI design, and market requirements.
You should respond to questions about:
- Product strategy and roadmapping
- Product development lifecycle
- User experience and user interface design
- Market requirements and competitive analysis
- Feature prioritization
- Product metrics and KPIs
- Agile methodologies
- Product launch strategies

If a question is outside your domain of expertise, use the no_response tool.
Always think carefully about whether you should respond or not.
"""

        # Set up product-specific tools
        tools = [
            GoogleSearchTool(),
            NotepadWriteTool("./notes/product"),
            NotepadReadTool("./notes/product"),
            PythonRunnerTool(),
        ]

        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)

        super().__init__(
            name=name,
            role="Product",
            office_chat=office_chat,
            tools=tools,
            model_name=model_name,
            system_prompt=system_prompt,
        )


class InfraAgent(Agent):
    """Infrastructure specialist agent."""

    def __init__(
        self,
        name: str,
        office_chat: OfficeChat,
        additional_tools: List[BaseTool] = None,
        model_name: str = None,
    ):
        """
        Args:
            name: The name of the agent
            office_chat: The global office chat
            additional_tools: Additional tools to add to this agent
            model_name: The Ollama model to use for this agent
        """
        system_prompt = f"""You are {name}, an infrastructure and DevOps specialist.
You have expertise in cloud infrastructure, DevOps practices, system administration, and software deployment.
You should respond to questions about:
- Cloud platforms (AWS, Azure, GCP)
- DevOps practices and tools
- CI/CD pipelines
- Containerization (Docker, Kubernetes)
- Infrastructure as Code (Terraform, CloudFormation)
- System monitoring and logging
- Security best practices
- Networking and VPNs
- Database administration

If a question is outside your domain of expertise, use the no_response tool.
Always think carefully about whether you should respond or not.
"""

        # Set up infrastructure-specific tools
        tools = [
            GoogleSearchTool(),
            NotepadWriteTool("./notes/infra"),
            NotepadReadTool("./notes/infra"),
            PythonRunnerTool(),
        ]

        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)

        super().__init__(
            name=name,
            role="Infrastructure",
            office_chat=office_chat,
            tools=tools,
            model_name=model_name,
            system_prompt=system_prompt,
        )
