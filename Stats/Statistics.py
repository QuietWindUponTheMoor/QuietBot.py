import discord
from Utils.DB import insert, select, validateSelect
from Utils.Embeds import createEmbed
from Utils.UnixTimestamp import getUnixTimestamp

class StatisticsHelpers:
    def getElapsedTimes(seconds: int):
        # Define time unit conversions
        SECONDS_IN_A_MINUTE = 60
        SECONDS_IN_AN_HOUR = 60 * SECONDS_IN_A_MINUTE
        SECONDS_IN_A_DAY = 24 * SECONDS_IN_AN_HOUR
        SECONDS_IN_A_WEEK = 7 * SECONDS_IN_A_DAY
        SECONDS_IN_A_MONTH = 30 * SECONDS_IN_A_DAY
        SECONDS_IN_A_YEAR = 365 * SECONDS_IN_A_DAY

        # Calculate each unit, starting from largest to smallest
        years = seconds // SECONDS_IN_A_YEAR
        seconds %= SECONDS_IN_A_YEAR
        
        months = seconds // SECONDS_IN_A_MONTH
        seconds %= SECONDS_IN_A_MONTH
        
        weeks = seconds // SECONDS_IN_A_WEEK
        seconds %= SECONDS_IN_A_WEEK
        
        days = seconds // SECONDS_IN_A_DAY
        seconds %= SECONDS_IN_A_DAY
        
        hours = seconds // SECONDS_IN_AN_HOUR
        seconds %= SECONDS_IN_AN_HOUR
        
        minutes = seconds // SECONDS_IN_A_MINUTE
        seconds %= SECONDS_IN_A_MINUTE
        
        # The remaining seconds
        return years, months, weeks, days, hours, minutes, seconds

    async def deletedMessageBySelf(self, message):
        """
        Checks that the person that deleted the message, also authored that message.
        """

        # Get the guild
        guild = message.guild

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
            # entry will contain the action taken and the user who took it
            if entry.target.id == message.author.id:
                return True
            else:
                return False
            
    async def guildIDFromInteraction(interaction: discord.Interaction):
        return interaction.guild_id
    
    async def userIDFromInteraction(interaction: discord.Interaction):
        return interaction.user.id
            
