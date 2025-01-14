import time
from aiogram.enums import ChatMemberStatus
from dotenv import load_dotenv
import os

load_dotenv()

LIFE_CS_CHAT_ID = os.getenv('LIFE_CS_CHAT_ID')
MESSAGE_LIMIT = 10  # Max number of messages allowed
TIME_LIMIT = 3600  # Time limit in seconds
# Format: {user_id: {"count": count of messages, "first_message_time": time of first message}}
user_message_data = {}


async def check_user_in_chat(bot, chat_id: str, user_id: int) -> bool:
    """
    Check if user is in chat
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        # Return True if user is a chat member, admin or creator
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception:
        return False  # Return False if user is not a chat member


async def check_message_limit(user_id: int) -> bool:
    """
    Check if user has reached message limit
    """
    if user_id in user_message_data:
        user_data = user_message_data[user_id]
        if user_data["count"] >= MESSAGE_LIMIT:
            if time.time() - user_data["first_message_time"] < TIME_LIMIT:
                return False
            else:
                user_message_data[user_id] = {"count": 1, "first_message_time": time.time()}
        else:
            user_message_data[user_id]["count"] += 1
    else:
        user_message_data[user_id] = {"count": 1, "first_message_time": time.time()}
    return True


async def check_user(bot, user_id: int) -> dict:
    """
    Check if user is in chat and has not reached message limit
    """
    is_member = await check_user_in_chat(bot, LIFE_CS_CHAT_ID, user_id)
    if not is_member:
        return {"status": False, "message": "Sorry, only NUP ACS and CSAI students are allowed to chat here."}
    if not await check_message_limit(user_id):
        return {"status": False, "message": "You have reached the message limit. Please try again later."}
    return {"status": True}
