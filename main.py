import requests
from discord.ext.commands import Bot
import discord.ext.commands as commands
import discord
import config
import re
from datetime import datetime as dt


class MindspeakerBot(Bot):
    async def init_verification_channels(self):
        """
        Initializes #verify channels (or similar).
        """

        for chan, role in config.VERIFICATION_CHANNELS:
            channel = self.get_channel(chan)
            async with channel.typing():
                await channel.purge(limit=None, check=None)
                message: discord.Message = await channel.send(
                    "By reacting to this message, you agree to abide by this server's rules")
                await message.add_reaction(u"\u2705")
                self.verification_assignments[message.id] = role

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
        if message.id in self.verification_assignments.keys():
            role_id = self.verification_assignments[message.id]
            role = message.guild.get_role(role_id)
            await user.add_roles(role, reason=dt.now().strftime("Accepted rules on %m/%d/%Y at %X."))
            await reaction.remove(user)

    async def on_raw_message_delete(self, payload):
        if payload.message_id in self.verification_assignments.keys():
            print("Warning: verification message deleted.")

    def __init__(self, *args, **kwargs):
        super(MindspeakerBot, self).__init__(*args, **kwargs)
        self.verification_assignments = dict()


bot = MindspeakerBot(config.PREFIX)


async def is_elevated(ctx) -> bool:
    return {role.id for role in ctx.author.roles}.intersection(set(config.ELEVATED_ROLES))


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
@commands.check(is_elevated)
async def nuke(ctx: commands.Context, channel_arg=None):
    channel_id = None
    channel = None
    if channel_arg is not None:
        match = re.match(r"\<#(\w*)\>", channel_arg)
        if match:
            channel_id = int(match.group(1))
            channel = ctx.guild.get_channel(channel_id)
        else:
            return
    else:
        channel = ctx.message.channel

    if channel is None:
        return

    async with channel.typing():
        await channel.purge(limit=None, check=lambda m: m != ctx.message)

    await ctx.message.delete(delay=3)
    await ctx.send(
        f"Channel {channel_arg if channel != ctx.message.channel else ''}nuked!\nhttps://media.giphy.com/media/oe33xf3B50fsc/giphy.gif",
        delete_after=3)


@bot.command()
async def vote(ctx: commands.Context, state: str = None):
    async with ctx.message.channel.typing():
        data: list = requests.get(
            "https://politics-elex-results.data.api.cnn.io/results/view/2020-national-races-PG.json").json()
        state_data = [ss for ss in data if ss.get("stateAbbreviation") == state.upper()]

    if state_data:
        state_data = state_data[0]
    else:
        await ctx.send("No data found")
        return

    async with ctx.message.channel.typing():
        candidates = [
            "{emoji} {name} - {num} ({pct}%){check}".format(
                emoji={"REP": ":red_circle:", "DEM": ":blue_circle:"}.get(candidate.get("majorParty"), ":black_circle"),
                name=candidate.get("fullName"),
                num=candidate.get("voteStr"),
                pct=candidate.get("votePercentStr"),
                check=" :white_check_mark:" if candidate.get("winner", False) else ""
            )
            for candidate in state_data.get("candidates", [])
        ]

        lines = ["**__Presidential Election Update__**",
                 "**{state_name}** ({pct_votes}% reporting)".format(state_name=state_data.get("stateName"),
                                                                    pct_votes=state_data.get("percentReporting")),
                 *candidates]

    await ctx.send(
        "\n".join(lines)
    )


if __name__ == '__main__':
    bot.run(config.TOKEN)
