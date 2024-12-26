import asyncio
import os
import zipfile

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

from data_processing.text_extractor import get_text
from database.database import upload

load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_ADMIN_BOT_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()
ALLOWED_USERS = os.getenv('ALLOWED_USERS').split(',')
ALLOWED_USERS = [int(user) for user in ALLOWED_USERS]


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


@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    document = message.document

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
                    await upload(await get_text(file_path), file_path)
        await message.reply("Zip archive uploaded and extracted successfully.")
    else:
        if file_name.endswith('.pdf'):
            await upload(await get_text(destination_file), file_path)
            await message.reply("File uploaded successfully.")
        else:
            await message.reply("You can upload only zip archives or pdf files.")


@dp.message(Command('show'))
async def list_files(message: types.Message):
    if not check_user(message.from_user.id):
        await message.reply("You are not allowed to use this bot.")
        return

    file_list = []
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        for name in dirs:
            file_list.append(os.path.relpath(os.path.join(root, name), DOWNLOAD_DIR) + "\\")
        for name in files:
            file_list.append(os.path.relpath(os.path.join(root, name), DOWNLOAD_DIR))

    if not file_list:
        await message.reply("No files uploaded yet.")
    else:
        file_list_str = "\n".join(f"📁 {file}" if file.endswith('\\') else f"📄 {file}" for file in file_list)
        await message.reply(f"Uploaded files:\n\n{file_list_str}")


@dp.message(Command('delete_file'))
async def delete_file(message: types.Message):
    if not check_user(message.from_user.id):
        await message.reply("You are not allowed to use this bot.")
        return

    command_args = message.text.split(maxsplit=1)
    if len(command_args) > 1:
        file_name = command_args[1]
    else:
        await message.reply("Please specify the file name to delete.")
        return

    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        await message.reply(f"File '{file_name}' deleted successfully.")
    else:
        await message.reply(f"File '{file_name}' not found.")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
