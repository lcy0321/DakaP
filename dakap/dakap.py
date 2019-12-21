"""A Discord bot made by lcy"""

import asyncio
import logging
import shlex
import signal
from typing import List, TypeVar

import discord

from .common import CommandFunc
from .count_emojis import count_emojis
from .get_time import get_time
from .misc import random_choice, show_raw_message

logger = logging.getLogger(__name__)    # pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s:%(levelname)-7s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

T = TypeVar('T')    # pylint: disable=invalid-name


class DakaP(discord.Client):
    """A Discord bot made by lcy"""

    def __init__(self, prefix: str = '$'):
        self.prefix = prefix
        super().__init__()

    async def on_ready(self) -> None:
        """Triggered when ready."""
        logger.info(f'Username   : {self.user.name}')
        logger.info(f'ID         : {self.user.id}')
        logger.info(f'In guild(s): {", ".join([guild.name for guild in self.guilds])}')

    async def on_message(self, message: discord.Message) -> None:
        """Triggered when a message start with specific prefix."""

        if message.author.bot:
            return

        arguments = self._parse_arguments(message)

        if arguments:
            command_func: CommandFunc = self._nope
            command = arguments[0]

            logger.info(f'{message.guild}-{message.channel}: {command}')

            if command == 'help':
                await self._send_help(message)

            # elif command == 'bye':
            #     await self.close()

            elif command in ['emoji', 'emojis']:
                command_func = count_emojis

            elif command == 'raw':
                command_func = show_raw_message

            elif command == 'choose':
                command_func = random_choice

            elif command == 'time':
                command_func = get_time

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
        help_msgs.append('```')

        await message.channel.send('\n'.join(help_msgs))

    def _parse_arguments(self, message: discord.Message) -> List[str]:
        """Parse the arguments in the message if it starts with the prefix"""

        message_stripped = message.content.strip()

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


def main():
    """Run the bot with the token."""

    with open('bot-token') as token_file:
        token = token_file.read().strip()

    client = DakaP()

    # Work-around: discord.Client.close() has some issues.
    # like "Unclosed client session", "Unclosed connector", "Task was destroyed but it is pending!"
    # client.run(token)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.ensure_future(client.close()))
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(client.close()))
    loop.run_until_complete(client.start(token))


if __name__ == "__main__":
    main()
