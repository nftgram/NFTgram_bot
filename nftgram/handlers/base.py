import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import any_state
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils.emoji import emojize

from nftgram.bot import dp
from nftgram.i18n import _


@dp.message_handler(CommandStart(), state=any_state)
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start."""
    keyboard = types.ReplyKeyboardMarkup(
        row_width=2, resize_keyboard=True, one_time_keyboard=True
    )
    keyboard.add(
        types.KeyboardButton(emojize(":heavy_plus_sign: ") + _("mint_nft")),
        types.KeyboardButton(emojize(":moneybag: ") + _("buy_nft")),
    )
    await state.finish()
    await message.answer(_("start_message"), reply_markup=keyboard)


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle exceptions when calling handlers."""
    if not isinstance(exception, MessageNotModified):
        logging.getLogger(__name__).error(
            "Error handling request {}".format(update.update_id), exc_info=True
        )
    return True
