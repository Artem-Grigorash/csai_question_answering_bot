import asyncio
import os
import subprocess

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from phi.assistant import Assistant
from phi.embedder.openai import OpenAIEmbedder
from phi.knowledge import AssistantKnowledge
from phi.llm.openai import OpenAIChat
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.vectordb.pgvector import PgVector2

import src.assistant_bot.messages as messages
from src.assistant_bot.feedback_db import init_db, save_rating, save_feedback, get_all_ratings, get_all_feedbacks, \
    clear_ratings, clear_feedbacks
from src.utils.translator import translate_text_with_openai

load_dotenv()

DB_URL = f"postgresql+psycopg2://{os.getenv('DB_NAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

TG_API_TOKEN = os.getenv('TG_API_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()

file_path = "feedback.txt"
last_question = ""
last_answer = ""
last_rate = 0

init_db()


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
            num_documents=4,
        ),
        description='An assistant for the CSAI (Computer Science and Artificial Intelligence) program at Neapolis University in Paphos, Cyprus',
        task='Answer questions related to the CSAI program at Neapolis University in Paphos, Cyprus',
        instructions=[
            "Always search the knowledge base first.",
            "First and foremost, interpret the question as being either related to the CSAI (Computer Science and Artificial Intelligence) program at Neapolis University or to the student life at this university in Paphos, Cyprus.",
            "Paphos Gardens is the place where students live.",
            "Provide the answer in telegram messenger format using emojis.",
            "Add link to the most important source which you used to find the answer.",
            "Provide clear, concise and very detailed answers.",
        ],
        show_tool_calls=False,
        search_knowledge=True,
        add_datetime_to_instructions=True,
        read_chat_history=True,
        debug_mode=True,
        prevent_hallucinations=True
    )


def query_assistant(assistant, question: str) -> str:
    return "".join([delta for delta in assistant.run(question)])


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


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


@dp.message()
async def ask(message: types.Message):
    global last_question, last_answer
    user_question = message.text.strip()
    if user_question == '':
        await message.reply(messages.NO_QUESTION)
    else:
        last_question = user_question
        answer = query_assistant(assistant, await translate_text_with_openai(user_question))
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
        await message.reply(answer, reply_markup=keyboard, parse_mode="Markdown")


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
        reply_markup=new_keyboard, parse_mode="Markdown"
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


assistant = setup()


#  Main

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
