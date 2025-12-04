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

### Basic Example

```python
from aiquorum.agents.base import MockAgent
from aiquorum.workflow.engine import Workflow

# 1. Define your agents
agents = [
    MockAgent("Architect", "Focus on structure and scalability."),
    MockAgent("Reviewer", "Critique for security and performance flaws.")
]

# 2. Configure the workflow
# Run for up to 5 steps, or stop if confidence reaches 90%
workflow = Workflow(agents, max_steps=5, confidence_threshold=0.9)

# 3. Run with a prompt
result = workflow.run("Design a microservices architecture for a banking app.")

# 4. Inspect results
print(f"Final Answer: {result.final_response}")
print(f"Confidence: {result.final_confidence}")
print(f"Total Steps: {result.total_steps}")
```

### Using OpenRouter

```python
from aiquorum.agents.langchain_agent import OpenRouterAgent

agent = OpenRouterAgent(
    name="Expert",
    instructions="You are a helpful assistant.",
    model="openai/gpt-4-turbo",
    api_key="sk-or-..."
)
```

## 🧩 Architecture

```mermaid
graph TD
    Start([User Prompt]) --> Step0[Step 0: Initial Answers]
    Step0 --> Eval{Confidence >= Threshold?}

    Eval -- Yes --> Finish([Return Result])
    Eval -- No --> LoopStart

    subgraph Iteration Loop
        LoopStart[Step N] --> Review[Agents Review History]
        Review --> Critique[Critique & Improve]
        Critique --> NewEval{Confidence >= Threshold?}
        NewEval -- No --> NextStep[Step N+1]
        NextStep --> LoopStart
    end

    NewEval -- Yes --> Finish
    NextStep -- Max Steps Reached --> Finish
```

The core components are:

*   **`Agent`**: Wraps an LLM with specific instructions. It receives the workflow history and produces a structured response (Content + Confidence).
*   **`Workflow`**: Manages the loop. It passes the context (previous answers) to agents and aggregates their confidence scores.

## 📜 License

**Apache License 2.0**

This software is open source. You may use it for commercial and non-commercial purposes, provided you maintain attribution and include the original license.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---
Built with ❤️ by Jules.
