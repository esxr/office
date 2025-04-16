import sys
from io import StringIO
from typing import Any, Dict
import traceback

from tools.base import BaseTool


class PythonRunnerTool(BaseTool):
    """Tool for executing Python code."""

    def __init__(self):
        super().__init__(
            name="python_runner",
            description="Execute Python code and return the output.",
        )

    async def _run(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Python code and return the results.

        Args:
            code: The Python code to execute

        Returns:
            Dict containing stdout, stderr, and execution status
        """
        # Create string buffers to capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        # Save the original stdout and stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        result = {"stdout": "", "stderr": "", "success": True}

        try:
            # Redirect stdout and stderr to our string buffers
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Execute the code
            exec(code, {})

            # Get the captured output
            result["stdout"] = stdout_capture.getvalue()

        except Exception as e:
            # Capture the exception information
            result["stderr"] = f"{str(e)}\n{traceback.format_exc()}"
            result["success"] = False

        finally:
            # Restore the original stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            # Get any stderr output even if there was no exception
            if not result["stderr"]:
                result["stderr"] = stderr_capture.getvalue()

        return result

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute"}
            },
            "required": ["code"],
        }
