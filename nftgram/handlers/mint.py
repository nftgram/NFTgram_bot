import json
import decimal
from urllib.parse import quote

from aiogram import types
from aiogram.types import ContentType
from aiogram.utils import markdown
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters.state import any_state

from nftgram import config
from nftgram.database import database
from nftgram import filters
from nftgram import utils
from nftgram.states import Minting
from nftgram.states import moderator_comment
from nftgram.bot import dp
from nftgram.bot import bot
from nftgram.i18n import _


step_handlers = {}


def step_handler(state):
    def decorator(callback):
        step_handlers[state._state] = callback
        return callback

    return decorator


@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":heavy_plus_sign:")), state=any_state
)
async def start_minting(message, state):
    await Minting.upload.set()
    await message.answer(
        _("ask_upload {nftgram_url} {rarible_url} {rules_url}").format(
            nftgram_url=markdown.link("NFTgram", "https://test.nftgram.store/"),
            rarible_url=markdown.link("Rarible", "https://test.nftgram.store/"),
            rules_url=markdown.link(_("rules"), "https://static.rarible.com/terms.pdf"),
        ),
        parse_mode=types.ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


@step_handler(Minting.upload)
async def upload_step(message, state):
    if message.content_type == ContentType.PHOTO:
        upload = max(message.photo, key=lambda size: size.file_size)
    elif message.content_type == ContentType.ANIMATION:
        upload = message.animation
    elif message.content_type == ContentType.DOCUMENT:
        upload = message.document
    else:
        await message.answer(_("unknown_content_type"))
        return False
    await utils.get_upload(upload.file_id)
    async with state.proxy() as data:
        data["upload"] = upload.file_id
        data["content_type"] = message.content_type
    return True


@dp.message_handler(
    content_types=[ContentType.PHOTO, ContentType.ANIMATION],
    state=Minting.upload,
)
async def confirm_compressed_upload(message, state):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton(emojize(":white_check_mark: ") + _("yes")),
        types.KeyboardButton(emojize(":x: ") + _("no")),
    )
    if message.content_type == ContentType.PHOTO:
        upload = max(message.photo, key=lambda size: size.file_size)
    elif message.content_type == ContentType.ANIMATION:
        upload = message.animation
    await state.update_data(upload=upload.file_id)
    await Minting.confirm_photo_upload.set()
    await message.answer(_("confirm_compressed_upload"), reply_markup=keyboard)


@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":x:")), state=Minting.confirm_photo_upload
)
async def ask_new_upload(message, state):
    await Minting.upload.set()
    await message.answer(_("ask_new_upload"))


@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":white_check_mark:")),
    state=Minting.confirm_photo_upload,
)
async def set_upload_compressed(message, state):
    async with state.proxy() as data:
        await utils.get_upload(data["upload"])
    await Minting.price.set()
    await message.answer(_("ask_price"))


@dp.message_handler(
    content_types=ContentType.DOCUMENT,
    state=Minting.upload,
)
@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":white_check_mark:")),
    state=Minting.confirm_photo_upload,
)
async def set_upload_document(message, state):
    if await upload_step(message, state):
        await Minting.price.set()
        await message.answer(_("ask_price"))


@dp.message_handler(content_types=ContentType.ANY, state=Minting.upload)
async def unknown_upload_content_type(message, state):
    await message.answer(_("unknown_content_type"))


@step_handler(Minting.price)
async def price_step(message, state):
    try:
        price_with_fee = decimal.Decimal(message.text)
    except decimal.InvalidOperation:
        await message.answer(_("wrong_price_format"))
        return False
    price = str(price_with_fee * decimal.Decimal("0.98"))
    await state.update_data(price=price)
    return price


@dp.message_handler(state=Minting.price)
async def set_price(message, state):
    price = await price_step(message, state)
    if price is not False:
        keyboard = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        keyboard.add(
            types.KeyboardButton(emojize(":white_check_mark: ") + _("yes")),
            types.KeyboardButton(emojize(":x: ") + _("no")),
        )
        await Minting.check_price.set()
        await message.answer(
            _("check_price {price}").format(price=price), reply_markup=keyboard
        )


@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":x:")), state=Minting.check_price
)
async def ask_new_price(message, state):
    await Minting.price.set()
    await message.answer(_("ask_new_price"))


@dp.message_handler(
    lambda msg: msg.text.startswith(emojize(":white_check_mark:")),
    state=Minting.check_price,
)
async def check_price(message, state):
    await Minting.name.set()
    await message.answer(_("ask_name"))


@step_handler(Minting.name)
async def name_step(message, state):
    await state.update_data(name=message.text)
    return True


