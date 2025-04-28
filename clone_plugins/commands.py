import os
import logging
import random
import asyncio
from Script import script
from validators import domain
from clone_plugins.dbusers import clonedb
from clone_plugins.users_api import get_user, update_user_info
from pyrogram import Client, filters, enums
from plugins.clone import mongo_db
from pyrogram.errors import ChatAdminRequired, FloodWait
from config import BOT_USERNAME, ADMINS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto
from config import PICS, CUSTOM_FILE_CAPTION, AUTO_DELETE_TIME, AUTO_DELETE, FORCE_MSG
import re
import json
import base64
from clone_plugins.functions import subscribed, is_subscribed, check_membership
import asyncio
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from pyrogram.errors import ChatInvalid, UserInvalid, FloodWait
from clone_plugins.functions import is_admin, get_messages, decode
from config import ADMINS
from clone_plugins.dbusers import clonedb
logger = logging.getLogger(__name__)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

@Client.on_message(filters.command("start") & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    user_id = message.from_user.id

    if not await clonedb.is_user_exist(bot_id, user_id):
        await clonedb.add_user(bot_id, user_id)

    text = message.text.strip()

    if len(text.split()) > 1:  # Deep-linked start command
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            argument = string.split("-")
        except Exception as e:
            logger.error(f"Error decoding base64 string: {e}")
            return await message.reply("<b><i>Something went wrong..!</i></b>")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.bot_details['db_channel']))
                end = int(int(argument[2]) / abs(client.bot_details['db_channel']))
                ids = list(range(start, end + 1)) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                logger.error(f"Error processing range arguments: {e}")
                return await message.reply("<b><i>Invalid range arguments..!</i></b>")
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.bot_details['db_channel']))]
            except Exception as e:
                logger.error(f"Error processing single ID argument: {e}")
                return await message.reply("<b><i>Invalid ID argument..!</i></b>")
        else:
            logger.error("Invalid argument format")
            return await message.reply("<b><i>Invalid argument format..!</i></b>")

        await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)

        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return await message.reply("<b><i>Something went wrong while fetching messages..!</i></b>")

        for msg in messages:
            caption = ""
            if msg.document and CUSTOM_FILE_CAPTION:
                caption = CUSTOM_FILE_CAPTION.format(
                    file_name=msg.document.file_name or "",
                    file_size=get_size(msg.document.file_size) or "",
                    file_caption=msg.caption.html if msg.caption else ""
                )
            elif msg.caption:
                caption = msg.caption.html

            reply_markup = None

            try:
                await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=True
                )
                await asyncio.sleep(0.1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=True
                )
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error copying message: {e}")

        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    else:  # Basic /start command
        me = await client.get_me()
        buttons = [
            [
                InlineKeyboardButton('💝 Subscribe My YouTube Channel', url='https://youtube.com/@Tech_VJ')
            ],
            [
                InlineKeyboardButton('🤖 Create Your Own Clone Bot', url=f'https://t.me/{BOT_USERNAME}?start=clone')
            ],
            [
                InlineKeyboardButton('💁‍♀️ Help', callback_data='help'),
                InlineKeyboardButton('About 🔻', callback_data='about')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        try:
            await message.reply_photo(
                photo=random.choice(PICS),
                caption=script.CLONE_START_TXT.format(message.from_user.mention, me.mention),
                reply_markup=reply_markup
            )
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        except Exception as e:
            logger.error(f"Error sending basic /start response: {e}")
            await message.reply("<b><i>Something went wrong while sending the welcome message..!</i></b>")

@Client.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    user_id = message.from_user.id
    buttons = []
    channel_ids = await clonedb.get_all_channels(bot_id)
    try:
        for channel_id in channel_ids:
            if not await check_membership(client, channel_id, user_id):
                ButtonUrl = client.invite_links[channel_id]
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Join Channel",
                        url=ButtonUrl
                    )
                ])
        
        try:
            buttons.append([InlineKeyboardButton(
                text='♻️ Tʀʏ Aɢᴀɪɴ',
                url=f"https://t.me/{client.bot_details['username']}?start={message.command[1] if len(message.command) > 1 else ''}"
            )])
        except IndexError:
            pass
        
        await message.reply(
            text=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True,
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@Client.on_message(filters.command('api') & filters.private)
async def shortener_api_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command

    if len(cmd) == 1:
        s = script.SHORTENER_API_MESSAGE.format(base_site=user["base_site"], shortener_api=user["shortener_api"])
        return await m.reply(s)

    elif len(cmd) == 2:    
        api = cmd[1].strip()
        await update_user_info(user_id, {"shortener_api": api})
        await m.reply("Shortener API updated successfully to " + api)
    else:
        await m.reply("You are not authorized to use this command.")

@Client.on_message(filters.command("base_site") & filters.private)
async def base_site_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command
    text = f"/base_site (base_site)\n\nCurrent base site: None\n\n EX: /base_site shortnerdomain.com\n\nIf You Want To Remove Base Site Then Copy This And Send To Bot - `/base_site None`"
    
    if len(cmd) == 1:
        return await m.reply(text=text, disable_web_page_preview=True)
    elif len(cmd) == 2:
        base_site = cmd[1].strip()
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("Base Site updated successfully")
    else:
        await m.reply("You are not authorized to use this command.")

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    bot_id = client.bot_details['bot_id']
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
            ],[
            InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', url=f'https://t.me/{BOT_USERNAME}?start=clone')
            ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('ᴀʙᴏᴜᴛ 🔻', callback_data='about')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.CLONE_START_TXT.format(query.from_user.mention, f"@{client.bot_details['username']}"),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CHELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )  

    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        owner = mongo_db.bots.find_one({'bot_id': bot_id})
        ownerid = int(owner['user_id'])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CABOUT_TXT.format(f"@{client.bot_details['username']}", ownerid),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )  

