from typing import List, Optional
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """
    Structured response from an agent.
    """
    content: str = Field(..., description="The textual response or critique provided by the agent.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    agent_name: str = Field(..., description="Name of the agent who produced this response.")
    step_number: int = Field(..., description="The step number in the workflow this response belongs to.")

class AgentContext(BaseModel):
    """
    Context passed to an agent during the workflow.
    """
    original_prompt: str
    current_step: int
    previous_responses: List[AgentResponse] = []
