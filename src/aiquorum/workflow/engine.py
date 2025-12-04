from typing import List, Optional
from pydantic import BaseModel
from aiquorum.types import AgentResponse, AgentContext
from aiquorum.agents.base import BaseAgent

class WorkflowResult(BaseModel):
    """
    Final result of the workflow.
    """
    final_response: str
    final_confidence: float
    history: List[AgentResponse]
    total_steps: int
    reason: str # Why it stopped (max steps or threshold)

class Workflow:
    """
    Manages the agent network workflow.
    """
    def __init__(
        self,
        agents: List[BaseAgent],
        max_steps: int = 5,
        confidence_threshold: float = 0.9
    ):
        self.agents = agents
        self.max_steps = max_steps
        self.confidence_threshold = confidence_threshold

    def calculate_aggregated_confidence(self, responses: List[AgentResponse]) -> float:
        """
        Calculates the aggregated confidence from a list of responses.
        Currently uses a simple average.
        """
        if not responses:
            return 0.0
        total = sum(r.confidence for r in responses)
        return total / len(responses)

    def run(self, prompt: str) -> WorkflowResult:
        """
        Executes the workflow.
        """
        history: List[AgentResponse] = []
        current_step = 0

        while current_step < self.max_steps:
            step_responses: List[AgentResponse] = []

            # Context for this step includes all previous history
            context = AgentContext(
                original_prompt=prompt,
                current_step=current_step,
                previous_responses=history
            )

            # Each agent processes the context
            # In a real async impl, this would be gathered. Here it is sequential.
            for agent in self.agents:
                response = agent.process(context)
                step_responses.append(response)

            # Add step responses to history
            history.extend(step_responses)

            # Calculate confidence for this step
            avg_confidence = self.calculate_aggregated_confidence(step_responses)

            # Check threshold
            if avg_confidence >= self.confidence_threshold:
                # Find the best response in this step to return
                best_response = max(step_responses, key=lambda r: r.confidence)
                return WorkflowResult(
                    final_response=best_response.content,
                    final_confidence=best_response.confidence, # Or avg_confidence? User said "trust for the answer... calculated considering all".
                                                               # I will return the best individual text but the confidence that triggered the stop.
                    history=history,
                    total_steps=current_step + 1,
                    reason="Confidence threshold met"
                )

            current_step += 1

        if not history:
             return WorkflowResult(
                final_response="No execution performed.",
                final_confidence=0.0,
                history=[],
                total_steps=0,
                reason="No steps executed"
            )

        # Get the responses from the very last iteration
        # The history list has all of them. We want the last len(agents) ones.
        last_step_responses = history[-len(self.agents):]
        best_response = max(last_step_responses, key=lambda r: r.confidence)

        return WorkflowResult(
            final_response=best_response.content,
            final_confidence=best_response.confidence,
            history=history,
            total_steps=current_step,
            reason="Max steps reached"
        )
