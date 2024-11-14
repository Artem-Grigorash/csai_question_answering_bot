import asyncio
import os
import subprocess

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

import messages

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


@dp.message(Command('ask'))
async def ask(message: types.Message):
    user_question = message.text[len('/ask'):].strip()
    if user_question == '':
        await message.reply('No question provided!')
    else:
        host = os.path.join(ANSWERING_HOST, 'ask')
        query_params = {
            'query': user_question,
            'num': 5,
        }
        response = httpx.get(host, params=query_params, timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            await message.reply("Something went wrong")
        else:
            await message.reply(response.json()['response']['content'])


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
