import discord

async def createEmbed(title, descr, color: discord.Color):
    return discord.Embed(
        title=title,
        description=descr,
        color=color
    )