@Client.on_message(filters.command('add_fsub') & filters.private & is_admin)
async def add_forcesub(client: Client, message: Message):
    pro = await message.reply("<b><i>Processing...</i></b>", quote=True)
    bot_id = client.bot_details['bot_id']
    channel_ids = await clonedb.get_all_channels(bot_id)
    fsubs = message.text.split()[1:]
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])

    if not fsubs:
        await pro.edit(
            "<b>You need to add channel IDs\n<blockquote><u>EXAMPLE</u>:\n/add_fsub [channel_ids] :</b> You can add one or multiple channel IDs at a time.</blockquote>",
            reply_markup=reply_markup
        )
        return

    channel_list = ""
    check = 0

    for id in fsubs:
        try:
            id = int(id)
        except ValueError:
            channel_list += f"<b><blockquote>Invalid ID: <code>{id}</code></blockquote></b>\n\n"
            continue

        if id in channel_ids:
            channel_list += f"<b><blockquote>ID: <code>{id}</code>, already exists.</blockquote></b>\n\n"
            continue

        id_str = str(id)
        
        if id_str.startswith('-') and id_str[1:].isdigit() and len(id_str) == 14:
            try:
                data = await client.get_chat(id)
                link = data.invite_link or await client.export_chat_invite_link(id)
                cname = data.title

                channel_list += f"<b><blockquote>NAME: <a href='{link}'>{cname}</a> (ID: <code>{id}</code>)</blockquote></b>\n\n"
                check += 1
            except (ChatInvalid, FloodWait) as e:
                channel_list += f"<b><blockquote>ID: <code>{id}</code>\n<i>Unable to add force-sub, check the channel ID or bot permissions.</i></blockquote></b>\n\n"
        else:
            channel_list += f"<b><blockquote>Invalid ID: <code>{id}</code></blockquote></b>\n\n"
    
    if check == len(fsubs):
        for id in fsubs:
            await clonedb.add_channel(bot_id, int(id))
        await pro.edit('<b><i>Updating chat-ID list...</i></b>')
        await client.update_chat_ids(bot_id)
        await pro.edit(
            f'<b>Force-Sub Channel Added ✅</b>\n\n{channel_list}',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await pro.edit(
            f'<b>❌ Error occurred while adding Force-Sub Channels</b>\n\n{channel_list.strip()}\n\n<b><i>Please try again...</i></b>',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

@Client.on_message(filters.command('del_fsub') & filters.private & is_admin)
async def delete_forcesub(client: Client, message: Message):
    pro = await message.reply("<b><i>Processing...</i></b>", quote=True)
    bot_id = client.bot_details['bot_id']
    channels = await clonedb.get_all_channels(bot_id)
    fsubs = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])

    if not fsubs:
        await pro.edit(
            "<b>Please provide valid IDs or arguments\n<blockquote><u>EXAMPLES</u>:\n/del_fsub [channel_ids] :</b> To delete one or multiple specified IDs\n<code>/del_fsub all</code> : To delete all available force-sub IDs</blockquote>",
            reply_markup=reply_markup
        )
        return

    if len(fsubs) == 1 and fsubs[0].lower() == "all":
        if channels:
            for id in channels:
                await clonedb.del_channel(bot_id, id)
            ids = "\n".join(f"<blockquote><code>{channel}</code> ✅</blockquote>" for channel in channels)
            await pro.edit('<b><i>Updating chat-ID list...</i></b>')
            await client.update_chat_ids(bot_id)
            await pro.edit(
                f"<b>⛔️ All available channel IDs deleted:\n{ids}</b>",
                reply_markup=reply_markup
            )
        else:
            await pro.edit(
                "<b><blockquote>No channel IDs available to delete</blockquote></b>",
                reply_markup=reply_markup
            )
        return

    passed = ""
    for sub_id in fsubs:
        try:
            id = int(sub_id)
        except ValueError:
            passed += f"<b><blockquote>Invalid ID: <code>{sub_id}</code></blockquote></b>\n"
            continue
        if id in channels:
            await clonedb.del_channel(bot_id, id)
            passed += f"<blockquote><code>{id}</code> ✅</blockquote>\n"
        else:
            passed += f"<b><blockquote><code>{id}</code> not in force-sub channels</blockquote></b>\n"

    await pro.edit('<b><i>Updating chat-ID list...</i></b>')
    await client.update_chat_ids(bot_id)
    await pro.edit(
        f"<b>⛔️ Provided channel IDs deleted:\n\n{passed}</b>",
        reply_markup=reply_markup
    )

