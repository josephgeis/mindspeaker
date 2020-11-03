from discord.ext.commands import Bot
import discord.ext.commands as commands
import discord
import config
import re


class MindspeakerBot(Bot):
    async def init_verification_channels(self):
        """
        Initializes #verify channels (or similar).
        """

        self.verification = dict()
        for chan, role in config.VERIFICATION_CHANNELS:
            channel = self.get_channel(chan)
            async with channel.typing():
                await channel.purge(limit=None, check=None)
                message: discord.Message = await channel.send("By reacting to this message, you agree to abide by this server's rules")
                await message.add_reaction(u"\u2705")
                self.verification[message.id] = role

    async def on_ready(self):
        print(f"Connected to Discord as {self.user}.")

        # initialize verification channel
        await self.init_verification_channels()

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        """
        Handles reactions added. Only for #verify channels rn.
        """

        if user.id == self.user.id:
            return

        message: discord.Message = reaction.message
        if message.id in self.verification.keys():
            role_id = self.verification[message.id]
            role = message.guild.get_role(role_id)
            await user.add_roles(role)
            await reaction.remove(user)

    async def on_raw_message_delete(self, payload):
        if payload.message_id in self.verification.keys():
            print("Warning: verification message deleted.")


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

    async with channel.typing():
        await channel.purge(limit=None, check=None)

    await ctx.send("Channel nuked!\nhttps://media.giphy.com/media/oe33xf3B50fsc/giphy.gif", delete_after=3)

if __name__ == '__main__':
    bot.run(config.TOKEN)
