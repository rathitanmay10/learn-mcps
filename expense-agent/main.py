import asyncio

from agent import agent


async def main():
    print("Expense Agent ready. Type 'quit' to exit.\n")
    history = []
    loop = asyncio.get_event_loop()

    async with agent:
        while True:
            user_input = (await loop.run_in_executor(None, input, "You: ")).strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                break

            try:
                result = await agent.run(user_input, message_history=history)
                history = result.all_messages()
                print(f"Agent: {result.output}\n")
            except Exception as e:
                print(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
