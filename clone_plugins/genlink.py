# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import filters, Client, enums
from clone_plugins.users_api import get_user, get_short_link
from clone_plugins.dbusers import clonedb
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from Script import script
from clone_plugins.functions import is_subscribed, is_admin, encode, get_message_id, catch_errors
from pyrogram import enums
import base64

command_list = ['start', 'users', 'broadcast', 'batch', 'genlink', 'help', 'cmd', 'info', 'add_fsub', 'fsub_chnl', 'restart', 'del_fsub', 'add_admins', 'del_admins', 'admin_list', 'cancel', 'auto_del', 'forcesub', 'files', 'add_banuser', 'del_banuser', 'banuser_list', 'status', 'req_fsub']

@Client.on_message(~filters.command(command_list) & filters.private & is_admin)
async def channel_post(client: Client, message: Message):
        
    reply_text = await message.reply_text("<b><i>Pʀᴏᴄᴇssɪɴɢ....</i></b>", quote=True)
    try:
        post_message = await message.copy(chat_id=client.bot_details['db_channel'], disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.bot_details['db_channel'], disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("<b>Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ..!</b>")
        return
    converted_id = post_message.id * abs(client.bot_details['db_channel'])
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.bot_details['username']}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=f'https://telegram.me/share/url?url={link}')]])

    await reply_text.edit(f"<b>Bᴇʟᴏᴡ ɪs ʏᴏᴜʀ ʟɪɴᴋ::</b>\n<blockquote>{link}</blockquote>", reply_markup=reply_markup, disable_web_page_preview=True)

@Client.on_message(filters.command('batch') & filters.private & is_admin)
@catch_errors
async def batch(client: Client, message: Message):
    channel = f"<a href={client.db_channel.invite_link}>ᴅʙ ᴄʜᴀɴɴᴇʟ</a>" 
    while True:
        try:
            first_message = await client.ask(text=f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Fɪʀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel} (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..</blockquote>\n<blockquote>Oʀ Sᴇɴᴅ ᴛʜᴇ {channel} Pᴏsᴛ Lɪɴᴋ</blockquote></b>", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60, disable_web_page_preview=True)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply(f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs Fᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ᴏʀ ᴍᴇssᴀɢᴇ ʟɪɴᴋ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ {channel}</blockquote></b>", quote = True, disable_web_page_preview=True)
            continue

    while True:
        try:
            second_message = await client.ask(text =f"<b><blockquote>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Lᴀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ {channel} (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..</blockquote>\n<blockquote>Oʀ Sᴇɴᴅ ᴛʜᴇ {channel} Pᴏsᴛ Lɪɴᴋ</blockquote></b>", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60, disable_web_page_preview=True)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply(f"<b>❌ Eʀʀᴏʀ..\n<blockquote>Tʜɪs Fᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ᴏʀ ᴍᴇssᴀɢᴇ ʟɪɴᴋ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ {channel}</blockquote></b>", quote=True, reply_markup=reply_markup, disable_web_page_preview=True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.bot_details['username']}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Sʜᴀʀᴇ URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Bᴇʟᴏᴡ ɪs ʏᴏᴜʀ ʟɪɴᴋ:</b>\n<blockquote>{link}</blockquote>", quote=True, reply_markup=reply_markup, disable_web_page_preview=True)
