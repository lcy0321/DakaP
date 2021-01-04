"""Misc commands for DAKA-bot"""

import random
from functools import partial
from typing import Optional, Tuple

from discord.channel import TextChannel
from discord.message import Message

from .common import SendFunc, is_msg_from_this_bot


async def show_raw_message(
        send: SendFunc,
        message: Message,
) -> None:
    """Send the raw text of the message."""
    # '\u200b': Zero-width space
    zero_width_space = '\u200b'
    await send(
        f'```\n{message.content.replace("`", zero_width_space + "`")}\n```'
    )


async def clean_my_messages(
        channel: TextChannel,
        limit: Optional[int],
) -> None:
    """Search for specific number of messages, and delete those sent by this bot."""

    if limit is not None:
        purge_limit = limit
    else:
        purge_limit = 100

    await channel.purge(limit=purge_limit, check=partial(is_msg_from_this_bot, channel.guild))


async def random_choice(
        send: SendFunc,
        options: Tuple[str, ...],
) -> None:
    """Randomly choose the items from the given list"""

    if options[0:]:
        choice = random.choice(options[0:])
        await send(f'> {choice}')