@dp.message_handler(state=Minting.name)
async def set_name(message, state):
    if await name_step(message, state):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                emojize(":fast_forward: ") + _("skip_description"),
                callback_data="skip_description",
            )
        )
        await Minting.description.set()
        await message.answer(_("ask_description"), reply_markup=keyboard)


@step_handler(Minting.description)
async def description_step(message, state):
    await state.update_data(description=message.text)
    return True


@dp.callback_query_handler(
    lambda call: call.data == "skip_description",
    state=Minting.description,
)
async def skip_description(call, state):
    await Minting.royalty.set()
    await call.answer()
    await call.message.answer(_("ask_royalty"))


@dp.message_handler(state=Minting.description)
async def set_description(message, state):
    if await description_step(message, state):
        await Minting.royalty.set()
        await message.answer(_("ask_royalty"))


@step_handler(Minting.royalty)
async def royalty_step(message, state):
    try:
        royalty = decimal.Decimal(message.text)
    except decimal.InvalidOperation:
        await message.answer(_("wrong_royalty_format"))
        return False
    await state.update_data(royalty=int(round(royalty, 2) * 100))
    return True


@dp.message_handler(state=Minting.royalty)
async def set_royalty(message, state):
    if await royalty_step(message, state):
        keyboard = types.ReplyKeyboardMarkup(
            row_width=1, one_time_keyboard=True, resize_keyboard=True
        )
        keyboard.add(
            types.KeyboardButton(emojize(":dollar: ") + _("commercial_use")),
            types.KeyboardButton(
                emojize(":globe_with_meridians: ") + _("non_commercial_use")
            ),
        )
        await Minting.license.set()
        await message.answer(_("ask_license"), reply_markup=keyboard)


@step_handler(Minting.license)
async def license_step(message, state):
    if message.text.startswith(emojize(":dollar: ")):
        license = "CC BY-SA 4.0"
    elif message.text.startswith(emojize(":globe_with_meridians: ")):
        license = "CC BY-NC-SA 4.0"
    else:
        await message.answer(_("unknown_license"))
        return False
    await state.update_data(license=license)
    return True


@dp.message_handler(state=Minting.license)
async def set_license(message, state):
    if await license_step(message, state):
        await check_token(message, state)


async def send_upload(chat_id, data):
    if data["content_type"] == ContentType.PHOTO:
        method = bot.send_photo
    elif data["content_type"] == ContentType.ANIMATION:
        method = bot.send_animation
    elif data["content_type"] == ContentType.DOCUMENT:
        method = bot.send_document
    await method(chat_id, data["upload"])


async def check_token(update, state):
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(
        types.InlineKeyboardButton(_("edit_token"), callback_data="edit_token"),
        types.InlineKeyboardButton(_("publish_token"), callback_data="publish_token"),
    )
    await Minting.check_token.set()
    data = await state.get_data()
    print(data)
    token = utils.token_message(data)
    text = _("check_token") + "\n" + token
    if isinstance(update, types.Message):
        await send_upload(update.from_user.id, data)
        await update.answer(text, reply_markup=keyboard_markup)
    elif isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard_markup)


@dp.callback_query_handler(
    lambda call: call.data == "cancel_edit_token",
    state=Minting.edit_token,
)
async def cancel_edit_token(call, state):
    await call.answer()
    await check_token(call, state)


async def edit_token(call, data, *, edit=True):
    lines = utils.token_message_lines(data)
    buttons = []
    for i, key in enumerate(lines.keys()):
        buttons.append(
            types.InlineKeyboardButton(
                str(i + 1), callback_data=filters.edit_token_step.new(step=key)
            )
        )
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(*buttons)
    keyboard_markup.row(
        types.InlineKeyboardButton(
            _("cancel_edit_token"), callback_data="cancel_edit_token"
        )
    )
    method = call.message.edit_text if edit else call.message.answer
    await Minting.edit_token.set()
    await call.answer()
    await method(
        _("token_editing") + "\n" + utils.message_from_lines(lines, numbered=True),
        reply_markup=keyboard_markup,
    )


@dp.callback_query_handler(
    lambda call: call.data == "edit_token",
    state=Minting.check_token,
)
@dp.callback_query_handler(
    lambda call: call.data == "cancel_edit_step",
    state=Minting.edit_token,
)
async def edit_token_start(call, state):
    data = await state.get_data()
    await edit_token(call, data)


