"""The messages a step sends to the model."""

# Standard Library
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptPair:
    """The system and user messages of a model request.

    Attributes
    ----------
    system_message
        The instructions the agent runs with.
    user_message
        The text sent with the request's other content, such as the PDF.
    """

    system_message: str
    user_message: str
