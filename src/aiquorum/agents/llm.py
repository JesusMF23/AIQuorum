from typing import Tuple, Any, Optional
import os
from dotenv import load_dotenv
from aiquorum.agents.base import BaseAgent
from aiquorum.agents.base import BaseAgent
from aiquorum.types import AgentResponse, AgentContext
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables from .env file immediately
load_dotenv()

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

import random

CRITIQUE_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "{instructions}"),
    ("user", """Original Prompt: {original_prompt}

Peer Responses from previous step:
{history_text}

Task: Peer Review & Improvement
1. Analyze the perspectives and solutions provided by your peers above.
2. Identify strengths, weaknesses, and any missing angles in their responses.
3. Challenge their assumptions if necessary.
4. Synthesize their insights with your own expertise to provide a SUPERIOR answer.

Your goal is to reach the highest quality answer possible by standing on the shoulders of giants (or critiquing them).

Ends your response with a JSON object containing 'confidence' (float 0-1) field, like: {{"confidence": 0.9}}""")
])


class LLMAgent(BaseAgent):
    """
    A base agent that wraps a LangChain-compatible ChatModel.
    Useful if you want to bring your own model instance (e.g. strict OpenAI, Anthropic, local LLM).
    """
    def __init__(self, name: str, instructions: str, model: Any, monitor: bool = False):
        """
        :param name: Name of the agent.
        :param instructions: System prompt/persona.
        :param model: A LangChain ChatModel instance.
        :param monitor: Whether to log monitoring events for this agent.
        """
        super().__init__(name, instructions, monitor=monitor)
        self.model = model

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        # Retrieve original exception to check for rate limits if possible, 
        # but broadly retrying exceptions that likely transient is safe for now.
        retry=retry_if_exception_type(Exception)
    )
    def _invoke_model(self, prompt_value):
        return self.model.invoke(prompt_value)

    def process(self, context: AgentContext) -> AgentResponse:
        if context.current_step == 0:
            prompt_value = INITIAL_PROMPT_TEMPLATE.invoke({
                "instructions": self.instructions,
                "original_prompt": context.original_prompt
            })
        else:
            # Filter and shuffle peer responses to avoid positional bias
            # Council Logic: Exclude self from peer review
            last_step_num = context.current_step - 1
            last_step_responses = [
                r for r in context.previous_responses 
                if r.step_number == last_step_num and r.agent_name != self.name
            ]
            
            # Shuffle them
            random.shuffle(last_step_responses)
            
            history_text = "\n\n".join(
                [f"--- Peer Response ({r.agent_name}) ---\n{r.content}\n(Confidence: {r.confidence})"
                 for r in last_step_responses]
            )
            
            prompt_value = CRITIQUE_PROMPT_TEMPLATE.invoke({
                "instructions": self.instructions,
                "original_prompt": context.original_prompt,
                "history_text": history_text
            })

        # Call the model with retries
        result = self._invoke_model(prompt_value)
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
        import re
        # Regex explanation:
        # ["']?       : Optional opening quote
        # confidence  : Literal "confidence"
        # ["']?       : Optional closing quote
        # \s*[:=]\s*  : Separator (colon or equals), optional whitespace
        # (-?[0-9]*\.?[0-9]+) : Float capture group (handles optional negative for robustness)
        match = re.search(r'["\']?confidence["\']?\s*[:=]\s*(-?[0-9]*\.?[0-9]+)', text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                return max(0.0, min(1.0, val))
            except ValueError:
                pass
        return 0.5  # Default fallback


class Agent(LLMAgent):
    """
    The standard agent for AIQuorum.
    Connects to OpenRouter (default) or any OpenAI-compatible API to access a wide range of models.
    """
    def __init__(self, name: str, instructions: str, model: str, api_key: Optional[str] = None, monitor: bool = False):
        """
        :param name: Name of the agent (e.g., "Architect").
        :param instructions: The persona and instructions for the agent.
        :param model: The model identifier (e.g., 'openai/gpt-4-turbo').
        :param api_key: API Key. If None, checks OPENROUTER_API_KEY environment variable.
        :param monitor: Whether to log monitoring events for this agent.
        """
        # Ensure env vars are loaded (in case the user didn't import module at top level)
        load_dotenv()

        _api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not _api_key:
            raise ValueError(
                "API key missing. Please provide `api_key` argument or set `OPENROUTER_API_KEY` "
                "in your environment variables or .env file."
            )

        llm = ChatOpenAI(
            model=model,
            openai_api_key=_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            # default_headers={
            #     "HTTP-Referer": "https://github.com/jules/aiquorum", # Placeholder
            #     "X-Title": "AIQuorum"
            # }
        )
        super().__init__(name, instructions, llm, monitor=monitor)
