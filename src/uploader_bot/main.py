import asyncio
import os
import zipfile
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from phi.document import Document

from src.data_processing.text_extractor import process_pdf, process_json
from src.database.database import add_documents
from phi.embedder.openai import OpenAIEmbedder
from phi.knowledge import AssistantKnowledge
from phi.vectordb.pgvector import PgVector2

from src.utils.translator import translate_text_with_openai

load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_ADMIN_BOT_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')
DB_URL = f"postgresql+psycopg2://{os.getenv('DB_NAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()
ALLOWED_USERS = os.getenv('ALLOWED_USERS').split(',')
ALLOWED_USERS = [int(user) for user in ALLOWED_USERS]

knowledge_base = AssistantKnowledge(
    vector_db=PgVector2(
        db_url=DB_URL,
        collection="auto_rag_docs",
        embedder=OpenAIEmbedder(model="text-embedding-ada-002", dimensions=1536, api_key=OPENAI_API_KEY),
    ),
    num_documents=3,
)


def check_user(user_id):
    return True
    # return user_id in ALLOWED_USERS


def add_user(user_id):
    if user_id not in ALLOWED_USERS:
        ALLOWED_USERS.append(user_id)


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    if not check_user(message.from_user.id):
        await message.reply("You are not allowed to use this bot.")
        return
    await message.reply("Welcome! Send file to upload it to database.")


async def upload_pdf(file_path, link=""):
    documents = await process_pdf(file_path)
    for i in range(len(documents)):
        documents[i].meta_data["link"] = link
        documents[i].content += f"\n\nSource: {link}"
    await add_documents(knowledge_base, documents)


async def upload_json(file_path, link=""):
    documents = await process_json(file_path)
    for i in range(len(documents)):
        documents[i].meta_data["link"] = link
        documents[i].content += f"\n\nSource: {link}"
    await add_documents(knowledge_base, documents)


@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    document = message.document
    link = ""
    if message.caption:
        link = message.caption.strip()

    file_id = document.file_id
    file_name = document.file_name

    file = await bot.get_file(file_id)
    file_path = file.file_path

    destination_file = os.path.join(DOWNLOAD_DIR, file_name)
    try:
        await asyncio.wait_for(bot.download_file(file_path, destination_file), timeout=120.0)
    except asyncio.TimeoutError:
        await message.reply("File download timed out. Please try again.")
        return

    if zipfile.is_zipfile(destination_file):
        with zipfile.ZipFile(destination_file, 'r') as zip_ref:
            zip_ref.extractall(DOWNLOAD_DIR)
        os.remove(destination_file)
        for root, _, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.pdf'):
                    await upload_pdf(file_path, link)
                elif file.endswith('.json'):
                    await upload_json(file_path, link)
        await message.reply("Zip archive uploaded and extracted successfully.")
    elif file_name.endswith('.pdf'):
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        await upload_pdf(file_path, link)
        await message.reply("File uploaded successfully.")
    elif file_name.endswith('.json'):
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        await upload_json(file_path, link)
        await message.reply("File uploaded successfully.")
    else:
        await message.reply("You can upload only zip archives, pdf and json files.")


@dp.message()
async def handle_message(message: types.Message):
    text = await translate_text_with_openai(message.text.strip())
    message_id = str(message.message_id)
    await add_documents(knowledge_base, [Document(
        name=message_id,
        id=f"message_{message_id}",
        content=text,
        meta_data={"chunk": 1}
    )])
    await message.reply("Message uploaded successfully.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot is running!')
    asyncio.run(main())
