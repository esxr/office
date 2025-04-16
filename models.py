from enum import Enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default model to use if not specified in environment
DEFAULT_MODEL = "deepseek-r1:8b-llama-distill-q8_0"


class ModelName(str, Enum):
    """Enum of supported model names."""

    DEEPSEEK_SMALL = "deepseek-r1:8b-llama-distill-q8_0"
    DEEPSEEK_CODER = "deepseek-coder"
    DEEPSEEK_INSTRUCT = "deepseek-instruct"
    LLAMA2 = "llama2"
    LLAMA3 = "llama3"
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"
    CODELLAMA = "codellama"

    @classmethod
    def from_string(cls, model_name: str) -> "ModelName":
        """Convert a string to a ModelName enum.

        Args:
            model_name: String representation of the model name

        Returns:
            The matching ModelName enum value
        """
        for model in cls:
            if model.value == model_name:
                return model

        # If no match, try to see if it's a variant with tags
        base_name = model_name.split(":")[0] if ":" in model_name else model_name
        for model in cls:
            if model.value == base_name:
                return model

        # If still no match, return default
        return cls.from_string(DEFAULT_MODEL)

    @classmethod
    def get_default(cls) -> "ModelName":
        """Get the default model from environment or fallback.

        Returns:
            The default ModelName
        """
        env_model = os.getenv("DEFAULT_MODEL", DEFAULT_MODEL)
        return cls.from_string(env_model)
