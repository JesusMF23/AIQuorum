from typing import List, Optional
import concurrent.futures
import logging
from pydantic import BaseModel
from aiquorum.agents.base import BaseAgent
from aiquorum.types import AgentResponse, AgentContext

logger = logging.getLogger(__name__)

class WorkflowResult(BaseModel):
    """
    Final result of the workflow.
    """
    final_response: str
    final_confidence: float
    history: List[AgentResponse]
    total_steps: int
    reason: str # Why it stopped (max steps or threshold)

class JudgeSpec(BaseModel):
    """
    Specification for a Judge agent.
    """
    agent: BaseAgent
    targets: List[str] # Names of agents to oversee

    model_config = {"arbitrary_types_allowed": True}

class Workflow:
    """
    Manages the agent network workflow.
    """
    def __init__(
        self,
        agents: List[BaseAgent],
        consolidator: BaseAgent,
        max_steps: int = 5,
        confidence_threshold: float = 0.9,
        judges: Optional[List[JudgeSpec]] = None,
        monitor: bool = False
    ):
        self.agents = agents
        self.consolidator = consolidator
        self.max_steps = max_steps
        self.confidence_threshold = confidence_threshold
        self.judges = judges or []
        self.monitor = monitor

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
        logger.info(f"Starting workflow with max_steps={self.max_steps}, defined_agents={len(self.agents)}")
        history: List[AgentResponse] = []
        current_step = 0

        while current_step < self.max_steps:
            if self.monitor:
                logger.info(f"Monitor: Step {current_step} triggered")
            else:
                logger.info(f"Processing Step {current_step}...")
            step_responses: List[AgentResponse] = []

            # Context for this step includes all previous history
            context = AgentContext(
                original_prompt=prompt,
                current_step=current_step,
                previous_responses=history
            )

            # Each agent processes the context
            # In a real async impl, this would be gathered. Here it is sequential.
            # Each agent processes the context in parallel
            # Each agent processes the context in parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_agent = {}
                for agent in self.agents:
                    # Logging: Who reviews whom
                    if current_step > 0 and (self.monitor or agent.monitor):
                        # Calculate peers (everyone else)
                        peers = [a.name for a in self.agents if a.name != agent.name]
                        logger.info(f"Monitor: Agent {agent.name} is reviewing peers: {peers}")
                    
                    future = executor.submit(agent.process, context.model_copy(deep=True))
                    future_to_agent[future] = agent

                for future in concurrent.futures.as_completed(future_to_agent):
                    agent = future_to_agent[future]
                    try:
                        logger.debug(f"Invoking agent {agent.name}...")
                        response = future.result()
                        step_responses.append(response)
                        
                        if self.monitor or agent.monitor:
                            logger.info(f"Monitor: response from agent {agent.name}: {response.content[:100]}..., confidence score of agent {agent.name}: {response.confidence}")
                        
                        logger.debug(f"Agent {agent.name} responded with confidence {response.confidence}")
                    except Exception as exc:
                        logger.error(f"Agent {agent.name} generated an exception: {exc}")

            # Run Judges (if any)
            if self.judges and step_responses:
                logger.debug("Invoking judges...")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_to_judge = {}
                    for j_spec in self.judges:
                        # Judge context: Only sees its targets' responses from THIS step
                        target_responses = [r for r in step_responses if r.agent_name in j_spec.targets]
                        if not target_responses:
                            continue
                        
                        judge_ctx = AgentContext(
                            original_prompt=prompt,
                            current_step=current_step,
                            previous_responses=target_responses # Judge specifically reviews these
                        )
                        
                        if self.monitor or j_spec.agent.monitor:
                             logger.info(f"Monitor: Judge {j_spec.agent.name} is reviewing targets: {j_spec.targets}")

                        future = executor.submit(j_spec.agent.process, judge_ctx)
                        future_to_judge[future] = j_spec.agent

                    for future in concurrent.futures.as_completed(future_to_judge):
                         judge = future_to_judge[future]
                         try:
                             resp = future.result()
                             # Mark as judgment?
                             resp.content = f"[JUDGMENT by {judge.name}] {resp.content}"
                             step_responses.append(resp)
                             if self.monitor or judge.monitor:
                                logger.info(f"Monitor: Judgment from {judge.name}: {resp.content[:100]}...")
                         except Exception as exc:
                             logger.error(f"Judge {judge.name} failed: {exc}")

            # Add step responses to history
            history.extend(step_responses)

            # Calculate confidence for this step
            avg_confidence = self.calculate_aggregated_confidence(step_responses)

            # Check threshold
            if avg_confidence >= self.confidence_threshold:
                logger.info(f"Confidence threshold met ({avg_confidence:.2f} >= {self.confidence_threshold}). Stopping early.")
                
                final_output = self._consolidate(prompt, history, step_responses)
                return WorkflowResult(
                    final_response=final_output.content if final_output else max(step_responses, key=lambda r: r.confidence).content,
                    final_confidence=avg_confidence,
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
        # Max steps reached
        final_output = self._consolidate(prompt, history, history[-len(self.agents):])

        return WorkflowResult(
            final_response=final_output.content if final_output else max(history[-len(self.agents):], key=lambda r: r.confidence).content,
            final_confidence=self.calculate_aggregated_confidence(history[-len(self.agents):]),
            history=history,
            total_steps=current_step,
            reason="Max steps reached"
        )

    def _consolidate(self, prompt: str, history: List[AgentResponse], last_step_responses: List[AgentResponse]) -> Optional[AgentResponse]:
        """
        Runs the consolidator agent.
        """
        # Consolidator is mandatory now
        logger.info("Running consolidation step...")
        context = AgentContext(
            original_prompt=prompt,
            current_step=999, # Special step for consolidation
            previous_responses=history # Consolidator sees full history
        )
        try:
            return self.consolidator.process(context)
        except Exception as exc:
            logger.error(f"Consolidator generated an exception: {exc}")
            return None
