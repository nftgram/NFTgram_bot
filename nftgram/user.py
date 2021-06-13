import json
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from nftgram.database import database


class UserMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: types.Update, data: dict):
        update_user = None
        if update.message:
            update_user = update.message.from_user
        elif update.callback_query and update.callback_query.message:
            update_user = update.callback_query.from_user
        if update_user:
            database_user = {
                "first_name": update_user.first_name,
                "last_name": update_user.last_name,
                "username": update_user.username,
                "locale": update_user.language_code,
            }
            # if update_user.id != config.OPERATOR_ID:
            #     database_user.state = states.Registration.first_message.state
            await database.set(f"name:{update_user.id}", json.dumps(database_user))


user_middleware = UserMiddleware()
