import asyncio
import os
import subprocess
import messages
import chromadb
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import database.database as db

load_dotenv()

COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")
THRESHOLD = 0

storage_path = os.getenv('STORAGE_PATH')
if storage_path is None:
    raise ValueError('STORAGE_PATH environment variable is not set')

client = chromadb.PersistentClient(path=storage_path)

collection = client.get_or_create_collection(name="csai")

TG_API_TOKEN = os.getenv('TG_API_TOKEN')
ANSWERING_HOST = os.getenv('ANSWERING_HOST')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')
RETRIEVER_URL = os.getenv("RETRIEVER_URL")
HTTP_TIMEOUT = 1200

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()


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


@dp.message(Command('ask'))
async def ask(message: types.Message):
    user_question = message.text[len('/ask'):].strip()
    if user_question == '':
        await message.reply('No question provided!')
    else:
        answer = await db.answer(user_question)
        await message.reply(answer)



@dp.message(Command('upload'))
async def upload_text(message: types.Message):
    text = message.text[len('/upload'):].strip()
    if text == '':
        await message.reply('No text provided!')
    else:
        await db.upload(text)
        await message.reply('Text uploaded!')


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
