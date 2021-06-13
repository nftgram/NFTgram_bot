import os

from nftgram import config
from nftgram import states
from nftgram.bot import bot
from nftgram.i18n import _


def message_from_lines(lines, numbered=False):
    if numbered:
        line_values = [f"{i + 1}. {line}" for i, line in enumerate(lines.values())]
    else:
        line_values = list(lines.values())
    return "\n".join(line_values)


def token_message_lines(token):
    name = _("name {name}").format(name=token["name"])
    description = _("description {description}").format(
        description=token.get("description", "-")
    )
    price = _("price {price}").format(price=token["price"])
    royalty = _("royalty {royalty}").format(royalty=int(token["royalty"]) / 100)
    license = _("license {license}").format(license=token["license"])
    return {
        states.Minting.name._state: name,
        states.Minting.description._state: description,
        states.Minting.price._state: price,
        states.Minting.royalty._state: royalty,
        states.Minting.license._state: license,
    }


def token_message(token) -> str:
    return message_from_lines(token_message_lines(token))


async def get_upload(file_id):
    file_path = os.path.join(config.UPLOADS_DIRECTORY, file_id)
    if not os.path.exists(file_path):
        await bot.download_file_by_id(file_id, file_path)
