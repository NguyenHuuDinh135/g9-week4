"""CLI entry point for the GeekBrain AI Q&A system."""

import sys

from src.agent import Agent


def main():
    print("=" * 60)
    print("  GeekBrain AI Q&A System")
    print("  Type 'quit' to exit, 'clear' to reset memory")
    print("=" * 60)
    print()

    agent = Agent()

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        if query.lower() == "clear":
            agent.reset_memory()
            print("Memory cleared.\n")
            continue

        try:
            result = agent.answer(query)
            if result.get("trace"):
                print("\n--- Trace ---")
                for step in result["trace"]:
                    print(f"  [{step['step']}] {step['data']}")
                print("--- End Trace ---")
            print(f"\nAssistant: {result['response']}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
