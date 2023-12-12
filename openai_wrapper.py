import sys
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio


# change as needed
MODEL = "gpt-4" # any GPT-3.5 or GPT-4 models
INSTRUCTIONS = "Provide key details only in bullet-point style. Give simple examples when asked."

# load environment variables from a .env file
# Make sure to have your OPENAI_API_KEY set
load_dotenv()

client = AsyncOpenAI()

async def add_message(thread_id, user_input):
    # add message to thread
    message = await client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=user_input)
    return message

async def get_answer(assistant_id, thread_id):
    # start a new run for the assistant to get an answer
    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # the trick that worked for me here was to check the run status every x seconds
    # poll every 2 seconds to check run completion
    while True:
        run_info = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run_info.completed_at:
            break

        if run_info.failed_at:
            sys.exit(f"Run failed. Error {run_info.last_error}")

        print("...", end="", flush=True)
        await asyncio.sleep(2)

    # retrieve then return assistant's answer
    messages = await client.beta.threads.messages.list(thread_id)
    content = messages.data[0].content[0].text.value
    return content


async def main():
    # create a new assistant and a new thread
    assistant = await client.beta.assistants.create(
        name="Ze Assistant",
        instructions=INSTRUCTIONS,
        model=MODEL,
        # tools=[{"type": "code_interpreter"}],
    )
    thread = await client.beta.threads.create()

    # loop to continuously prompt the user for input
    while True:
        user_input = input("=> ")
        if user_input == "q":
            break
        await add_message(thread.id, user_input)
        answer = await get_answer(assistant_id=assistant.id, thread_id=thread.id)
        print(f"\n💬:\n{answer}")

# run asynchronously
asyncio.run(main())
