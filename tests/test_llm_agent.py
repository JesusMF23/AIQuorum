from unittest.mock import MagicMock
from aiquorum.agents.llm import LLMAgent
from aiquorum.types import AgentContext, AgentResponse

def test_llm_agent_calls_invoke():
    # Mock the LLM
    mock_llm = MagicMock()
    # Mock response
    mock_response = MagicMock()
    mock_response.content = "Better answer. \"confidence\": 0.9"
    mock_llm.invoke.return_value = mock_response

    agent = LLMAgent("TestLC", "You are a test", mock_llm)

    context = AgentContext(
        original_prompt="Hello",
        current_step=0,
        previous_responses=[]
    )

    response = agent.process(context)

    assert response.content == "Better answer. \"confidence\": 0.9"
    assert response.confidence == 0.9
    assert response.agent_name == "TestLC"

    # Verify invoke was called
    mock_llm.invoke.assert_called_once()

def test_llm_agent_confidence_extraction():
    mock_llm = MagicMock()
    agent = LLMAgent("Test", "", mock_llm)

    # Test cases
    assert agent._extract_confidence('{"confidence": 0.85}') == 0.85
    assert agent._extract_confidence('confidence: 0.1') == 0.1
    assert agent._extract_confidence('No confidence here') == 0.5 # Default
    assert agent._extract_confidence('confidence: 1.5') == 1.0 # Clamped
    assert agent._extract_confidence('confidence: -0.5') == 0.0 # Clamped
