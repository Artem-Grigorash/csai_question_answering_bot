import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_ADMIN_BOT_TOKEN')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher()
ALLOWED_USERS = [414450175]


def check_user(user_id):
    return user_id in ALLOWED_USERS

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
    await bot.download_file(file_path, destination_file)
    await message.reply("File uploaded successfully.")


@dp.message(Command('show'))
async def list_files(message: types.Message):
    if not check_user(message.from_user.id):
        await message.reply("You are not allowed to use this bot.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.reply("No files uploaded yet.")
    else:
        file_list = "\n".join(files)
        await message.reply(f"Uploaded files:\n{file_list}")

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
