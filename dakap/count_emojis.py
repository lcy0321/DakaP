"""Count the emojis in the guild"""

import asyncio
import logging
import unicodedata
from collections import Counter as counter
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from operator import attrgetter, itemgetter
from typing import (Collection, Counter, Iterable, Iterator, NamedTuple, Tuple,
                    TypeVar)

import discord

from .common import is_msg_from_me

logger = logging.getLogger(__name__)    # pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)


class EmojiCountResult(NamedTuple):
    channel_name: str
    message_count: int
    emoji_counter: Counter[str]


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
        _arguments,
) -> None:
    """Count the emojis in the guild."""

    with message.channel.typing():

        emojis = [str(emoji) for emoji in message.guild.emojis]
        emoji_counter = counter(emojis)     # A counter contains all the emojis and starts from 1

        # discord library expects a timezone-naive datetime
        start_time = datetime.utcnow() - timedelta(weeks=12)

        counting_tasks = [
            asyncio.create_task(_count_emojis_in_channel(
                client=client,
                channel=channel,
                emojis=emojis,
                after=start_time,
            ))
            for channel in message.guild.text_channels + message.guild.threads
            if channel.permissions_for(channel.guild.me).read_message_history
        ]

        counting_results: list[EmojiCountResult] = [await task for task in counting_tasks]
        emoji_counter = sum((result.emoji_counter for result in counting_results), emoji_counter)

        await _send_emoji_count_summary(
            emoji_count_results=counting_results,
            start_time=start_time,
            channel_to_send=message.channel,
        )
        await _send_emoji_count_result(
            emoji_counter=emoji_counter,
            channel_to_send=message.channel,
        )


async def _count_emojis_in_channel(
        client: discord.Client,
        channel: discord.abc.Messageable,
        emojis: Iterable[discord.Emoji],
        after: datetime,
) -> EmojiCountResult:
    """Count emojis in the messages in the channel."""

    emoji_counter: Counter[discord.Emoji] = counter()
    message_count = 0

    logger.debug(f'Start counting in #{channel.name}...')

    async for history_message in channel.history(limit=None, after=after):
        if not is_msg_from_me(client, history_message):
            message_count += 1
            emoji_counter += _count_emojis_in_msg(
                emojis=emojis,
                message=history_message,
            )
    logger.debug(f'Finish counting {message_count} message(s) in #{channel.name}...')

    return EmojiCountResult(
        channel_name=channel.name,
        message_count=message_count,
        emoji_counter=emoji_counter,
    )


def _count_emojis_in_msg(
        emojis: Iterable[discord.Emoji],
        message: discord.Message,
) -> Counter[discord.Emoji]:
    """Count emojis in the message."""
    emoji_counter: Counter[discord.Emoji] = counter()
    for emoji in emojis:
        if emoji in message.content:
            emoji_counter[emoji] += 1
        if emoji in [str(reaction.emoji) for reaction in message.reactions]:
            emoji_counter[emoji] += 1
    return emoji_counter


async def _send_emoji_count_summary(
    emoji_count_results: Collection[EmojiCountResult],
    start_time: datetime,
    channel_to_send: discord.abc.Messageable,
) -> None:
    message_lines = []

    # Counted from <UTC+8 datetime>
    start_tw_time = start_time.replace(tzinfo=timezone.utc).astimezone(
        tz=timezone(offset=timedelta(hours=8))
    )

    # Starting time of counting and the sum of the counts
    all_message_count = sum(result.message_count for result in emoji_count_results)
    message_lines.append(
        f'Counted from {start_tw_time.isoformat(sep=" ", timespec="seconds")}, '
        f'{all_message_count} messages have been processed:'
    )

    # Message count from each channel
    message_lines += [
        (_cjk_ljust(f'From #{result.channel_name}:', 50) + f'{result.message_count} message(s)')
        for result in sorted(emoji_count_results, key=attrgetter('message_count'), reverse=True)
    ]

    message_lines = [
        '```',
        *message_lines,
        '```',
    ]

    await channel_to_send.send('\n'.join(message_lines))


async def _send_emoji_count_result(
    emoji_counter: Counter[str],
    channel_to_send: discord.abc.Messageable,
) -> None:

    emoji_count_strs = [
        f'{emoji}: {count - 1 :3}'
        for emoji, count in sorted(emoji_counter.items(), key=itemgetter(1), reverse=True)
    ]

    if logger.isEnabledFor(logging.DEBUG):
        for emoji_count in emoji_count_strs:
            logger.debug(emoji_count)

    # Counted from <UTC+8 datetime>
    message_lines = [
        '\t'.join(column)
        for column in grouper(emoji_count_strs, number=10, fillvalue='')
    ]

    for message_line in message_lines:
        await channel_to_send.send(message_line)


# a ljust() that treat CJK characters as double-width
def _cjk_ljust(string: str, width: int) -> str:
    def _width(char: str) -> int:
        # 'W': Wide
        # 'F': Fullwidth
        return 2 if unicodedata.east_asian_width(char) in 'WF' else 1

    str_len = sum(_width(char) for char in string)
    if str_len >= width:
        return string
    return string + ' ' * (width - str_len)
