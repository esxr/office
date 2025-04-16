import os
from typing import Any, Dict
from pathlib import Path

from tools.base import BaseTool


class NotepadWriteTool(BaseTool):
    """Tool for writing content to a file."""

    def __init__(self, notes_dir: str = "./notes"):
        super().__init__(
            name="notepad_write",
            description="Write content to a file in the notes directory.",
        )
        self.notes_dir = notes_dir
        # Create the notes directory if it doesn't exist
        Path(self.notes_dir).mkdir(parents=True, exist_ok=True)

    async def _run(self, filename: str, content: str, **kwargs) -> str:
        """Write content to a file.

        Args:
            filename: Name of the file to write to
            content: Content to write to the file

        Returns:
            Confirmation message
        """
        # Ensure we're only writing to the notes directory
        # and prevent directory traversal attacks
        clean_filename = os.path.basename(filename)
        file_path = os.path.join(self.notes_dir, clean_filename)

        # Write the content to the file
        with open(file_path, "w") as f:
            f.write(content)

        return f"Content written to {clean_filename} successfully"

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file to write to",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["filename", "content"],
        }


class NotepadReadTool(BaseTool):
    """Tool for reading content from a file."""

    def __init__(self, notes_dir: str = "./notes"):
        super().__init__(
            name="notepad_read",
            description="Read content from a file in the notes directory.",
        )
        self.notes_dir = notes_dir
        # Create the notes directory if it doesn't exist
        Path(self.notes_dir).mkdir(parents=True, exist_ok=True)

    async def _run(self, filename: str, **kwargs) -> Dict[str, Any]:
        """Read content from a file.

        Args:
            filename: Name of the file to read from

        Returns:
            Dict containing the file content and success status
        """
        # Ensure we're only reading from the notes directory
        # and prevent directory traversal attacks
        clean_filename = os.path.basename(filename)
        file_path = os.path.join(self.notes_dir, clean_filename)

        result = {"content": "", "success": True, "error": None}

        try:
            # Check if the file exists
            if not os.path.exists(file_path):
                result["success"] = False
                result["error"] = f"File {clean_filename} not found"
                return result

            # Read the content from the file
            with open(file_path, "r") as f:
                result["content"] = f.read()

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file to read from",
                }
            },
            "required": ["filename"],
        }
