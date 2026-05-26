import asyncio
from dotenv import load_dotenv
from agent import agent

load_dotenv()


async def main():
    print("Expense Agent ready. Type 'quit' to exit.\n")
    history = []

    async with agent:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                break

            result = await agent.run(user_input, message_history=history)
            history = result.all_messages()
            print(f"Agent: {result.output}\n")


if __name__ == "__main__":
    asyncio.run(main())
