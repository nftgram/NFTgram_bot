import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import any_state
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils import markdown
from aiogram.utils.emoji import emojize

from nftgram.bot import dp
from nftgram.database import database
from nftgram.i18n import _


@dp.message_handler(CommandStart(), state=any_state)
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start."""
    keyboard = types.ReplyKeyboardMarkup(
        row_width=2, resize_keyboard=True, one_time_keyboard=True
    )
    keyboard.add(types.KeyboardButton(emojize(":heavy_plus_sign: ") + _("mint_nft")))
    await state.finish()
    file_id = await database.get("logo_file_id")
    if file_id:
        logo_message = await message.answer_photo(file_id.decode())
    else:
        logo_message = await message.answer_photo(
            types.InputFile.from_url("https://nftgram.store/images/logo_forbot.png")
        )
        photo = max(logo_message.photo, key=lambda size: size.file_size)
        await database.set("logo_file_id", photo.file_id)
    await message.answer(
        _("start_message {nftgram_url} {mint_nft}").format(
            nftgram_url=markdown.link("NFTgram", "https://nftgram.store"),
            mint_nft=markdown.bold(_("mint_nft")),
        ),
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Handle exceptions when calling handlers."""
    if not isinstance(exception, MessageNotModified):
        logging.getLogger(__name__).error(
            "Error handling request {}".format(update.update_id), exc_info=True
        )
    return True
