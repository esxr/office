import os
from typing import Any, Dict, List
import requests

from tools.base import BaseTool


class GoogleSearchTool(BaseTool):
    """Tool for searching the web using Google Search via SerpAPI."""

    def __init__(self, api_key: str = None):
        super().__init__(
            name="google_search",
            description="Search the web using Google Search. Returns search results for the given query.",
        )
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SerpAPI API key not provided and not found in environment variables"
            )

    async def _run(
        self, query: str, num_results: int = 5, **kwargs
    ) -> List[Dict[str, str]]:
        """Execute a Google search.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            List of search result objects
        """
        params = {
            "q": query,
            "num": num_results,
            "api_key": self.api_key,
            "engine": "google",
        }

        response = requests.get("https://serpapi.com/search", params=params)

        if response.status_code != 200:
            return {"error": f"Error during search: {response.text}"}

        search_results = response.json()
        organic_results = search_results.get("organic_results", [])

        results = []
        for result in organic_results[:num_results]:
            results.append(
                {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                }
            )

        return results

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on Google",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default: 5)",
                },
            },
            "required": ["query"],
        }
