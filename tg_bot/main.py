import asyncio
import os
import subprocess

import tg_bot.messages as messages
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import database.database as db
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
from phi.knowledge import AssistantKnowledge
from phi.embedder.openai import OpenAIEmbedder
from phi.vectordb.pgvector import PgVector2
from phi.storage.assistant.postgres import PgAssistantStorage

load_dotenv()

TG_API_TOKEN = os.getenv('TG_API_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()
DB_URL = os.getenv('DB_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def setup() -> Assistant:
    llm = OpenAIChat(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    # Set up the Assistant with storage, knowledge base, and tools
    return Assistant(
        name="auto_rag_assistant",  # Name of the Assistant
        llm=llm,  # Language model to be used
        storage=PgAssistantStorage(table_name="auto_rag_storage", db_url=DB_URL),
        knowledge_base=AssistantKnowledge(
            vector_db=PgVector2(
                db_url=DB_URL,
                collection="auto_rag_docs",
                embedder=OpenAIEmbedder(model="text-embedding-ada-002", dimensions=1536, api_key=OPENAI_API_KEY),
            ),
            num_documents=3,
        ),
        instructions=[
            "Search your knowledge base first.",
            "If not found, print that the answer is not found.",
            "Provide clear, concise and very detailed answers.",
        ],
        show_tool_calls=True,
        search_knowledge=True,
        read_chat_history=True,
        markdown=True,
        debug_mode=True,
    )


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply(messages.START_MESSAGE)


@dp.message(Command('help'))
async def send_welcome(message: types.Message):
    await message.reply("Hi!")


@dp.message(Command('ping'))
async def send_response(message: types.Message):
    try:
        response = messages.CONNECTION_SUCCESSFUL
    except subprocess.CalledProcessError:
        response = messages.CONNECTION_FAILED

    await message.reply(response)


@dp.message()
async def ask(message: types.Message):
    user_question = message.text.strip()
    if user_question == '':
        await message.reply('No question provided!')
    else:
        answer = db.query_assistant(assistant, user_question)
        await message.reply(answer, parse_mode='Markdown')


assistant = setup()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
