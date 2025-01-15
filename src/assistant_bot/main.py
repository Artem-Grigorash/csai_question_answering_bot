import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatType
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
from src.utils.authenticator import check_user
import src.assistant_bot.messages as messages
from src.assistant_bot.feedback_db import init_db, save_rating, save_feedback
from src.utils.translator import translate_text_with_openai

load_dotenv()

DB_URL = f"postgresql+psycopg2://{os.getenv('DB_NAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

TG_API_TOKEN = os.getenv('TG_API_TOKEN')

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
    if message.chat.type != ChatType.PRIVATE:
        return
    await message.reply(messages.START_MESSAGE)


@dp.message(Command('help'))
async def send_welcome(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    await message.reply(messages.HELP_MESSAGE)


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()


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
    await query.message.edit_text(query.message.text, reply_markup=None, parse_mode="Markdown")
    await query.answer()
    await query.message.reply(messages.FEEDBACK_REQUEST)
    await state.set_state(FeedbackStates.waiting_for_feedback)


@dp.message(FeedbackStates.waiting_for_feedback)
async def handle_user_feedback(message: types.Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return
    user_feedback = message.text.strip()
    save_feedback(last_question, last_answer, user_feedback, last_rate)
    await message.reply(messages.AFTER_FEEDBACK)
    await state.clear()


@dp.message()
async def ask(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    global last_question, last_answer

    user_id = message.from_user.id
    check = await check_user(bot, user_id)
    if not check["status"]:
        await message.reply(check["message"])
        return

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


assistant = setup()


#  Main

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