@Client.on_message(filters.command('fsub_chnl') & filters.private & is_admin)
async def get_forcesub(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    pro = await message.reply('<b><i>Fetching chat ID list...</i></b>', quote=True)
    await message.reply_chat_action(ChatAction.TYPING)

    channel_list = await client.update_chat_ids(bot_id)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
    await message.reply_chat_action(ChatAction.CANCEL)

    await pro.edit(
        f"<b>⚡ FORCE-SUB CHANNEL LIST:</b>\n\n{channel_list or 'No channels found.'}",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command('add_admins') & filters.private & is_admin)
async def add_admins(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    pro = await message.reply("<b><i>Processing...</i></b>", quote=True)
    admin_ids = await clonedb.get_all_admins(bot_id)

    admins = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])

    if not admins:
        await pro.edit(
            "<b>You need to add admin IDs\n<blockquote><u>EXAMPLE</u>:\n/add_admins [user_id] :</b> You can add one or multiple user IDs at a time.</blockquote>",
            reply_markup=reply_markup
        )
        return

    admin_list = ""
    check = 0

    for id in admins:
        try:
            id = int(id)
        except ValueError:
            admin_list += f"<b><blockquote>Invalid ID: <code>{id}</code></blockquote></b>\n"
            continue

        if id in admin_ids:
            admin_list += f"<b><blockquote>ID: <code>{id}</code>, already exists.</blockquote></b>\n"
            continue

        id_str = str(id)
        if id_str.isdigit() and len(id_str) == 10:
            admin_list += f"<b><blockquote>ID: <code>{id}</code></blockquote></b>\n"
            check += 1
        else:
            admin_list += f"<b><blockquote>Invalid ID: <code>{id}</code></blockquote></b>\n"

    if check == len(admins):
        for id in admins:
            await clonedb.add_admin(bot_id, int(id))
        await pro.edit(
            f'<b>New IDs added to admin list ✅</b>\n\n{admin_list}',
            reply_markup=reply_markup
        )
    else:
        await pro.edit(
            f'<b>❌ Error occurred while adding admins</b>\n\n{admin_list.strip()}\n\n<b><i>Please try again...</i></b>',
            reply_markup=reply_markup
        )

