"""Helping functions"""

from typing import Awaitable, Callable, Sequence

import discord

CommandFunc = Callable[[discord.Client, discord.Message, Sequence[str]], Awaitable[None]]
SupportChannel = discord.TextChannel | discord.VoiceChannel | discord.Thread


def is_msg_from_me(client: discord.Client, message: discord.Message) -> bool:
    """Check if the message is sent by this bot."""
    return message.author == client.user
