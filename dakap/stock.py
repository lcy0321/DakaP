"""Get market data from Yahoo! Finance's API"""

import logging
from collections.abc import Sequence

import discord
import yfinance

_ALIASES = {
    'COVER': '5253.t',
    'ANYCOLOR': '5032.t',
    'TRENDMICRO': '4704.t',
}

_logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


async def get_stocks_prices(
    _client: discord.Client,
    message: discord.Message,
    arguments: Sequence[str],
) -> None:
    """Get stocks prices from Yahoo! Finance's API"""
    if arguments[1:]:
        async with message.channel.typing():
            embeds = []
            # Discord only allows 10 embeds per message
            for arg in arguments[1:11]:
                try:
                    embeds.append(_get_discord_embed_for_stock_price(symbol=arg))
                except Exception:  # pylint: disable=broad-except
                    _logger.exception(f'Failed to get stock price for {arg}')

            if embeds:
                await message.reply(embeds=embeds)


def _get_discord_embed_for_stock_price(symbol: str) -> discord.Embed:
    try:
        actual_symbol = _ALIASES[symbol.upper()]
    except KeyError:
        actual_symbol = symbol

    ticker = yfinance.Ticker(ticker=actual_symbol)
    info = ticker.info
    # Work-around: https://github.com/ranaroussi/yfinance/issues/1636
    # fast_info = ticker.fast_info
    fast_info = ticker.get_fast_info

    name = info['longName']
    symbol = info['symbol']
    currency = info['currency']
    previous_close = info['previousClose']
    last_price = fast_info['lastPrice']

    delta = last_price - previous_close
    delta_percent = delta / previous_close * 100
    if delta > 0:
        delta_color = 0xFF0000
        description_prefix = '📈'
    elif delta < 0:
        delta_color = 0x137333
        description_prefix = '📉'
    else:
        delta_color = 0x777777
        description_prefix = ''

    embed = discord.Embed(
        title=f'{name} ({symbol})',
        url=f'https://finance.yahoo.com/quote/{symbol}',
        description=(
            description_prefix
            + f' {currency} {last_price:,.2f} ({delta:+,.2f}) ({delta_percent:+.2f}%)'
        ),
        color=delta_color,
    )
    return embed