class StatisticsView(StatisticsHelpers):
    @staticmethod
    async def viewUserStats(interaction: discord.Interaction):
        # Get the guildID & the memberID
        guildID = await StatisticsHelpers.guildIDFromInteraction(interaction)
        memberID = await StatisticsHelpers.userIDFromInteraction(interaction)

        # Fetch data
        result = await select("SELECT * FROM statistics WHERE guildID=%s AND memberID=%s;", (guildID, memberID))
        data = await validateSelect(result)
        if not data:
            await interaction.response.send_message(f"# OOPS! \nSorry, but a member with ID '{memberID}' for guild '{guildID}' could not be found. Please try again, or contact the bot developer.", ephemeral=True)
            return False
        
        # Define data points
        data = data[0]
        totalPoints = data[2]
        msgsSent = data[3]
        msgsDeleted = data[4]
        timesMentioned = data[5]
        reactions = data[6]
        timeInVC = data[7] # In Seconds
        timeStreaming = data[8] # In Seconds
        membersInvited = data[9]

        # Process data
        # Time elapsed
        years, months, weeks, days, hours, minutes, seconds = StatisticsHelpers.getElapsedTimes(timeInVC) # Get time in VC
        timeInVC = f"{years} years, {months} months, {weeks} weeks, {days} days, {hours} hours, {minutes} minutes, & {seconds} seconds"
        years, months, weeks, days, hours, minutes, seconds = StatisticsHelpers.getElapsedTimes(timeStreaming) # Get time streaming
        timeStreaming = f"{years} years, {months} months, {weeks} weeks, {days} days, {hours} hours, {minutes} minutes, & {seconds} seconds"
        # Messages
        activeMsgs = msgsSent - msgsDeleted

        # Create embed
        embed = await createEmbed(title="Your Stats", descr="Here are your stats for this server!", color=discord.Color.green())
        embed.add_field(name="Total Points", value=totalPoints, inline=True)
        embed.add_field(name="Messages Sent", value=msgsSent, inline=True)
        embed.add_field(name="Messages Deleted", value=msgsDeleted, inline=True)
        embed.add_field(name="Active Messages", value=activeMsgs, inline=True)
        embed.add_field(name="Times Mentioned", value=timesMentioned, inline=True)
        embed.add_field(name="Reactions Made", value=reactions, inline=True)
        embed.add_field(name="Members Invited", value=membersInvited, inline=True)
        embed.add_field(name="Time In Voice Chat", value=timeInVC, inline=False)
        embed.add_field(name="Time Streaming", value=timeStreaming, inline=False)

        # Reply
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def viewServerStats(interaction: discord.Interaction):
        # Get the guildID & the memberID
        guildID = await StatisticsHelpers.guildIDFromInteraction(interaction)
        memberID = await StatisticsHelpers.userIDFromInteraction(interaction)

        # Fetch data
        result = await select("""
            SELECT
                COUNT(memberID) as membersCount,
                SUM(points) as totalPoints,
                SUM(messagesSent) as msgsSent,
                SUM(messagesDeleted) as msgsDeleted,
                SUM(timesMentioned) as totalMentions,
                SUM(reactions) as totalReactions,
                SUM(timeInVC) as totalTimeInVC,
                SUM(timeStreaming) as totalTimeStreaming,
                SUM(membersInvited) as totalMembersInvited
            FROM statistics WHERE guildID=%s;
        """, (guildID,))
        data = await validateSelect(result)
        if not data:
            await interaction.response.send_message(f"# OOPS! \nSorry, but a guild with ID '{guildID}' could not be found. Please try again, or contact the bot developer.", ephemeral=True)
            return False
        
        # Define data points
        data = data[0]
        totalMembers = data[0]
        totalPoints = data[1]
        msgsSent = data[2]
        msgsDeleted = data[3]
        timesMentioned = data[4]
        reactions = data[5]
        timeInVC = data[6] # In Seconds
        timeStreaming = data[7] # In Seconds
        membersInvited = data[8]

        # Process data
        # Time elapsed
        years, months, weeks, days, hours, minutes, seconds = StatisticsHelpers.getElapsedTimes(timeInVC) # Get time in VC
        timeInVC = f"{years} years, {months} months, {weeks} weeks, {days} days, {hours} hours, {minutes} minutes, & {seconds} seconds"
        years, months, weeks, days, hours, minutes, seconds = StatisticsHelpers.getElapsedTimes(timeStreaming) # Get time streaming
        timeStreaming = f"{years} years, {months} months, {weeks} weeks, {days} days, {hours} hours, {minutes} minutes, & {seconds} seconds"
        # Messages
        activeMsgs = msgsSent - msgsDeleted

        # Create embed
        embed = await createEmbed(title="Server All Time Stats", descr="Here are the lifetime stats for this server!", color=discord.Color.green())
        embed.add_field(name="Members", value=totalMembers, inline=True)
        embed.add_field(name="Total Points", value=totalPoints, inline=True)
        embed.add_field(name="Messages Sent", value=msgsSent, inline=True)
        embed.add_field(name="Messages Deleted", value=msgsDeleted, inline=True)
        embed.add_field(name="Active Messages", value=activeMsgs, inline=True)
        embed.add_field(name="Total Mentions", value=timesMentioned, inline=True)
        embed.add_field(name="Reactions Made", value=reactions, inline=True)
        embed.add_field(name="Time In Voice Chat", value=timeInVC, inline=False)
        embed.add_field(name="Time Streaming", value=timeStreaming, inline=False)
        embed.add_field(name="Members Invited", value=membersInvited, inline=True)

        # Reply
        await interaction.response.send_message(embed=embed, ephemeral=False)

