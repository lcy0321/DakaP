""""Reply the thumnail image URL for the given YouTuve URL."""

import base64
import re
import struct
from datetime import datetime, timezone
from typing import Sequence

import discord


async def reply_youtube_thumbnail(
        _client: discord.Client,
        message: discord.Message,
        arguments: Sequence[str],
) -> None:
    """Reply with the latest YouTube thumbnail"""
    try:
        yt_url = arguments[1]
    except KeyError:
        return

    try:
        await message.reply(
            parse_and_generate_youtube_thumbnail_url(yt_url=yt_url)
        )
    except ValueError:
        pass


def parse_and_generate_youtube_thumbnail_url(yt_url: str) -> str:
    # pattern from:
    #   https://stackoverflow.com/questions/3452546/how-do-i-get-the-youtube-video-id-from-a-url#comment80849763_27728417
    if matched := re.fullmatch(
        r'^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]+).*',
        yt_url,
    ):
        return _generate_youtube_thumbnail_url(youtube_video_id=matched.groups()[0])
    raise ValueError()


def _generate_youtube_thumbnail_url(youtube_video_id: str) -> str:
    unique_str = _generate_unique_str_from_current_time()
    return f'https://i.ytimg.com/vi/{youtube_video_id}/maxresdefault.jpg?v={unique_str}'


def _generate_unique_str_from_current_time() -> str:
    """Get bytes format of the current time, and encoded with base64."""
    return base64.urlsafe_b64encode(
        struct.pack(
            '!I',
            int(datetime.now(tz=timezone.utc).timestamp()),
        ).lstrip()
    ).decode()[:-2]  # remove the trailing `==`
