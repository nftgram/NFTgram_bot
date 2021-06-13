from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class Minting(StatesGroup):
    upload = State()
    confirm_photo_upload = State()
    price = State()
    check_price = State()
    name = State()
    description = State()
    royalty = State()
    license = State()
    check_token = State()
    edit_token = State()


moderator_comment = State()