class Statistics(StatisticsView):
    # STATS TO TRACK:
    # points-
    # messagesSent-
    # messagesDeleted-
    # timesMentioned-
    # reactions-
    # timeInVC (seconds)
    # timeStreaming (seconds)
    # membersInvited-

    def __init__(self, bot):
        self.bot = bot
        self.pointsPerMessage = 1
        self.pointsPerReaction = 2
        self.pointsPerMention = 5
        self.pointsPerInvitedMember = 20

    async def changePoints(self, pointsType="msg", addRemove="+", guildID=None, memberID=None):
        # Init modifier
        modifier = 0

        # Get type
        if pointsType == "msg": modifier = self.pointsPerMessage
        elif pointsType == "react": modifier = self.pointsPerReaction
        elif pointsType == "mention": modifier = self.pointsPerMention
        elif pointsType == "invite": modifier = self.pointsPerInvitedMember

        # Get add or remove
        if addRemove == "+":
            # Insert into database
            await insert("INSERT INTO statistics (guildID, memberID, points) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE points=points+%s;", (guildID, memberID, modifier, modifier))
        elif addRemove == "-":
            # Insert into database
            await insert("INSERT INTO statistics (guildID, memberID, points) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE points=points-%s;", (guildID, memberID, -modifier, modifier))

    async def incrementMemberInvites(self, member):
        # Get the guildID & memberID
        guild = member.guild
        guildID = guild.id
        inviterMemberID = None

        # Check the audit logs
        async for entry in guild.audit_logs(limit=15, action=discord.AuditLogAction.invite_use): # Limit of 15, in the case of lots of activity in the server
            if entry.target.id == member.id:
                inviterMemberID = entry.user.id

                # Insert into database
                await insert("INSERT INTO statistics (guildID, memberID, membersInvited) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE membersInvited=membersInvited+1;", (guildID, inviterMemberID))
                await self.changePoints(pointsType="invite", addRemove="+", guildID=guildID, memberID=inviterMemberID)
                break

    async def addReact(self, payload):
        # Get the guildID & the memberID
        guildID = payload.guild_id
        memberID = payload.user_id

        # Insert into database
        await insert("INSERT INTO statistics (guildID, memberID, reactions) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE reactions=reactions+1;", (guildID, memberID))
        await self.changePoints(pointsType="react", addRemove="+", guildID=guildID, memberID=memberID)

    async def removeReact(self, payload):
        # Get the guildID & the memberID
        guildID = payload.guild_id
        memberID = payload.user_id

        # Insert into database
        await insert("INSERT INTO statistics (guildID, memberID, reactions) VALUES (%s, %s, -1) ON DUPLICATE KEY UPDATE reactions=reactions-1;", (guildID, memberID))
        await self.changePoints(pointsType="react", addRemove="-", guildID=guildID, memberID=memberID)

    async def addMention(self, message):
        # Get the guildID & the memberID
        guildID = message.guild.id
        memberID = message.author.id

        # Check if it's a mention
        mentionedByUserID = None
        mentionedUserID = None
        if len(message.mentions) > 0:
            mentionedByUserID = memberID
            for mentionedUser in message.mentions:
                mentionedUserID = mentionedUser.id
        else:
            # Return, because the message isn't a valid mention
            return
        
        # Insert into database
        await insert("INSERT INTO statistics (guildID, memberID, timesMentioned) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE timesMentioned=timesMentioned+1;", (guildID, mentionedUserID))
        await self.changePoints(pointsType="mention", addRemove="+", guildID=guildID, memberID=memberID)
    
    async def addMessage(self, message):
        # Get the message info
        guildID = message.guild.id
        memberID = message.author.id
        messageID = message.id
        messageContent = message.content

        # Get unix timestamp
        unix = getUnixTimestamp()

        # Insert into database
        await insert("INSERT INTO statistics (guildID, memberID, messagesSent) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE messagesSent=messagesSent+1;", (guildID, memberID))
        await insert("INSERT INTO messages (guildID, memberID, messageID, unixTimestamp, content) VALUES (%s, %s, %s, %s, %s);", (guildID, memberID, messageID, unix, messageContent))
        await self.changePoints(pointsType="msg", addRemove="+", guildID=guildID, memberID=memberID)

    async def removeMessage(self, message):
        # Get the message info
        guildID = message.guild.id
        memberID = message.author.id
        messageID = message.id

        # Get unix timestamp
        unix = getUnixTimestamp()

        # Edit message record & return if the deleted message was not created by the deleter
        if not await self.deletedMessageBySelf(message):
            await insert("UPDATE messages SET active=FALSE, deleterID=%s, deletedUnixTimestamp=%s WHERE guildID=%s AND messageID=%s;", (memberID, unix, guildID, messageID))
            return

        # Insert into database
        await insert("INSERT INTO statistics (guildID, memberID, messagesSent) VALUES (%s, %s, -1) ON DUPLICATE KEY UPDATE messagesSent=messagesSent-1;", (guildID, memberID))
        await self.changePoints(pointsType="msg", addRemove="-", guildID=guildID, memberID=memberID)