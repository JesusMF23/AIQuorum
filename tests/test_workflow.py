import pytest
from aiquorum.agents.base import MockAgent
from aiquorum.workflow.engine import Workflow

def test_workflow_steps():
    agents = [
        MockAgent("Agent A", "Be critical"),
        MockAgent("Agent B", "Be creative")
    ]
    # Threshold 1.0 ensures it runs all steps (since mock caps at 0.95)
    workflow = Workflow(agents, max_steps=3, confidence_threshold=1.0)
    result = workflow.run("Explain quantum physics.")

    assert result.total_steps == 3
    assert result.reason == "Max steps reached"
    assert len(result.history) == 6 # 2 agents * 3 steps

def test_workflow_threshold_early_stop():
    agents = [
        MockAgent("Agent A", "Be critical"),
        MockAgent("Agent B", "Be creative")
    ]
    # Mock starts at 0.5 and increases by 0.1 per step.
    # Step 0: 0.5
    # Step 1: 0.6
    # Set threshold to 0.6.

    workflow = Workflow(agents, max_steps=5, confidence_threshold=0.6)
    result = workflow.run("Explain quantum physics.")

    # Step 0: Avg 0.5 < 0.6. Continue.
    # Step 1: Avg 0.6 >= 0.6. Stop.
    # So total steps should be 2.

    assert result.total_steps == 2
    assert result.reason == "Confidence threshold met"
    assert result.final_confidence >= 0.6

def test_workflow_step_content():
    agents = [MockAgent("Agent A", "")]
    workflow = Workflow(agents, max_steps=2, confidence_threshold=1.0)
    result = workflow.run("Test Prompt")

    # Check step 0 content
    assert "Initial answer" in result.history[0].content
    # Check step 1 content
    assert "Critique of step 0" in result.history[1].content
