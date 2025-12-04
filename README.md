# AIQuorum

![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

> **⚠️ Vibe Code Alert**
>
> This project was 99% vibe coded as a fun Saturday hack because I wanted to explore and evaluate a number of LLMs side by side in the process of reading books together with LLMs. It's nice and useful to see multiple responses side by side, and also the cross-opinions of all LLMs on each other's outputs. I'm not going to support it in any way, it's provided here as is for other people's inspiration and I don't intend to improve it. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

**AIQuorum** is a Python framework for orchestrating a network of AI agents to iteratively solve problems, critique each other's work, and converge on high-confidence solutions. It is designed to work seamlessly with **OpenRouter** and **LangChain**.

## 🚀 Overview

The framework allows you to:
1.  **Configure Agents**: Define multiple agents with different personas, instructions, and underlying LLMs (via OpenRouter or LangChain).
2.  **Iterative Refinement**: Execute a workflow where agents not only answer but also review and improve upon previous iterations.
3.  **Confidence-Based Termination**: Automatically stop the workflow when a consensus or confidence threshold is met, or after a fixed number of steps.

## 📦 Installation

```bash
pip install aiquorum
```

*(Note: This package is currently in development and available from source).*

## 🛠️ Usage

### Configuration (OpenRouter)

AIQuorum is designed to be used with OpenRouter to access a wide variety of LLMs.

1.  Get an API key from [OpenRouter](https://openrouter.ai/).
2.  Set it as an environment variable:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Or use a `.env` file (ensure `python-dotenv` is installed and loaded).

### Basic Example

```python
import os
from aiquorum.agents.langchain_agent import OpenRouterAgent
from aiquorum.workflow.engine import Workflow

# Load env vars if using .env
# from dotenv import load_dotenv; load_dotenv()

# 1. Define your agents
# You can mix and match models easily.
agents = [
    OpenRouterAgent(
        name="Architect",
        instructions="Focus on structure and scalability. Be critical.",
        model="openai/gpt-4-turbo"
    ),
    OpenRouterAgent(
        name="Security Expert",
        instructions="Focus on security vulnerabilities. Be paranoid.",
        model="anthropic/claude-3-opus"
    )
]

# 2. Configure the workflow
# Run for up to 3 steps, or stop if confidence reaches 85%
workflow = Workflow(agents, max_steps=3, confidence_threshold=0.85)

# 3. Run with a prompt
# Step 0: Agents answer independently.
# Step 1+: Agents see previous answers, critique them, and improve.
result = workflow.run("Design a secure login system for a healthcare app.")

# 4. Inspect results
print(f"Final Answer by {result.history[-1].agent_name}:")
print(result.final_response)
print(f"Confidence: {result.final_confidence}")
print(f"Total Steps: {result.total_steps}")
```

## 🧩 Architecture & Flow

### Workflow Diagram

```mermaid
graph TD
    Start([User Prompt]) --> Step0[Step 0: Initial Answers]
    Step0 --> Eval{Confidence >= Threshold?}

    Eval -- Yes --> Finish([Return Result])
    Eval -- No --> LoopStart

    subgraph Iteration Loop
        LoopStart[Step N] --> Review[Agents Review History]
        Review --> Critique[Critique & Improve (Meta-Prompt)]
        Critique --> NewEval{Confidence >= Threshold?}
        NewEval -- No --> NextStep[Step N+1]
        NextStep --> LoopStart
    end

    NewEval -- Yes --> Finish
    NextStep -- Max Steps Reached --> Finish
```

### The Meta-Prompt
In Step 0, agents receive the user prompt directly.
In subsequent steps, **AIQuorum** automatically wraps the prompt in a "Meta-Prompt". This instructs the agent to:
1.  Read the history of previous responses (from themselves and other agents).
2.  Critique the strengths and weaknesses.
3.  Provide an improved answer.
4.  Rate their confidence in the new answer.

This logic is handled by `LangChainAgent` and `ChatPromptTemplate`.

## 📜 License

**Apache License 2.0**

This software is open source. You may use it for commercial and non-commercial purposes, provided you maintain attribution and include the original license.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---
Built with ❤️ by Jules.
