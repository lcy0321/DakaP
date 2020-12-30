"""Count the emojis in the guild"""

import asyncio
import logging
from collections import Counter as counter
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from operator import itemgetter
from typing import Counter, Iterable, Iterator, NamedTuple, Tuple, TypeVar

import discord
from discord.channel import TextChannel
from discord.guild import Guild

from .common import is_msg_from_this_bot

logger = logging.getLogger(__name__)    # pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)


class EmojiCountResult(NamedTuple):
    """EmojiCountResult"""
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
        guild: Guild,
        channel: TextChannel,
) -> None:
    """Count the emojis in the guild."""

    async with channel.typing():

        emojis = [str(emoji) for emoji in guild.emojis]
        emoji_counter = counter(emojis)     # A counter contains all the emojis and starts from 1

        # discord library expects a timezone-naive datetime
        start_time = datetime.utcnow() - timedelta(weeks=12)

        counting_tasks = [
            asyncio.create_task(_count_emojis_in_channel(
                guild=guild,
                channel=target_channel,
                emojis=emojis,
                after=start_time,
            ))
            for target_channel in guild.text_channels
            if target_channel.permissions_for(guild.me).read_message_history
        ]

        # Get a tuple for all the message_count and a tuple for all the emoji_counter
        counting_results: Tuple[Tuple[int, ...], Tuple[Counter[str], ...]] = (
            *zip(*[await task for task in counting_tasks]),         # type: ignore
        )
        message_counts, emoji_counters = counting_results

        message_count = sum(message_counts)
        emoji_counter = sum(emoji_counters, emoji_counter)

        emoji_count_strs = [
            f'{emoji}: {count - 1 :3}'
            for emoji, count in sorted(emoji_counter.items(), key=itemgetter(1), reverse=True)
        ]

        if logger.isEnabledFor(logging.DEBUG):
            for emoji_count in emoji_count_strs:
                logger.debug(emoji_count)

        # Counted from <UTC+8 datetime>
        tw_timezone = timezone(offset=timedelta(hours=8))
        start_tw_time = start_time.replace(tzinfo=timezone.utc).astimezone(tz=tw_timezone)
        message_lines = (
            [(
                f'Counted from {start_tw_time.isoformat(sep=" ", timespec="seconds")}, '
                f'{message_count} messages have been processed:'
            )]
            + ['\t'.join(column) for column in grouper(emoji_count_strs, number=10, fillvalue='')]
        )

        for message_line in message_lines:
            await channel.send(message_line)


async def _count_emojis_in_channel(
        guild: Guild,
        channel: discord.TextChannel,
        emojis: Iterable[discord.Emoji],
        after: datetime,
) -> EmojiCountResult:
    """Count emojis in the messages in the channel."""

    emoji_counter: Counter[discord.Emoji] = counter()
    message_count = 0

    logger.debug(f'Start counting in #{channel.name}...')

    async for history_message in channel.history(limit=None, after=after):
        if not is_msg_from_this_bot(guild=guild, message=history_message):
            message_count += 1
            emoji_counter += _count_emojis_in_msg(
                emojis=emojis,
                message=history_message,
            )
    logger.debug(f'Finish counting {message_count} message(s) in #{channel.name}...')

    return EmojiCountResult(message_count=message_count, emoji_counter=emoji_counter)


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