@Client.on_message(filters.command('del_admins') & filters.private & is_admin)
async def delete_admins(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    pro = await message.reply("<b><i>Processing...</i></b>", quote=True)
    admin_ids = await clonedb.get_all_admins(bot_id)
    admins = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])

    if not admins:
        await pro.edit(
            "<b>Please provide valid IDs or arguments\n<blockquote><u>EXAMPLES</u>:\n/del_admins [user_ids] :</b> To delete one or multiple specified IDs\n<code>/del_admins all</code> : To delete all available user IDs</blockquote>",
            reply_markup=reply_markup
        )
        return

    if len(admins) == 1 and admins[0].lower() == "all":
        if admin_ids:
            for id in admin_ids:
                await clonedb.del_admin(bot_id, id)
            ids = "\n".join(f"<blockquote><code>{admin}</code> ✅</blockquote>" for admin in admin_ids)
            await pro.edit(
                f"<b>⛔️ All available admin IDs deleted:\n{ids}</b>",
                reply_markup=reply_markup
            )
        else:
            await pro.edit(
                "<b><blockquote>No admin list available to delete</blockquote></b>",
                reply_markup=reply_markup
            )
        return

    passed = ""
    for ad_id in admins:
        try:
            id = int(ad_id)
        except ValueError:
            passed += f"<b><blockquote>Invalid ID: <code>{ad_id}</code></blockquote></b>\n"
            continue
        if id in admin_ids:
            await clonedb.del_admin(bot_id, id)
            passed += f"<blockquote><code>{id}</code> ✅</blockquote>\n"
        else:
            passed += f"<b><blockquote><code>{id}</code> not in admin list</blockquote></b>\n"

    await pro.edit(
        f"<b>⛔️ Provided admin IDs deleted:\n\n{passed}</b>",
        reply_markup=reply_markup
    )

@Client.on_message(filters.command('admin_list') & filters.private & is_admin)
async def get_admin_list(client: Client, message: Message):
    bot_id = client.bot_details['bot_id']
    pro = await message.reply("<b><i>Processing...</i></b>", quote=True)
    admin_ids = await clonedb.get_all_admins(bot_id)
    admin_list = "<b><blockquote>No admin IDs found!</blockquote></b>"

    if admin_ids:
        admin_list = ""
        for id in admin_ids:
            await message.reply_chat_action(ChatAction.TYPING)
            try:
                user = await client.get_users(id)
                user_link = f"tg://openmessage?user_id={id}"
                first_name = user.first_name or "No first name!"
                admin_list += f"<b><blockquote>NAME: <a href='{user_link}'>{first_name}</a>\n(ID: <code>{id}</code>)</blockquote></b>\n\n"
            except (UserInvalid, FloodWait):
                admin_list += f"<b><blockquote>ID: <code>{id}</code>\n<i>Unable to load other details.</i></blockquote></b>\n\n"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
    await message.reply_chat_action(ChatAction.CANCEL)
    await pro.edit(
        f"<b>🤖 BOT ADMINS LIST:</b>\n\n{admin_list}",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command('settings') & filters.private & is_admin)
async def settings_command(client: Client, message: Message):
    pro = await message.reply("<b><i>Fetching settings...</i></b>", quote=True)
    
    settings_text = (
        "<b>⚙️ Settings Commands:</b>\n\n"
        "<b>/add_fsub</b> - Add force-sub channel IDs.\n"
        "<b>/del_fsub</b> - Delete force-sub channel IDs.\n"
        "<b>/fsub_chnl</b> - View list of force-sub channels.\n"
        "<b>/add_admins</b> - Add new admin IDs.\n"
        "<b>/del_admins</b> - Delete admin IDs.\n"
        "<b>/admin_list</b> - View list of bot admins.\n"
        "<b>/batch</b> - Make batch of messages."
    )
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Close ✖️", callback_data="close")]
    ])
    
    await pro.edit(
        text=settings_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
