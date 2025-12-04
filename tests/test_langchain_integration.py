from unittest.mock import MagicMock, patch
import pytest
import os
from aiquorum.agents.langchain_agent import LangChainAgent, OpenRouterAgent
from aiquorum.types import AgentContext, AgentResponse

def test_langchain_agent_step_0():
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Answer. confidence: 0.8"
    mock_llm.invoke.return_value = mock_response

    agent = LangChainAgent("Test", "Inst", mock_llm)
    context = AgentContext(original_prompt="Hi", current_step=0)

    agent.process(context)

    # Verify invoke called with prompt value (which comes from template)
    # We can check that invoke was called
    mock_llm.invoke.assert_called_once()
    # If we want to check the prompt content deeply, we'd need to inspect the call args
    call_args = mock_llm.invoke.call_args
    prompt_value = call_args[0][0]
    # Check that it contains the user prompt
    messages = prompt_value.to_messages()
    assert messages[0].content == "Inst"
    assert "Hi" in messages[1].content

def test_langchain_agent_step_N():
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Better. confidence: 0.9"
    mock_llm.invoke.return_value = mock_response

    agent = LangChainAgent("Test", "Inst", mock_llm)
    prev_resp = AgentResponse(content="Bad", confidence=0.1, agent_name="Other", step_number=0)
    context = AgentContext(original_prompt="Hi", current_step=1, previous_responses=[prev_resp])

    agent.process(context)

    call_args = mock_llm.invoke.call_args
    prompt_value = call_args[0][0]
    messages = prompt_value.to_messages()

    # Check that the history is in the user message
    user_msg = messages[1].content
    assert "Original Prompt: Hi" in user_msg
    assert "Step 0 - Other: Bad" in user_msg
    assert "Task: Review the previous answers" in user_msg

def test_openrouter_agent_env_var():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-env-key"}):
        # We need to mock ChatOpenAI so it doesn't actually try to validate connection
        with patch("aiquorum.agents.langchain_agent.ChatOpenAI") as MockChat:
            agent = OpenRouterAgent("OR", "Inst", "model")
            MockChat.assert_called_with(
                model="model",
                openai_api_key="sk-env-key",
                openai_api_base="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://github.com/jules/aiquorum", "X-Title": "AIQuorum"}
            )

def test_openrouter_agent_missing_key():
    with patch.dict(os.environ, {}, clear=True):
         with pytest.raises(ValueError, match="OpenRouter API key"):
             OpenRouterAgent("OR", "Inst", "model")
