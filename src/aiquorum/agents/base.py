import abc
from aiquorum.types import AgentContext, AgentResponse

class BaseAgent(abc.ABC):
    """
    Abstract base class for an agent in the quorum.
    """
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions

    @abc.abstractmethod
    def process(self, context: AgentContext) -> AgentResponse:
        """
        Process the input context and return a response.
        """
        pass

class MockAgent(BaseAgent):
    """
    A mock agent for testing purposes.
    Returns a predictable response and increases confidence with steps.
    """
    def process(self, context: AgentContext) -> AgentResponse:
        # Simulate improvement over steps
        step = context.current_step
        base_confidence = 0.5

        # Artificial logic: confidence increases by 0.1 each step, max 0.95
        confidence = min(0.95, base_confidence + (step * 0.1))

        if step == 0:
            content = f"[{self.name}] Initial answer to: {context.original_prompt}"
        else:
            # Review previous responses
            last_response = context.previous_responses[-1] if context.previous_responses else None
            prev_content = last_response.content if last_response else "None"
            content = f"[{self.name}] Critique of step {step-1}: '{prev_content}'. Improved answer."

        return AgentResponse(
            content=content,
            confidence=confidence,
            agent_name=self.name,
            step_number=step
        )
