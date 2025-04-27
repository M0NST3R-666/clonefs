import motor.motor_asyncio
from config import CDB_NAME, CLONE_DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        
    async def add_user(self, bot_id, user_id):
        user = {'user_id': int(user_id)}
        await self.db[str(bot_id)].insert_one(user)
    
    async def is_user_exist(self, bot_id, id):
        user = await self.db[str(bot_id)].find_one({'user_id': int(id)})
        return bool(user)
    
    async def total_users_count(self, bot_id):
        count = await self.db[str(bot_id)].count_documents({})
        return count
    
    async def get_all_users(self, bot_id):
        return self.db[str(bot_id)].find({})
    
    async def delete_user(self, bot_id, user_id):
        await self.db[str(bot_id)].delete_many({'user_id': int(user_id)})
    
    async def channel_exist(self, bot_id, channel_id: int):
        found = await self.db[f"{bot_id}_channels"].find_one({'_id': channel_id})
        return bool(found)
        
    async def add_channel(self, bot_id, channel_id: int):
        if not await self.channel_exist(bot_id, channel_id):
            await self.db[f"{bot_id}_channels"].insert_one({'_id': channel_id})
            return
    
    async def del_channel(self, bot_id, channel_id: int):
        if await self.channel_exist(bot_id, channel_id):
            await self.db[f"{bot_id}_channels"].delete_one({'_id': channel_id})
            return
    
    async def get_all_channels(self, bot_id):
        channel_docs = await self.db[f"{bot_id}_channels"].find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids
    
    async def admin_exist(self, bot_id, admin_id: int):
        found = await self.db[f"{bot_id}_admins"].find_one({'_id': admin_id})
        return bool(found)
        
    async def add_admin(self, bot_id, admin_id: int):
        if not await self.admin_exist(bot_id, admin_id):
            await self.db[f"{bot_id}_admins"].insert_one({'_id': admin_id})
            return
    
    async def del_admin(self, bot_id, admin_id: int):
        if await self.admin_exist(bot_id, admin_id):
            await self.db[f"{bot_id}_admins"].delete_one({'_id': admin_id})
            return
    
    async def get_all_admins(self, bot_id):
        users_docs = await self.db[f"{bot_id}_admins"].find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids
    
    async def add_reqChannel(self, bot_id, channel_id: int):
        await self.db[f"{bot_id}_rqst_fsub_Channel_data"].update_one(
            {'_id': channel_id}, 
            {'$setOnInsert': {'user_ids': []}},
            upsert=True
        )

    async def reqSent_user(self, bot_id, channel_id: int, user_id: int):
        await self.db[f"{bot_id}_rqst_fsub_Channel_data"].update_one(
            {'_id': channel_id}, 
            {'$addToSet': {'user_ids': user_id}}, 
            upsert=True
        )

    async def del_reqSent_user(self, bot_id, channel_id: int, user_id: int):
        await self.db[f"{bot_id}_rqst_fsub_Channel_data"].update_one(
            {'_id': channel_id}, 
            {'$pull': {'user_ids': user_id}}
        )
        
    async def clear_reqSent_user(self, bot_id, channel_id: int):
        if await self.reqChannel_exist(bot_id, channel_id):
            await self.db[f"{bot_id}_rqst_fsub_Channel_data"].update_one(
                {'_id': channel_id}, 
                {'$set': {'user_ids': []}}
            )

    async def reqSent_user_exist(self, bot_id, channel_id: int, user_id: int):
        found = await self.db[f"{bot_id}_rqst_fsub_Channel_data"].find_one(
            {'_id': channel_id, 'user_ids': user_id}
        )
        return bool(found)

    async def del_reqChannel(self, bot_id, channel_id: int):
        await self.db[f"{bot_id}_rqst_fsub_Channel_data"].delete_one({'_id': channel_id})

    async def reqChannel_exist(self, bot_id, channel_id: int):
        found = await self.db[f"{bot_id}_rqst_fsub_Channel_data"].find_one({'_id': channel_id})
        return bool(found)

    async def get_reqSent_user(self, bot_id, channel_id: int):
        data = await self.db[f"{bot_id}_rqst_fsub_Channel_data"].find_one({'_id': channel_id})
        if data:
            return data.get('user_ids', [])
        return []

    async def get_reqChannel(self, bot_id):
        channel_docs = await self.db[f"{bot_id}_rqst_fsub_Channel_data"].find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids
        
    async def get_reqLink_channels(self, bot_id):
        channel_docs = await self.db[f"{bot_id}_store_reqLink_data"].find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids

    async def get_stored_reqLink(self, bot_id, channel_id: int):
        data = await self.db[f"{bot_id}_store_reqLink_data"].find_one({'_id': channel_id})
        if data:
            return data.get('link')
        return None

    async def store_reqLink(self, bot_id, channel_id: int, link: str):
        await self.db[f"{bot_id}_store_reqLink_data"].update_one(
            {'_id': channel_id}, 
            {'$set': {'link': link}}, 
            upsert=True
        )

    async def del_stored_reqLink(self, bot_id, channel_id: int):
        await self.db[f"{bot_id}_store_reqLink_data"].delete_one({'_id': channel_id})

clonedb = Database(CLONE_DB_URI, CDB_NAME)