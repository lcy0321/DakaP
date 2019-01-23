"""A bot to count the emojis in the guild."""

from collections import Counter
from itertools import zip_longest

import discord


def grouper(iterable, number, fillvalue=None):
    """
    From https://docs.python.org/3/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * number
    return zip_longest(*args, fillvalue=fillvalue)


class DakaP(discord.Client):
    """A bot to count the emojis in the guild."""

    prefix = '$ '
    history_limit = 10

    async def on_ready(self):
        """Triggered when ready."""
        print(f'Username: {self.user.name}')
        print(f'ID: {self.user.id}')

    async def on_message(self, message):
        """Triggered when a message start with specific prefix"""

        if self.is_msg_from_me(message):
            return

        if message.content.startswith(self.prefix):
            command = message.content.replace(self.prefix, '').strip()

            print(f'{message.guild}-{message.channel}: {command}')

            if command == 'bye':
                await self.logout()

            elif command == 'emoji':

                emojis = [str(emoji) for emoji in message.guild.emojis]

                for channel in message.guild.channels:
                    if isinstance(channel, discord.TextChannel) and \
                            message.guild.me.permissions_in(channel).read_message_history:

                        emoji_counter = await self.count_emoji_in_channel(emojis, channel)

                        result = []
                        for emoji, count in emoji_counter.items():
                            result.append(f'{emoji}: {count - 1 :3}')

                        await message.channel.send(
                            '\n'.join(
                                [f'Channel: {channel.mention}']
                                + ['\t'.join(column) for column in grouper(
                                    result, self.history_limit, fillvalue=''
                                )]
                            )
                        )

            elif command == 'clean':
                await message.channel.purge(check=self.is_msg_from_me)

    def is_msg_from_me(self, msg):
        """Check if the message is sent by this bot."""
        return msg.author.id == self.user.id

    async def count_emoji_in_channel(self, emojis, channel):
        """Count emojis in the messages in the channel.
           The counters start at 1.
        """
        emoji_counter = Counter(emojis)

        async for history_message in channel.history(limit=5000):
            if not self.is_msg_from_me(history_message):
                emoji_counter += self.count_emoji_in_msg(
                    emojis, history_message.content
                )

        return emoji_counter

    @staticmethod
    def count_emoji_in_msg(emojis, message_content):
        """Count emojis in the message."""
        counter = Counter()
        for emoji in emojis:
            if emoji in message_content:
                counter[emoji] += 1
        return counter


def main():
    """Run the bot with the token."""
    with open('bot-token') as token_file:
        token = token_file.read().strip()
    client = DakaP()
    client.run(token)


if __name__ == "__main__":
    main()
