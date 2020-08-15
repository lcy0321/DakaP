"""Count the emojis in the guild"""

import asyncio
import logging
from collections import Counter as counter
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from operator import itemgetter
from typing import Counter, Iterable, Iterator, List, Tuple, TypeVar

import discord

from .common import is_msg_from_me

logger = logging.getLogger(__name__)    # pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)


T = TypeVar('T')    # pylint: disable=invalid-name


def grouper(iterable: Iterable[T], number: int, fillvalue: T = None) -> Iterator[Tuple[T]]:
    """
    From https://docs.python.org/3/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * number
    return zip_longest(*args, fillvalue=fillvalue)


async def count_emojis(
        client: discord.Client,
        message: discord.Message,
        _arguments
) -> None:
    """Count the emojis in the guild."""

    with message.channel.typing():

        emojis = [str(emoji) for emoji in message.guild.emojis]
        emoji_counter = counter(emojis)     # Counter starts from 1

        # discord library expects a timezone-naive datetime
        start_time = datetime.utcnow() - timedelta(weeks=12)

        counting_tasks = []

        for channel in message.guild.channels:
            if isinstance(channel, discord.TextChannel) and \
                    message.guild.me.permissions_in(channel).read_message_history:

                counting_tasks.append(asyncio.create_task(
                    _count_emojis_in_channel(client, channel, emojis, after=start_time)
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
        tw_timezone = timezone(offset=timedelta(hours=8))
        start_tw_time = start_time.replace(tzinfo=timezone.utc).astimezone(tz=tw_timezone)
        message_lines = (
            [(
                f'Counted from {start_tw_time.isoformat(sep=" ", timespec="seconds")}'
            )]
            + ['\t'.join(column) for column in grouper(result, number=10, fillvalue='')]
        )

        for message_line in message_lines:
            await message.channel.send(message_line)


async def _count_emojis_in_channel(
        client: discord.Client,
        channel: discord.TextChannel,
        emojis: List[discord.Emoji],
        after: datetime,
) -> Counter[str]:
    """Count emojis in the messages in the channel."""
    emoji_counter: Counter[discord.Emoji] = counter()
    msg_count = 0

    logger.debug(f'Start counting in #{channel.name}...')

    async for history_message in channel.history(limit=None, after=after):
        if not is_msg_from_me(client, history_message):
            msg_count += 1
            emoji_counter += _count_emojis_in_msg(
                emojis, history_message
            )
    logger.debug(f'Finish counting {msg_count} message(s) in #{channel.name}...')

    return emoji_counter


def _count_emojis_in_msg(
        emojis: Iterable[discord.Emoji], message: discord.Message
) -> Counter[discord.Emoji]:
    """Count emojis in the message."""
    emoji_counter: Counter[discord.Emoji] = counter()
    for emoji in emojis:
        if emoji in message.content:
            emoji_counter[emoji] += 1
        if emoji in [str(reaction.emoji) for reaction in message.reactions]:
            emoji_counter[emoji] += 1
    return emoji_counter
