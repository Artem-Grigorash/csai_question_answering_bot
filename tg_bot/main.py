import asyncio
import os
import subprocess
import tg_bot.messages as messages
import chromadb
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from database import database as db
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

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

file_path = "feedback.txt"
last_question = ""
last_answer = ""


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


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


@dp.message(Command('ask'))
async def ask(message: types.Message):
    global last_question, last_answer
    user_question = message.text[len('/ask'):].strip()
    if user_question == '':
        await message.reply('No question provided!')
    else:
        last_question = user_question
        answer = await db.answer(user_question)
        last_answer = answer
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👍 Like", callback_data="like"),
                    InlineKeyboardButton(text="👎 Dislike", callback_data="dislike"),
                ]
            ]
        )
        await message.reply(answer, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == 'like')
async def callback_like(query: types.CallbackQuery):
    await query.message.edit_text(f"{query.message.text}\n\nYou rated this response as: 👍 Like")


@dp.callback_query(lambda c: c.data == 'dislike')
async def callback_dislike(query: types.CallbackQuery):
    new_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Provide Feedback", callback_data="feedback"),
            ]
        ]
    )
    await query.message.edit_text(
        f"{query.message.text}\n\nYou rated this response as: 👎 Dislike",
        reply_markup=new_keyboard
    )


@dp.callback_query(lambda c: c.data == 'feedback')
async def callback_feedback(query: types.CallbackQuery, state: FSMContext):
    await query.message.reply(
        "We value your feedback. Please provide it as a separate message, and we will take it into account.")
    await state.set_state(FeedbackStates.waiting_for_feedback)


@dp.message(FeedbackStates.waiting_for_feedback)
async def handle_user_feedback(message: types.Message, state: FSMContext):
    user_feedback = message.text.strip()
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"--User question--\n\n{last_question}\n\n--Bot answer--\n\n{last_answer}\n\n--User feedback--\n\n{user_feedback}")
    await message.reply("Thank you for your feedback! We will definitely take it into account.")
    await state.clear()


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
