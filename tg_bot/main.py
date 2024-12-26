import asyncio
import os
import subprocess

from aiogram.types import InputMediaDocument, InputFile

import tg_bot.messages as messages
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import database.database as db
from aiogram.types import FSInputFile


load_dotenv()

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


@dp.message()
async def ask(message: types.Message):
    user_question = message.text.strip()
    if user_question == '':
        await message.reply('No question provided!')
    else:
        answer, document_paths = await db.answer(user_question)
        media = []
        for i, document_path in enumerate(document_paths):
            file = FSInputFile(document_path)
            media.append(InputMediaDocument(media=file))
        if media:
            await message.reply(answer, parse_mode='Markdown')
            await message.reply_media_group(media)
        else:
            await message.reply(answer, parse_mode='Markdown')


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
