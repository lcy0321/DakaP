"""Misc commands for DAKA-bot"""

import random
from functools import partial
from typing import Sequence

import discord

from .common import is_msg_from_me


async def show_raw_message(
        _client,
        message: discord.Message,
        _arguments,
) -> None:
    """Send the raw text of the message."""
    # '\u200b': Zero-width space
    zero_width_space = '\u200b'
    await message.channel.send(
        f'```\n{message.content.replace("`", zero_width_space + "`")}\n```'
    )


async def clean_my_messages(
        client: discord.Client,
        message: discord.Message,
        arguments: Sequence[str]
) -> None:
    """Search for specific number of messages, and delete those sent by me."""

    limit = 100

    if arguments[1:]:
        try:
            limit = int(arguments[1])
        except ValueError:
            pass

    await message.channel.purge(limit=limit, check=partial(is_msg_from_me, client))


async def random_choice(
        _client,
        message: discord.Message,
        arguments: Sequence[str]
) -> None:
    """Randomly choose the items from the given list"""

    if arguments[1:]:
        choice = random.choice(arguments[1:])
        await message.channel.send(f'> {choice}')
