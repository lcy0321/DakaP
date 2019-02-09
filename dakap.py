"""A bot to count the emojis in a guild."""

import asyncio
import logging
import signal
from collections import Counter
from datetime import datetime, timedelta
from itertools import zip_longest
from operator import itemgetter

import discord

logger = logging.getLogger(__name__)    # pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s:%(levelname)-7s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def grouper(iterable, number, fillvalue=None):
    """
    From https://docs.python.org/3/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * number
    return zip_longest(*args, fillvalue=fillvalue)


class DakaP(discord.Client):
    """A bot to count the emojis in the guild."""

    prefix = '$'

    async def on_ready(self):
        """Triggered when ready."""
        logger.info(f'Username   : {self.user.name}')
        logger.info(f'ID         : {self.user.id}')
        logger.info(f'In guild(s): {", ".join([guild.name for guild in self.guilds])}')

    async def on_message(self, message):
        """Triggered when a message start with specific prefix."""

        if message.author.bot:
            return

        if message.content.startswith(self.prefix):
            command = message.content.replace(self.prefix, '').strip().split(maxsplit=1)[0]

            logger.info(f'{message.guild}-{message.channel}: {command}')

            if command == 'bye':
                await self.close()

            elif command in ['emoji', 'emojis']:
                await self._count_emojis(message)

            elif command == 'raw':
                await self._show_raw_message(message)

            elif command == 'clean':
                await self._clean_my_messages(message)

    async def _count_emojis(self, message):
        """Count the emojis in the guild."""

        await message.channel.send(
            f'Start counting emojis in {message.guild.name}...'
        )

        emojis = [str(emoji) for emoji in message.guild.emojis]
        emoji_counter = Counter(emojis)     # Counter starts from 1

        start_time = datetime.utcnow() - timedelta(weeks=12)

        counting_tasks = []

        for channel in message.guild.channels:
            if isinstance(channel, discord.TextChannel) and \
                    message.guild.me.permissions_in(channel).read_message_history:

                counting_tasks.append(asyncio.create_task(
                    self._count_emojis_in_channel(emojis, channel, after=start_time)
                ))

        emoji_counter = sum(
            [await task for task in counting_tasks],
            emoji_counter
        )

        result = [
            f'{emoji}: {count - 1 :3}'
            for emoji, count in sorted(emoji_counter.items(), key=itemgetter(1), reverse=True)
        ]

        if logger.isEnabledFor(logging.DEBUG):
            for emoji_count in result:
                logger.debug(emoji_count)

        # Counted from <UTC+8 datetime>
        await message.channel.send(
            (f'Counted from '
             f'{(start_time + timedelta(hours=8)).isoformat(sep=" ", timespec="seconds")}\n')
            + '\n'.join(
                ['\t'.join(column) for column in grouper(result, number=10, fillvalue='')]
            )
        )

    @staticmethod
    async def _show_raw_message(message):
        """Send the raw text of the message."""
        # '\u200b': Zero-width space
        zero_width_space = '\u200b'
        await message.channel.send(
            f'```\n{message.content.replace("`", zero_width_space + "`")}\n```'
        )

    async def _clean_my_messages(self, message):
        """Search for specific number of messages, and delete those sent by me."""

        limit = 100
        parameters = message.content.replace(self.prefix, '').strip().split()[1:]

        if parameters:
            try:
                limit = int(parameters[0])
            except ValueError:
                pass

        await message.channel.purge(limit=limit, check=self._is_msg_from_me)

    def _is_msg_from_me(self, message):
        """Check if the message is sent by this bot."""
        return message.author.id == self.user.id

    async def _count_emojis_in_channel(self, emojis, channel, after):
        """Count emojis in the messages in the channel."""
        emoji_counter = Counter()

        logger.debug(f'Start counting in #{channel.name}...')

        async for history_message in channel.history(limit=None, after=after):
            if not self._is_msg_from_me(history_message):
                emoji_counter += self._count_emojis_in_msg(
                    emojis, history_message
                )
        logger.debug(f'Finish counting in #{channel.name}...')

        return emoji_counter

    @staticmethod
    def _count_emojis_in_msg(emojis, message):
        """Count emojis in the message."""
        counter = Counter()
        for emoji in emojis:
            if emoji in message.content:
                counter[emoji] += 1
            if emoji in [str(reaction.emoji) for reaction in message.reactions]:
                counter[emoji] += 1
        return counter


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
