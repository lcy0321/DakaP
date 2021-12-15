"""Get time in different time zones"""

from datetime import datetime
from typing import Sequence

import discord
from dateutil import parser
from dateutil.tz import UTC, gettz

# TIME_FORMAT = '%Y-%m-%d %I:%M:%S%p'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIMEZONE_NAMES = [
    'Asia/Taipei',
    'Asia/Tokyo',
    'America/New_York',
]
DEFAULT_TIMEZONE_NAME = 'Asia/Taipei'


async def get_time(
        _client: discord.Client,
        message: discord.Message,
        arguments: Sequence[str]
) -> None:
    """Get time in different time zones"""

    # Get the time we want to print (in UTC timezone)
    if len(arguments) == 1:
        # No specific time
        utc_time = _get_current_time()
    else:
        try:
            # Parse the arguments
            utc_time = _get_from_time(' '.join(arguments[1:]).upper())
        except parser.ParserError:      # type: ignore
            # Parse error
            await message.channel.send('```Parse Error```')
            return

    # `datetime`s in each timezone
    time_in_tzs = [utc_time.astimezone(gettz(timezone)) for timezone in TIMEZONE_NAMES]

    msg = []
    msg.append('```')
    # '<Timezone Name>: <Time String>'
    msg += [
        f'{time_in_tz.tzname()}: {time_in_tz.strftime(TIME_FORMAT)}'
        for time_in_tz in time_in_tzs
    ]
    msg.append('```')

    await message.channel.send('\n'.join(msg))


def _get_current_time() -> datetime:
    """Get current time"""
    return datetime.now(tz=UTC)


def _get_from_time(specific_time_str: str) -> datetime:
    """Get specific time from a string. May raise `parser.ParserError`"""

    # default datetime: Precise to the minutes with Asia/Taipei timezone
    default_dt = datetime.now(tz=gettz(DEFAULT_TIMEZONE_NAME)).replace(second=0, microsecond=0)

    def tzinfo_func(tzname: str, tzoffset: int):
        """Identify the timezone"""
        if tzoffset:
            return tzoffset

        iana_tz = gettz(tzname)
        if iana_tz:
            return iana_tz

        # Aliases
        if tzname in ['US', 'ET']:
            return gettz('America/New_York')
        if tzname in ['JP', 'JPN', 'JAPAN', 'JST']:
            return gettz('Asia/Tokyo')
        if tzname in ['TW', 'TWN', 'TAIPEI', 'TPE', 'NST', 'CST']:
            return gettz('Asia/Taipei')

        return gettz(DEFAULT_TIMEZONE_NAME)

    return parser.parse(specific_time_str, default=default_dt, tzinfos=tzinfo_func)
