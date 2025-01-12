import asyncio
import os
import subprocess
import src.tg_bot.messages as messages
import chromadb
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from src.database import database as db
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from tg_bot.feedback_db import init_db, save_feedback, save_rating, clear_feedbacks, clear_ratings, get_all_ratings, \
    get_all_feedbacks

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
last_rate = 0

init_db()


#  User commands

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply(messages.START_MESSAGE)


@dp.message(Command('help'))
async def send_welcome(message: types.Message):
    await message.reply(messages.HELP_MESSAGE)


@dp.message(Command('ping'))
async def send_response(message: types.Message):
    try:
        response = messages.CONNECTION_SUCCESSFUL
    except subprocess.CalledProcessError:
        response = messages.CONNECTION_FAILED

    await message.reply(response)


@dp.message(Command('upload'))
async def upload_text(message: types.Message):
    text = message.text[len('/upload'):].strip()
    if text == '':
        await message.reply(messages.NO_TEXT)
    else:
        await db.upload(text)
        await message.reply(messages.TEXT_UPLOADED)


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


@dp.message(Command('ask'))
async def ask(message: types.Message):
    global last_question, last_answer
    user_question = message.text[len('/ask'):].strip()
    if user_question == '':
        await message.reply(messages.NO_QUESTION)
    else:
        last_question = user_question
        answer = await db.answer(user_question)
        last_answer = answer
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="😭", callback_data="1"),
                    InlineKeyboardButton(text="😢", callback_data="2"),
                    InlineKeyboardButton(text="😐", callback_data="3"),
                    InlineKeyboardButton(text="🙂", callback_data="4"),
                    InlineKeyboardButton(text="😃", callback_data="5")
                ]
            ]
        )
        await message.reply(answer, reply_markup=keyboard)


#  Feedback processing

@dp.callback_query(lambda c: c.data in ['1', '2', '3', '4', '5'])
async def callback_rating(query: types.CallbackQuery):
    global last_question, last_answer, last_rate

    rating = query.data
    emoji_map = {
        '1': '😭',
        '2': '😢',
        '3': '😐',
        '4': '🙂',
        '5': '😃'
    }

    last_rate = int(rating)
    save_rating(int(rating))

    new_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=messages.OPTION_FEEDBACK, callback_data="feedback"), ]])

    await query.message.edit_text(
        f"{query.message.text}\n\nYou rated this response as: {emoji_map[rating]}",
        reply_markup=new_keyboard
    )


@dp.callback_query(lambda c: c.data == 'feedback')
async def callback_feedback(query: types.CallbackQuery, state: FSMContext):
    await query.message.reply(messages.FEEDBACK_REQUEST)
    await state.set_state(FeedbackStates.waiting_for_feedback)


@dp.message(FeedbackStates.waiting_for_feedback)
async def handle_user_feedback(message: types.Message, state: FSMContext):
    user_feedback = message.text.strip()
    save_feedback(last_question, last_answer, user_feedback, last_rate)
    await message.reply(messages.AFTER_FEEDBACK)
    await state.clear()


#  Admin commands

@dp.message(Command('show_ratings'))
async def cmd_show_ratings(message: types.Message):
    ratings = get_all_ratings()
    if not ratings:
        await message.reply(messages.NO_RATINGS)
        return

    response_text = messages.ALL_RATINGS + "\n\n"
    for row in ratings:
        feedback_id, rating, created_at = row
        response_text += f"ID: {feedback_id} | Rating: {rating} | Date: {created_at}\n"
    await message.reply(response_text)


@dp.message(Command('show_feedbacks'))
async def cmd_show_feedbacks(message: types.Message):
    feedbacks = get_all_feedbacks()

    if not feedbacks:
        await message.reply(messages.NO_FEEDBACK)
        return

    response_text = messages.ALL_FEEDBACK + "\n\n"
    for fb in feedbacks:
        feedback_id = fb[0]
        user_question = fb[1]
        bot_answer = fb[2]
        user_feedback = fb[3]
        rating = fb[4]
        created_at = fb[5]

        response_text += (
            f"\n**Feedback ID:** {feedback_id}\n"
            f"\n**Question:** {user_question}\n"
            f"\n**Answer:** {bot_answer}\n"
            f"\n**User Feedback:** {user_feedback}\n"
            f"\n**Rating:** {rating}\n"
            f"\n**Date:** {created_at}\n"
            f"-----------------------------\n\n"
        )

    await message.reply(response_text, parse_mode="Markdown")


@dp.message(Command('clear_ratings'))
async def cmd_clear_ratings(message: types.Message):
    clear_ratings()
    await message.reply(messages.RATINGS_CLEANED)


@dp.message(Command('clear_feedbacks'))
async def cmd_clear_feedbacks(message: types.Message):
    clear_feedbacks()
    await message.reply(messages.FEEDBACK_CLEANED)

#  Main

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())