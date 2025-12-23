import os
import sys
import logging
from dotenv import load_dotenv

# Ensure we can import the package if running from root without install
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from aiquorum.agents.llm import Agent
from aiquorum.workflow.engine import Workflow

def main():
    # Configure logging to show steps in console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    print("Welcome to AIQuorum Demo!")
    
    # Load .env file
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables or .env file.")
        print("Please create a .env file with your API key to run this demo.")
        return

    print("Initializing agents...")

    # Create real agents
    agents = [
        Agent(
            name="Architect", 
            instructions="You are a software architect. Focus on high-level design, patterns, and scalability.",
            model="openai/gpt-3.5-turbo" # Cost-effective default
        ),
        Agent(
            name="Reviewer", 
            instructions="You are a code reviewer. Focus on potential bugs, security issues, and pythonic best practices.",
            model="openai/gpt-3.5-turbo"
        )
    ]

    # Initialize workflow
    print("Setting up workflow...")
    workflow = Workflow(agents, max_steps=3, confidence_threshold=0.85)

    # Run workflow
    original_prompt = "Design a Python class for a thread-safe Singleton pattern."
    print(f"\nRunning workflow on prompt: '{original_prompt}'")
    print("This may take a moment as we call the LLMs...")
    
    try:
        result = workflow.run(original_prompt)

        # Display results
        print("\n--- Workflow Finished ---")
        print(f"Total Steps: {result.total_steps}")
        print(f"Reason for stop: {result.reason}")
        print(f"Final Confidence: {result.final_confidence}")
        print("\nStep History:")
        for response in result.history:
            print(f"\n[Step {response.step_number}] {response.agent_name} (Conf: {response.confidence:.2f}):")
            print("-" * 40)
            # Truncate content for display if too long
            preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
            print(preview)
            print("-" * 40)
            
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()
