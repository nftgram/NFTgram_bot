from aiogram import types
from aiogram.dispatcher.filters.filters import Filter
from aiogram.utils.callback_data import CallbackData

from nftgram import config


class OperatorFilter(Filter):
    async def check(self, obj: types.base.TelegramObject) -> bool:
        if isinstance(obj, types.Message):
            return obj.from_user.id == obj.chat.id == config.OPERATOR_ID
        elif isinstance(obj, types.CallbackQuery):
            return obj.from_user.id == obj.message.chat.id == config.OPERATOR_ID
        else:
            return False


edit_token_step = CallbackData("edit_token_step", "step")
approve_token = CallbackData("approve_token", "token_id")
reject_token = CallbackData("reject_token", "token_id")
request_token_changes = CallbackData("request_token_changes", "token_id")
start_changes = CallbackData("start_changes", "token_id")
