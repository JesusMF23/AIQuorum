from typing import Tuple, Any
from aiquorum.agents.base import BaseAgent
from aiquorum.types import AgentResponse, AgentContext

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_openai import ChatOpenAI
except ImportError:
    # Just a placeholder if dependencies are not installed,
    # but we added them to pyproject.toml so they should be there.
    pass

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
        system_msg = SystemMessage(content=self.instructions)

        if context.current_step == 0:
            user_content = f"User Prompt: {context.original_prompt}"
        else:
            history_text = "\n\n".join(
                [f"Step {r.step_number} - {r.agent_name}: {r.content} (Confidence: {r.confidence})"
                 for r in context.previous_responses]
            )
            user_content = (
                f"Original Prompt: {context.original_prompt}\n\n"
                f"History of responses:\n{history_text}\n\n"
                f"Task: Review the previous answers, critique them, and provide an improved answer. "
                f"Ends your response with a JSON object containing 'confidence' (float 0-1) field."
            )

        messages = [system_msg, HumanMessage(content=user_content)]

        # Call the model
        result = self.model.invoke(messages)
        content = result.content

        # For simplicity, we are parsing confidence from the text or mocking it.
        # Ideally we use structured output or function calling.
        # Here we will try to extract it or default to 0.8
        confidence = self._extract_confidence(content)

        # Clean content if needed (remove the JSON part if we want)

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
    def __init__(self, name: str, instructions: str, model: str, api_key: str):
        llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/jules/aiquorum", # Placeholder
                "X-Title": "AIQuorum"
            }
        )
        super().__init__(name, instructions, llm)
