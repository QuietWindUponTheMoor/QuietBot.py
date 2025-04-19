import discord
from Utils.DB import select, validateSelect
from Utils.Embeds import createEmbed
from Utils.UnixTimestamp import getUnixTimestamp

class ModAlerts:

    def __init__(self, bot):
        self.bot = bot

    # "private" methods
    async def getAlertChannelID(self, guildID) -> bool:
        """
        :return: Returns a tuple with bool specifying if the channelID could be fetched [0] and the response [1]
        :rtype: tuple(bool, string|int)
        """
        result = await select("SELECT * FROM modalertschannel WHERE guildID=%s;", (guildID,))
        data = await validateSelect(result)
        if not data:
            return (False, "There is no alert channel set. Please set one using /modalerts")
        else:
            return (True, int(data[0][1]))
        
    async def getChannelByID(self, channelID):
        return await self.bot.fetch_channel(channelID)
    
    async def sendToAlertChannel(self, channel, embed):
        await channel.send(embed=embed)

    # "public" methods
    async def msgCreate(self, message):
        # Get data
        guildID = message.guild.id if message.guild else None
        messageContent = message.content
        memberID = message.author.id
        
        # Get unix timestamp
        unix = getUnixTimestamp()

        # Fetch channelID
        ableToBeFetched, channelID = await self.getAlertChannelID(guildID)
        if not ableToBeFetched:
            return
        
        # Fetch channel
        channel = await self.getChannelByID(channelID)
        
        # Send to alerts channel
        embed = await createEmbed(title="New Message!", descr=None, color=discord.Color.green())
        embed.add_field(name="Member", value=f"<@{memberID}>", inline=True)
        embed.add_field(name="Channel", value=f"{message.channel.mention}", inline=True)
        embed.add_field(name="UnixTimestamp", value=unix, inline=False)
        embed.add_field(name="Message", value=messageContent, inline=False)

        # Send
        await self.sendToAlertChannel(channel, embed)

    async def msgDelete(self, message):
        # Get data
        guildID = message.guild.id if message.guild else None
        messageContent = message.content
        memberID = message.author.id
        
        # Get unix timestamp
        unix = getUnixTimestamp()

        # Fetch channelID
        ableToBeFetched, channelID = await self.getAlertChannelID(guildID)
        if not ableToBeFetched:
            print(f"Could not fetch channelID for messageID {message.id}")
            return
        
        # Fetch channel
        channel = await self.getChannelByID(channelID)
        
        # Send to alerts channel
        embed = await createEmbed(title="A Message Was Deleted!", descr=None, color=discord.Color.red())
        embed.add_field(name="Member", value=f"<@{memberID}>", inline=True)
        embed.add_field(name="Channel", value=f"{message.channel.mention}", inline=True)
        embed.add_field(name="UnixTimestamp", value=unix, inline=False)
        embed.add_field(name="Message", value=messageContent, inline=False)

        # Send
        await self.sendToAlertChannel(channel, embed)

    async def msgEdit(self, message):
        # Get data
        guildID = message.guild.id if message.guild else None
        messageContent = message.content
        memberID = message.author.id
        messageID = message.id
        
        # Get unix timestamp
        unix = getUnixTimestamp()

        # Fetch channelID
        ableToBeFetched, channelID = await self.getAlertChannelID(guildID)
        if not ableToBeFetched:
            return
        
        # Fetch channel
        channel = await self.getChannelByID(channelID)

        # Fetch old message
        result = await select("SELECT content FROM messages WHERE guildID=%s AND messageID=%s;", (guildID, messageID))
        oldMsg = await validateSelect(result)
        if not oldMsg[0][0]:
            return
        oldMsg = oldMsg[0][0]
        
        # Send to alerts channel
        embed = await createEmbed(title="A Message Was Edited!", descr=None, color=discord.Color.yellow())
        embed.add_field(name="Member", value=f"<@{memberID}>", inline=True)
        embed.add_field(name="Channel", value=f"{message.channel.mention}", inline=True)
        embed.add_field(name="UnixTimestamp", value=unix, inline=False)
        embed.add_field(name="Old Message", value=oldMsg, inline=False)
        embed.add_field(name="New Message", value=messageContent, inline=False)

        # Send
        await self.sendToAlertChannel(channel, embed)