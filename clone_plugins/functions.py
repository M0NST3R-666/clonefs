from config import ADMINS
import asyncio
from pyrogram.errors import UserNotParticipant
from pyrogram.enums import ChatMemberStatus
from pyrogram import filters
from clone_plugins.dbusers import clonedb
import base64
import re

async def is_subscribed(filter, client, update):
    me = await client.get_me()
    channel_ids = await clonedb.get_all_channels(me.id)
    if not channel_ids:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True

    for group_id in channel_ids:
        if not await check_each(client, group_id, user_id):
            return False

    return True

async def check_each(client, group_id, user_id):
    try:
        membership = await check_membership(client, group_id, user_id)
        if membership:
            return True
        return False
    except Exception as e:
        print(e)
        return False

async def check_membership(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ]:
            return True
        return False
    except UserNotParticipant:
        return False

async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id
        me = await client.get_me()    
        return any([user_id == ADMINS, await clonedb.admin_exist(me.id, user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False


subscribed = filters.create(is_subscribed)
is_admin = filters.create(check_admin)

async def encode(string):
    try:
        string_bytes = string.encode("ascii")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        base64_string = (base64_bytes.decode("ascii")).strip("=")
        return base64_string
    except Exception as e:
        print(f'Error occured on encode, reason: {e}')

async def decode(base64_string):
    try:
        base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
        base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
        string_bytes = base64.urlsafe_b64decode(base64_bytes) 
        string = string_bytes.decode("ascii")
        return string
    except Exception as e:
        print(f'Error occured on decode, reason: {e}')

async def get_messages(client, message_ids):
    try:
        messages = []
        total_messages = 0
        while total_messages != len(message_ids):
            temb_ids = message_ids[total_messages:total_messages+200]
            try:
                msgs = await client.get_messages(
                    chat_id=client.bot_details['db_channel'],
                    message_ids=temb_ids
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                msgs = await client.get_messages(
                    chat_id=client.bot_details['db_channel'],
                    message_ids=temb_ids
                )
            except:
                pass
            total_messages += len(temb_ids)
            messages.extend(msgs)
        return messages
    except Exception as e:
        print(f'Error occured on get_messages, reason: {e}')


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

from functools import wraps

def catch_errors(func):
    @wraps(func)
    async def wrapper(client, message):
        try:
            await func(client, message)
        except Exception as e:
            await message.reply_text(f"❌ <b>Something went wrong!</b>\n\n<code>{e}</code>")
    return wrapper
