import asyncio
import os
import subprocess

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from phi.assistant import Assistant
from phi.embedder.openai import OpenAIEmbedder
from phi.knowledge import AssistantKnowledge
from phi.llm.openai import OpenAIChat
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.vectordb.pgvector import PgVector2

from src.assistant_bot import messages
from src.utils.translator import translate_text_with_openai

load_dotenv()

TG_API_TOKEN = os.getenv('TG_API_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()
DB_URL = f"postgresql+psycopg2://{os.getenv('DB_NAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def setup() -> Assistant:
    llm = OpenAIChat(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    return Assistant(
        name="auto_rag_assistant",
        llm=llm,
        storage=PgAssistantStorage(table_name="auto_rag_storage", db_url=DB_URL),
        knowledge_base=AssistantKnowledge(
            vector_db=PgVector2(
                db_url=DB_URL,
                collection="auto_rag_docs",
                embedder=OpenAIEmbedder(model="text-embedding-ada-002", dimensions=1536, api_key=OPENAI_API_KEY),
            ),
            num_documents=5,
        ),
        description='You are assistant for the CSAI program at Neapolis University in Cyprus',
        instructions=[
            "Search your knowledge base first.",
            "First and foremost, interpret the question as being either related to the CSAI (Computer Science and Artificial Intelligence) program at Neapolis University or to the student life at this university in Cyprus.",
            "If you know the answer, provide it.",
            "If you don't know the answer, print 'The answer was not found'.",
            "Provide the answer in telegram format.",
            "Provide clear, concise and very detailed answers.",
        ],
        show_tool_calls=True,
        search_knowledge=True,
        read_chat_history=True,
        debug_mode=True,

    )


def query_assistant(assistant, question: str) -> str:
    return "".join([delta for delta in assistant.run(question)])


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
    user_question = await translate_text_with_openai(message.text.strip())
    if user_question == '':
        await message.reply('No question provided!')
    else:
        print(user_question)
        answer = query_assistant(assistant, user_question)
        await message.reply(answer, parse_mode="Markdown")


assistant = setup()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
