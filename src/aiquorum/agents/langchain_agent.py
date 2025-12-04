from typing import Tuple, Any, Optional
import os
from aiquorum.agents.base import BaseAgent
from aiquorum.types import AgentResponse, AgentContext

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except ImportError:
    # Dependencies handled in pyproject.toml
    pass

# Metaprompt Templates
INITIAL_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "{instructions}"),
    ("user", "User Prompt: {original_prompt}")
])

CRITIQUE_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "{instructions}"),
    ("user", """Original Prompt: {original_prompt}

History of responses:
{history_text}

Task: Review the previous answers, critique them, and provide an improved answer.
Evaluate the strengths and weaknesses of the previous responses.
Then, provide your own improved answer based on your specific perspective.
Finally, provide a confidence score (0.0 to 1.0) indicating how certain you are that this is the best possible answer.

Ends your response with a JSON object containing 'confidence' (float 0-1) field, like: {{"confidence": 0.9}}""")
])

class LangChainAgent(BaseAgent):
    """
    An agent that uses a LangChain ChatModel (e.g., ChatOpenAI, ChatAnthropic).
    Can be used with OpenRouter by configuring the base_url.
    """
    def __init__(self, name: str, instructions: str, model: Any):
        """
        :param name: Name of the agent.
        :param instructions: System prompt/persona.
        :param model: A LangChain ChatModel instance (e.g. ChatOpenAI).
        """
        super().__init__(name, instructions)
        self.model = model

    def process(self, context: AgentContext) -> AgentResponse:
        if context.current_step == 0:
            prompt_value = INITIAL_PROMPT_TEMPLATE.invoke({
                "instructions": self.instructions,
                "original_prompt": context.original_prompt
            })
        else:
            history_text = "\n\n".join(
                [f"Step {r.step_number} - {r.agent_name}: {r.content} (Confidence: {r.confidence})"
                 for r in context.previous_responses]
            )
            prompt_value = CRITIQUE_PROMPT_TEMPLATE.invoke({
                "instructions": self.instructions,
                "original_prompt": context.original_prompt,
                "history_text": history_text
            })

        # Call the model
        result = self.model.invoke(prompt_value)
        content = result.content

        confidence = self._extract_confidence(content)

        return AgentResponse(
            content=content,
            confidence=confidence,
            agent_name=self.name,
            step_number=context.current_step
        )

    def _extract_confidence(self, text: str) -> float:
        # Simple heuristic or regex could go here.
        # For now, let's just look for "confidence": 0.X or confidence: 0.X
        import re
        # Regex explanation:
        # ["']?       : Optional opening quote
        # confidence  : Literal "confidence"
        # ["']?       : Optional closing quote
        # \s*[:=]\s*  : Separator (colon or equals), optional whitespace
        # ([0-9]*\.?[0-9]+) : Float capture group
        # We need to handle optional negative sign for testing robustness, though confidence should be positive.
        match = re.search(r'["\']?confidence["\']?\s*[:=]\s*(-?[0-9]*\.?[0-9]+)', text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                return max(0.0, min(1.0, val))
            except ValueError:
                pass
        return 0.5  # Default fallback


class OpenRouterAgent(LangChainAgent):
    """
    Convenience class for OpenRouter.
    """
    def __init__(self, name: str, instructions: str, model: str, api_key: Optional[str] = None):
        """
        Initialize an OpenRouter agent.

        :param name: Name of the agent.
        :param instructions: System prompt.
        :param model: Model identifier (e.g., 'openai/gpt-4-turbo').
        :param api_key: OpenRouter API Key. If None, checks OPENROUTER_API_KEY env var.
        """
        _api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not _api_key:
            raise ValueError("OpenRouter API key must be provided or set in OPENROUTER_API_KEY environment variable.")

        llm = ChatOpenAI(
            model=model,
            openai_api_key=_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/jules/aiquorum", # Placeholder
                "X-Title": "AIQuorum"
            }
        )
        super().__init__(name, instructions, llm)
