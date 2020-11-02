from discord.ext.commands import Bot
import discord.ext.commands as commands
import config
import re


class MindspeakerBot(Bot):
    async def on_ready(self):
        print(f"Connected to Discord as {self.user}.")


bot = MindspeakerBot(config.PREFIX)


async def is_elevated(ctx) -> bool:
    return {role.id for role in ctx.author.roles}.intersection(set(config.ELEVATED_ROLES))


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
@commands.check(is_elevated)
async def nuke(ctx, channel_arg=None):
    channel_id = None
    channel = None
    if channel_arg is not None:
        match = re.match(r"\<#(\w*)\>", channel_arg)
        if match:
            channel_id = match.group(1)
            channel = ctx.guild.get_channel(channel_id)
        else:
            return
    else:
        channel = ctx.message.channel

    if channel is None:
        return

    await channel.purge(limit=None, check=None)

    await ctx.send("Channel nuked!\nhttps://media.giphy.com/media/oe33xf3B50fsc/giphy.gif", delete_after=3)

if __name__ == '__main__':
    bot.run(config.TOKEN)