@dp.callback_query_handler(filters.edit_token_step.filter(), state=Minting.edit_token)
async def edit_token_step(call, callback_data, state):
    keyboard = types.InlineKeyboardMarkup()
    step = callback_data["step"]
    if step == Minting.name._state:
        answer = _("ask_new_name")
    elif step == Minting.description._state:
        answer = _("ask_new_description")
        keyboard.row(
            types.InlineKeyboardButton(
                _("remove_description"), callback_data="remove_description"
            ),
        )
    elif step == Minting.price._state:
        answer = _("ask_new_price")
    elif step == Minting.royalty._state:
        answer = _("ask_new_royalty")
    elif step == Minting.license._state:
        answer = _("ask_new_license")
    else:
        await call.answer(_("unknown_step"))
        return
    keyboard.row(
        types.InlineKeyboardButton(
            _("cancel_edit_step"), callback_data="cancel_edit_step"
        ),
    )
    await state.update_data(edit_step=step)
    await call.answer()
    await call.message.edit_text(answer, reply_markup=keyboard)


@dp.callback_query_handler(
    lambda call: call.data == "remove_description",
    state=Minting.edit_token,
)
async def remove_description(call, state):
    async with state.proxy() as data:
        data.pop("description")
    await check_token(call, state)


@dp.message_handler(state=Minting.edit_token)
async def edit_token_finish(message, state):
    data = await state.get_data()
    if await step_handlers[data["edit_step"]](message, state) is not False:
        await check_token(message, state)


@dp.callback_query_handler(
    lambda call: call.data == "publish_token",
    state=Minting.check_token,
)
async def publish_token(call, state):
    data = await state.get_data()
    token = utils.token_message(data)
    data["user_id"] = call.from_user.id
    token_id = await database.incr("token_id")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            emojize(":white_check_mark: ") + _("approve_token"),
            callback_data=filters.approve_token.new(token_id=token_id),
        ),
        types.InlineKeyboardButton(
            emojize(":arrows_counterclockwise: ") + _("request_token_changes"),
            callback_data=filters.request_token_changes.new(token_id=token_id),
        ),
        types.InlineKeyboardButton(
            emojize(":x: ") + _("reject_token"),
            callback_data=filters.reject_token.new(token_id=token_id),
        ),
    )
    await database.set(f"token:{token_id}", json.dumps(data))
    await send_upload(config.MODERATOR_ID, data)
    await bot.send_message(
        config.MODERATOR_ID,
        _("moderation_request {token_id}").format(token_id=token_id) + "\n" + token,
        reply_markup=keyboard,
    )
    await state.finish()
    await call.answer()
    await call.message.answer(
        _("moderation_requested {token_id}").format(token_id=token_id)
    )


@dp.callback_query_handler(filters.approve_token.filter(), state=any_state)
async def approve_token(call, callback_data, state):
    token_id = callback_data["token_id"]
    data = json.loads(await database.get(f"token:{token_id}"))
    ipfs_hash = await utils.pin_to_ipfs(token_id, data)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            _("confirm_url"),
            url="https://nftgram.store/mint?ipfs={}&royalty={}&token_id={}".format(
                quote(f"/ipfs/{ipfs_hash}"), data["royalty"], token_id
            ),
        )
    )
    await bot.send_message(data["user_id"], _("confirm_transaction"))
    await call.answer()
    await call.message.edit_text(_("token_approved"))


@dp.callback_query_handler(filters.request_token_changes.filter(), state=any_state)
async def request_token_changes(call, callback_data, state):
    await moderator_comment.set()
    await state.update_data(token_id=callback_data["token_id"])
    await call.answer()
    await call.message.answer(_("ask_moderator_comment"))


@dp.message_handler(state=moderator_comment)
async def send_moderator_comment(message, state):
    async with state.proxy() as data:
        keyboard = types.InlineKeyboardMarkup()
        callback_data = filters.start_changes.new(token_id=data["token_id"])
        keyboard.add(
            types.InlineKeyboardButton(
                emojize(":pencil2: ") + _("start_editing"),
                callback_data=callback_data,
            )
        )
    token_id = data["token_id"]
    data = json.loads(await database.get(f"token:{token_id}"))
    await bot.send_message(
        data["user_id"],
        _("moderator_comment {comment}").format(comment=message.text),
        reply_markup=keyboard,
    )
    await state.finish()


@dp.callback_query_handler(filters.start_changes.filter(), state=any_state)
async def start_changes(call, callback_data, state):
    token_id = callback_data["token_id"]
    data = json.loads(await database.get(f"token:{token_id}"))
    await edit_token(call, data, edit=False)


@dp.callback_query_handler(filters.reject_token.filter(), state=any_state)
async def reject_token(call, callback_data, state):
    token_id = callback_data["token_id"]
    data = json.loads(await database.get(f"token:{token_id}"))
    await bot.send_message(data["user_id"], _("token_rejected"))
    await call.answer()
    await call.message.edit_text(
        _("token_rejected_moderator {token_id}").format(token_id=token_id)
    )
