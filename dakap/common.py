"""Helping functions"""

from typing import Awaitable, Callable, Sequence

import discord

CommandFunc = Callable[[discord.Client, discord.Message, Sequence[str]], Awaitable[None]]


def is_msg_from_this_bot(guild: discord.Guild, message: discord.Message) -> bool:
    """Check if the message is sent by this bot."""
    return message.author == guild.me
