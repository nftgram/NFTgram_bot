from aiogram import Bot
from aiogram import Dispatcher

from nftgram import config
from nftgram import database
from nftgram.i18n import i18n
from nftgram.user import user_middleware

bot = Bot(config.TOKEN)
dp = Dispatcher(bot)
dp.storage = database.storage
dp.middleware.setup(user_middleware)
dp.middleware.setup(i18n)
