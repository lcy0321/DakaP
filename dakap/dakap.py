"""A Discord bot made by lcy"""

import asyncio
import logging
import shlex
from typing import List, TypeVar

import discord

from .common import CommandFunc
from .count_emojis import count_emojis
from .get_time import get_time
from .misc import random_choice, show_raw_message
from .stock import get_stocks_prices
from .youtube_thumbnail import (
    parse_and_generate_youtube_thumbnail_url,
    reply_youtube_thumbnail,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)-7s:%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

T = TypeVar('T')  # pylint: disable=invalid-name


class DakaP(discord.Client):
    """A Discord bot made by lcy"""

    def __init__(self, prefix: str = '$'):
        self.prefix = prefix
        super().__init__(
            intents=discord.Intents(
                guilds=True,
                emojis_and_stickers=True,
                guild_messages=True,
                guild_reactions=True,
                message_content=True,
            )
        )
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        """Triggered when ready."""
        if not self.user:
            raise RuntimeError('User not ready.')
        logger.info(f'Username   : {self.user.name}')
        logger.info(f'ID         : {self.user.id}')
        logger.info(
            f'In guild(s): {", ".join([f"{guild.name}({guild.id})" for guild in self.guilds])}'
        )

    async def on_message(self, message: discord.Message) -> None:
        """Triggered when a message start with specific prefix."""

        if message.author.bot:
            return

        for message_line in message.content.splitlines():
            arguments = self._parse_arguments(message_line)

            if arguments:
                command_func: CommandFunc = self._nope
                command = arguments[0].lower()

                logger.info(f'{message.guild}-{message.channel}: {command}')

                if command == 'help':
                    await self._send_help(message)

                # elif command == 'bye':
                #     await self.close()

                elif command in ('emoji', 'emojis'):
                    command_func = count_emojis

                elif command == 'raw':
                    command_func = show_raw_message

                elif command == 'choose':
                    command_func = random_choice

                elif command == 'time':
                    command_func = get_time

                elif command in ('yt', 'youtube'):
                    command_func = reply_youtube_thumbnail

                elif command in ('stock', 'finance'):
                    command_func = get_stocks_prices

                # elif command == 'clean':
                #     await self._clean_my_messages(message, arguments)

                await command_func(self, message, arguments)

    @staticmethod
    async def _nope(_client, _message, _arguments) -> None:
        pass

    async def _send_help(self, message: discord.Message) -> None:
        """Send the help message of this bot"""
        help_msgs = []
        help_msgs.append('Source: https://github.com/lcy0321/DakaP')
        help_msgs.append('```')
        help_msgs.append('help')
        help_msgs.append('        顯示說明')
        help_msgs.append('emoji/emojis')
        help_msgs.append('        計算伺服器內一定時間內各個 emoji 的數量')
        help_msgs.append('raw <content>')
        help_msgs.append('        顯示該則訊息在被格式化前的型態')
        help_msgs.append('choose <item1> [<item2>...]')
        help_msgs.append('        隨機選擇其中一個項目')
        help_msgs.append('time [<time>]')
        help_msgs.append('        顯示不同時區中的現在時間或特定時間')
        help_msgs.append('yt/youtube <YouTube URL>')
        help_msgs.append('        顯示該 YouTube 影片最新的縮圖')
        help_msgs.append('stock/finance <stock symbol>')
        help_msgs.append('        顯示該股票的最新價格（延遲）')
        help_msgs.append('```')

        await message.reply('\n'.join(help_msgs))

    def _parse_arguments(self, message_line: str) -> List[str]:
        """Parse the arguments in the message if it starts with the prefix"""

        message_stripped = message_line.strip()

        if not message_stripped.startswith(self.prefix):
            return []

        arguments = shlex.split(message_stripped)

        if arguments[0] == '$':
            # e.g. $ command arg1 arg2
            arguments = arguments[1:]
        else:
            # e.g. $command arg1 arg2
            arguments[0] = arguments[0][1:]

        return arguments


client = DakaP()


@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(
    send_messages=True,
    send_messages_in_threads=True,
)
@client.tree.context_menu(name='擷取 YT 預覽圖')
async def context_menu_reply_youtube_thumbnail(
    interaction: discord.Interaction,
    message: discord.Message,
) -> None:
    for message_line in message.content.splitlines():
        try:
            thumbnail_url = parse_and_generate_youtube_thumbnail_url(
                yt_url=message_line,
            )
        except ValueError:
            continue
        else:
            return await interaction.response.send_message(content=thumbnail_url)
    return await interaction.response.send_message(
        content='No YouTube URL found in the message.',
        ephemeral=True,
    )


def main():
    """Run the bot with the token."""

    with open('bot-token', encoding='utf-8') as token_file:
        token = token_file.read().strip()

    asyncio.run(client.start(token))


if __name__ == "__main__":
    main()
