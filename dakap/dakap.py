"""A Discord bot made by lcy"""

# pylint: disable=invalid-name

import asyncio
import logging
import re
import signal
from enum import IntEnum
from typing import Optional, TypeVar

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context
from discord_slash import SlashCommand, SlashContext

from dakap.common import SendFunc

from .count_emojis import count_emojis
from .get_time import get_time
from .misc import clean_my_messages, random_choice, show_raw_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s:%(levelname)-7s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

T = TypeVar('T')


class InteractionResponseType(IntEnum):
    """InteractionResponseType for Slash Command Interaction Response
    Refers to:
    https://discord.com/developers/docs/interactions/slash-commands#interaction-response
    """
    # ACK a `Ping`
    Pong = 1
    # ACK a command without sending a message, eating the user's input
    Acknowledge = 2
    # respond with a message, eating the user's input
    ChannelMessage = 3
    # respond with a message, showing the user's input
    ChannelMessageWithSource = 4
    # ACK a command without sending a message, showing the user's input
    AcknowledgeWithSource = 5


class DakaPBot(Bot):
    """Override some methods in `discord.ext.commands`"""

    _prefix = '$'

    @staticmethod
    def prefix_match(_bot: Bot, message: discord.Message) -> str:
        """Match the prefix with space insensitivity"""
        escaped_prefix = re.escape(DakaPBot._prefix)
        match = re.match(
            pattern=rf'{escaped_prefix}\s*',
            string=message.content,
        )
        if match:
            return match[0]
        return DakaPBot._prefix

    async def on_ready(self) -> None:
        """Triggered when ready."""
        logger.info(f'Username   : {self.user.name}')
        logger.info(f'ID         : {self.user.id}')
        logger.info(f'In guild(s): {", ".join([guild.name for guild in self.guilds])}')


bot = DakaPBot(
    command_prefix=DakaPBot.prefix_match,
    case_insensitive=True,
    description='Source: https://github.com/lcy0321/DakaP',
)
slash = SlashCommand(bot, auto_register=True)


async def _ack_slash_tirggered(ctx: SlashContext):
    await ctx.send(send_type=InteractionResponseType.AcknowledgeWithSource)


def _wrap_slash_context_send(ctx: SlashContext, hidden: bool = False) -> SendFunc:
    async def send(content: str):
        await ctx.send(
            send_type=InteractionResponseType.ChannelMessage,
            content=content,
            hidden=hidden,
        )
    return send


@bot.command()
async def emoji(ctx: Context):
    """Count the emojis in the guild."""
    async with ctx.typing():
        return await count_emojis(send=ctx.send, guild=ctx.guild)


@bot.command()
async def emojis(ctx: Context):
    """Count the emojis in the guild."""
    async with ctx.typing():
        return await count_emojis(send=ctx.send, guild=ctx.guild)


@bot.command()
async def raw(ctx: Context):
    """Send the raw text of the message."""
    return await show_raw_message(send=ctx.send, message=ctx.message)


@bot.command()
async def choose(ctx: Context, *options: str):
    """Randomly choose the items from the given list."""
    return await random_choice(send=ctx.send, options=options)


@bot.command()
async def time(ctx: Context, *time_args: str):
    """Get time in different time zones."""
    return await get_time(send=ctx.send, time_args=time_args)


@bot.command()
@commands.is_owner()
async def clean(ctx: Context, limit: Optional[int]):
    """Search for specific number of messages, and delete those sent by this bot."""
    return await clean_my_messages(channel=ctx.channel, limit=limit)


@slash.slash(name='emoji', description='Count the emojis in the guild.')
async def slash_emoji(ctx: SlashContext):
    """Count the emojis in the guild."""
    await _ack_slash_tirggered(ctx=ctx)
    async with ctx.channel.typing():
        return await count_emojis(send=_wrap_slash_context_send(ctx=ctx), guild=ctx.guild)


@slash.slash(name='time', description='Get time in different time zones.')
async def slash_time(ctx: SlashContext, *time_args: str):
    """Get time in different time zones."""
    return await get_time(send=_wrap_slash_context_send(ctx=ctx, hidden=True), time_args=time_args)


def main():
    """Run the bot with the token."""

    with open('bot-token') as token_file:
        token = token_file.read().strip()

    # Work-around: discord.Client.close() has some issues.
    # like "Unclosed client session", "Unclosed connector", "Task was destroyed but it is pending!"
    # client.run(token)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.ensure_future(bot.close()))
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(bot.close()))
    loop.run_until_complete(bot.start(token))


if __name__ == "__main__":
    main()
