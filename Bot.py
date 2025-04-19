import sys
import os
os.environ["SSL_CERT_FILE"] = os.path.join(os.path.dirname(__file__), "cacert.pem")
import discord
from discord import app_commands
from Utils.DynButtons import DynGroupsMenu
from Utils.EnvironmentVariables import env
from Utils.DB import createTable, insert, select, validateSelect
from Utils.Emojis import decodeEmoji
from Utils.UnixTimestamp import getUnixTimestamp
from Streams.Announcements import StreamAnnouncements
from Utils.CardFile import CardFile
from colorama import Fore, Style
from Stats.Statistics import Statistics, StatisticsView
from Fun.Cards.Standard52CardDeckRandDraw import Standard52CardDeckRandDraw
from Moderation.ModAlerts import ModAlerts
from Fun.Cards.Blackjack import Blackjack

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Bot & Command Tree
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Statistics init
Stats = Statistics(bot)

# ModAlerts init
Alerts = ModAlerts(bot)

# Blackjack
BlackJ = Blackjack(bot)

# -------------------------------------------------------------------------------------------------------------------------------------------
    
# HELPERS
def roleIDFromMention(mention: str):
    return mention.replace("@", "").replace("&", "").replace("<", "").replace(">", "").replace(" ", "")
async def isValidRole(roleID: str, interaction: discord.Interaction):
    # Cast roleID
    roleID = int(roleID)

    # Check validity
    role = interaction.guild.get_role(roleID)
    if role is not None:
        return True
    else:
        return False
async def interactionIsOwner(interaction: discord.Interaction):
    # Get userID, guildID, and the guild itself
    userID = await userIDFromInteraction(interaction)
    guildID = await guildIDFromInteraction(interaction)
    guild = await guildFromInteraction(interaction)

    # Compare guild owner user ID to userID
    if guild.owner_id == userID:
        return True
    else:
        await interaction.response.send_message(f"# OOPS! You are not the guild owner! \n### You cannot use this command!", ephemeral=True)
        print(f'{Fore.BLUE}INFO: A user tried creating a role group for guild {Fore.CYAN}{guildID}{Fore.BLUE} and they are not the owner. They have been told they cannot use this command.{Style.RESET_ALL}')
        return False
async def userIDFromInteraction(interaction: discord.Interaction):
    return interaction.user.id
async def guildFromInteraction(interaction: discord.Interaction):
    return interaction.guild
async def guildIDFromInteraction(interaction: discord.Interaction):
    return interaction.guild_id
async def userDM(userID, msg):
    # Get user object
    user = await bot.fetch_user(userID)

    try:
        await user.send(msg)
        print(f'{Fore.GREEN}DM Message Sent to user {Fore.CYAN}{userID}: {Fore.BLUE} "{msg}"{Style.RESET_ALL}')
        return True
    except discord.Forbidden:
        print(f'{Fore.YELLOW}WARNING: Could not send message to the user {Fore.CYAN}{userID}{Fore.YELLOW}!{Style.RESET_ALL}')
        return False
    except Exception as err:
        print(f'{Fore.YELLOW}WARNING: Could not send message to the user {Fore.CYAN}{userID}{Fore.YELLOW}: {err}{Style.RESET_ALL}')
async def createTables():
        print(f'{Fore.BLUE}INFO: Attempting to create table "guilds" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS guilds (
            guildID BIGINT PRIMARY KEY NOT NULL,
            ownerUserID BIGINT NOT NULL,
            ownerMemberID BIGINT NOT NULL
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "roleGroups" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS roleGroups (
            guildID BIGINT NOT NULL,
            name VARCHAR(32) PRIMARY KEY NOT NULL
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "roles" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS roles (
            roleID BIGINT PRIMARY KEY NOT NULL,
            groupName VARCHAR(32) NOT NULL,
            title VARCHAR(32) NOT NULL,
            descr VARCHAR(1200) NOT NULL,
            emoji VARCHAR(128) NOT NULL,
            guildID BIGINT NOT NULL
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "reactMsgs" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS reactMsgs (
            groupName VARCHAR(32) NOT NULL,
            msgID BIGINT PRIMARY KEY NOT NULL,
            roleID BIGINT NOT NULL,
            emoji VARCHAR(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
            guildID BIGINT NOT NULL,
            UNIQUE KEY unique_group_role (groupName, roleID) -- Unique key, doesn't show up in select queries
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "statistics" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS statistics (
            guildID BIGINT NOT NULL,
            memberID BIGINT NOT NULL,
            UNIQUE KEY uniqueMember (guildID, memberID), -- Unique key, doesn't show up in select queries
            points BIGINT DEFAULT 0,
            messagesSent BIGINT DEFAULT 0,
            messagesDeleted BIGINT DEFAULT 0,
            timesMentioned BIGINT DEFAULT 0,
            reactions BIGINT DEFAULT 0,
            timeInVC BIGINT DEFAULT 0, -- Time in seconds
            timeStreaming BIGINT DEFAULT 0, -- Time in seconds
            membersInvited BIGINT DEFAULT 0
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "messages" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS messages (
            guildID BIGINT NOT NULL,
            
            deleterID BIGINT DEFAULT NULL, -- If message was deleted, this is the memberID of the person that deleted it
            deletedUnixTimestamp BIGINT DEFAULT NULL, -- If message was deleted, the unix timestamp of deletion
            
            editorID BIGINT DEFAULT NULL, -- If message was edited, this is the memberID of the person that deleted it
            editedUnixTimestamp BIGINT DEFAULT NULL, -- If message was edited, the unix timestamp of edit
            
            active BOOL DEFAULT TRUE NOT NULL, -- Whether or not the message is active (not deleted) or not (deleted)
            edited BOOL DEFAULT FALSE NOT NULL, -- Whether or not the message has been edited
            
            memberID BIGINT NOT NULL,
            messageID BIGINT NOT NULL,
            unixTimestamp BIGINT NOT NULL,
            
            content TEXT NOT NULL,
            newContent TEXT DEFAULT NULL, -- If the message was edited, this is the new content of the message
            UNIQUE KEY uniqueKey (guildID, messageID) -- Unique key, doesn't show up in select queries
        );
        ''')
        print(f'{Fore.BLUE}INFO: Attempting to create table "modalertschannel" if not exists.{Style.RESET_ALL}')
        tablesCreated = await createTable('''
        CREATE TABLE IF NOT EXISTS modalertschannel (
            guildID BIGINT PRIMARY KEY NOT NULL,
            channelID BIGINT NOT NULL
        );
        ''')

        # Return bool result
        print(f'{Fore.LIGHTGREEN_EX}Successfully created tables (if was needed)!{Style.RESET_ALL}')
        return tablesCreated

# ----------------------------------------------------------------

# Create instance of stream announcement
#streamAnnouncements = StreamAnnouncements(bot)

# Create roleGroup command
@tree.command(name="rolegroup", description="Create a group of roles. USAGE: /rolegroup <groupname>")
async def role_group(interaction: discord.Interaction, name: str):
    # Check if user is the guild owner
    isOwner = await interactionIsOwner(interaction)
    if not isOwner: return False

    # Insert group into the database
    guildID = await guildIDFromInteraction(interaction)
    insertedName = await insert("INSERT INTO roleGroups (guildID, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE guildID=VALUES(guildID), name=VALUES(name);", (guildID, name))
    if not insertedName:
        await interaction.response.send_message(f"# OOPS! \n### Could not insert group into the database, please try again!", ephemeral=True)
        print(f'{Fore.YELLOW}WARNING: A user tried creating a role group, and the group could not be inserted into the database: {Fore.CYAN}{name}{Fore.YELLOW}. The user was prompted to try the command again.{Style.RESET_ALL}')
        return False

    # Send success message
    await interaction.response.send_message(f"# SUCCESS! \n### The role group '{name}' has been created!", ephemeral=True)

# Create addrole command
@tree.command(name="addrole", description="Add a role to a group. USAGE: /addrole <groupname> @role <title> <description> <emoji>")
async def role_group(interaction: discord.Interaction, group_name: str, role_mention: str, title: str, descr: str, emoji: str):
    # Check if user is the guild owner
    isOwner = await interactionIsOwner(interaction)
    if not isOwner: return False

    # Get guildID
    guildID = await guildIDFromInteraction(interaction)

    # Verify that the role is valid
    roleID = str(roleIDFromMention(role_mention))
    isValidR = await isValidRole(roleID, interaction)
    if not isValidR:
        await interaction.response.send_message(f"# OOPS! The role '{roleID}' is not a valid role, please try again!", ephemeral=True)
        print(f'{Fore.YELLOW}WARNING: A user tried adding a role to a group, and one or more of the roles was invalid: {Fore.CYAN}{roleID}{Fore.YELLOW}. The user was prompted to try the command again.{Style.RESET_ALL}')
        return False

    # Verify that the group is valid
    result = await select("SELECT COUNT(*) AS C FROM rolegroups WHERE guildID=%s AND name=%s;", (guildID, group_name))
    isValidGroup = await validateSelect(result)
    isValidGroup = isValidGroup[0][0]
    if isValidGroup != 1:
        await interaction.response.send_message(f"# OOPS! The group '{group_name}' is not a valid role, please try again!", ephemeral=True)
        print(f'{Fore.YELLOW}WARNING: A user tried adding a role to a group, and the group name was invalid: {Fore.CYAN}{group_name}{Fore.YELLOW}. The user was prompted to try the command again.{Style.RESET_ALL}')
        return False
    
    # Decode emoji
    emoji = await decodeEmoji(emoji)
    
    # Insert role into database
    insertedRole = await insert("INSERT INTO roles (roleID, groupName, title, descr, emoji, guildID) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE roleID=VALUES(roleID), groupName=VALUES(groupName), title=VALUES(title), descr=VALUES(descr), emoji=VALUES(emoji), guildID=VALUES(guildID);", (roleID, group_name, title, descr, emoji, guildID))
    if not insertedRole:
        await interaction.response.send_message(f"# OOPS! \n### Could not insert role '{roleID}' into the database! Please try again!", ephemeral=True)
        print(f'{Fore.YELLOW}WARNING: A user tried adding a role to a group, and it could not be inserted into the database: {Fore.CYAN}{roleID}{Fore.YELLOW}. The user was prompted to try the command again.{Style.RESET_ALL}')
        return False
    
    # Send success message
    await interaction.response.send_message(f"# SUCCESS! \n### The role {role_mention} has been added to group '{group_name}'!", ephemeral=True)

# Create postroles command
@tree.command(name="postroles", description="Create a reaction roles message for the specified type of role. USAGE: /postroles <groupname>")
async def post_roles(interaction: discord.Interaction):
    # Check if user is the guild owner
    isOwner = await interactionIsOwner(interaction)
    if not isOwner: return False

    # Fetch the guildID
    guildID = await guildIDFromInteraction(interaction)
    
    # Send init message
    await interaction.response.send_message(f"## Fetching available role groups...", ephemeral=True)

    # Fetch available role groups
    result = await select("SELECT * FROM rolegroups WHERE guildID=%s;", (guildID,))
    availableGroups = await validateSelect(result)
    options = []
    for group in availableGroups:
        option = {"id": group[1], "name": group[1]}
        options.append(option)

    # Display options for the user
    view = DynGroupsMenu(options)
    await interaction.followup.send("Choose a group to post:", view=view)

# User stats command
@tree.command(name="mystats", description="Get stats about your time in this server. USAGE: /mystats")
async def mystats(interaction: discord.Interaction): await Statistics.viewUserStats(interaction)

# Server stats command
@tree.command(name="serverstats", description="Show the lifetime stats of this server. USAGE: /serverstats")
async def serverstats(interaction: discord.Interaction): await Statistics.viewServerStats(interaction)

# Rand card draws command(s)
@tree.command(name="rand52draw", description="Draw a random card from a standard 52-card deck. USAGE: /rand52draw")
async def rand52draw(interaction: discord.Interaction):
    # Fetch random card
    cardTuple = Standard52CardDeckRandDraw().random
    cardName = cardTuple[0]
    file = await CardFile(cardTuple)

    # Send result
    await interaction.response.send_message(content=f"# You drew: \n## {cardName}", file=file, ephemeral=False)

# Modalerts channel command
@tree.command(name="modalerts", description="Set or changes the channel to receive moderation alerts. USAGE: /modalerts [optional]: <channel>")
async def modalerts(interaction: discord.Interaction, channel: discord.TextChannel = None):
    # Check if user is the guild owner
    isOwner = await interactionIsOwner(interaction)
    if not isOwner: return False

    # Get guildID and channel ID
    guildID = await guildIDFromInteraction(interaction)
    channelID = ""
    channelObj = None

    # Check if user used the optional channel argument
    if channel:
        channelID = channel.id
        channelObj = channel
    else:
        channelID = interaction.channel.id
        channelObj = interaction.channel
    
    # Insert into database
    await insert("INSERT INTO modalertschannel (guildID, channelID) VALUES (%s, %s) ON DUPLICATE KEY UPDATE channelID=VALUES(channelID);", (guildID, channelID))

    # Reply
    await interaction.response.send_message(f"# Success! \n Moderation alerts and info will now be sent to {channelObj.mention}", ephemeral=True)

# Blackjack game command
@tree.command(name="blackjack", description="Play a game of blackjack in the current channel! USAGE: /blackjack")
async def blackjack(interaction: discord.Interaction):
    await BlackJ.play(interaction)

# Main on_ready event
@bot.event
async def on_ready(): # Event that triggers when the bot has connected to Discord
    # Create necessary tables
    tablesCreated = await createTables()
    if not tablesCreated: # Fatal if the table was not created
        print(f'{Fore.RED}FATAL ERROR: Could not create necessary tables!{Style.RESET_ALL}')
        sys.exit() # Exit script

    # Sync registered commands
    await tree.sync()

    # Start stream listening
    #streamAnnouncements.start()

    # Send login message
    print(f'Logged in as {bot.user.name}\n=----------=')

# Message create event
@bot.event
async def on_message(message):
    # Ignore if it's the bot
    if message.author == bot.user: return

    # Stats
    await Stats.addMessage(message)
    await Stats.addMention(message) # Only adds if msg is a mention

    # Mod alerts
    await Alerts.msgCreate(message)

# Message delete event
@bot.event
async def on_message_delete(message):
    # Ignore if it's the bot
    if message.author == bot.user: return

    # Stats
    await Stats.removeMessage(message)

    # Mod alerts
    await Alerts.msgDelete(message)

# Message edit event
@bot.event
async def on_message_edit(before, after):
    # Get the message info
    guildID = after.guild.id if after.guild else None
    messageID = after.id
    editorID = after.author.id
    newContent = after.content

    # Get unix timestamp
    unix = getUnixTimestamp()

    # Edit message record
    await insert("UPDATE messages SET edited=TRUE, editorID=%s, editedUnixTimestamp=%s, newContent=%s WHERE guildID=%s AND messageID=%s;", (editorID, unix, newContent, guildID, messageID))

    # Mod alerts
    await Alerts.msgEdit(after)

# Reaction remove event
@bot.event
async def on_raw_reaction_remove(payload):
    # Ignore if bot
    if payload.user_id == bot.user.id: return

    # Stats
    await Stats.removeReact(payload)

    # Get guildID and guild
    guildID = payload.guild_id
    guild = bot.get_guild(guildID)

    # Get the channel
    channelID = payload.channel_id
    channel = bot.get_channel(channelID)
    if channel is None: # In case the bot doesn't have the channel cached, fetch it
        channel = await bot.fetch_channel(channelID)

    # Get the member
    userID = payload.user_id
    member = guild.get_member(userID)
    if member is None: # If member is not cached, fetch it
        member = await guild.fetch_member(userID)

    # Get the msgID
    msgID = payload.message_id

    # Select all reaction messages
    result = await select("SELECT * FROM reactMsgs WHERE guildID=%s AND msgID=%s;", (guildID, msgID))
    reactMsg = await validateSelect(result)
    if reactMsg == None: # No reactMsg was found that matched this emoji and message
        return
    
    # Get record's data
    msg = reactMsg[0]
    groupName = msg[0]
    mid = msg[1]
    rid = msg[2]
    emoji = msg[3]
    guildID = msg[4]

    # Fetch the role
    role = guild.get_role(rid)
    if role is None:
        return False  # Role not found

    if role in member.roles:
        await member.remove_roles(role)

# Reaction add event
@bot.event
async def on_raw_reaction_add(payload):
    # Ignore if bot
    if payload.user_id == bot.user.id: return

    # Stats
    await Stats.addReact(payload)

    # Get guildID and guild
    guildID = payload.guild_id
    guild = bot.get_guild(guildID)

    # Get the channel
    channelID = payload.channel_id
    channel = bot.get_channel(channelID)
    if channel is None: # In case the bot doesn't have the channel cached, fetch it
        channel = await bot.fetch_channel(channelID)

    # Get the member
    userID = payload.user_id
    member = guild.get_member(userID)
    if member is None: # If member is not cached, fetch it
        member = await guild.fetch_member(userID)

    # Get the msgID
    msgID = payload.message_id

    # Select all reaction messages
    result = await select("SELECT * FROM reactMsgs WHERE guildID=%s AND msgID=%s;", (guildID, msgID))
    reactMsg = await validateSelect(result)
    if reactMsg == None: # No reactMsg was found that matched this emoji and message
        return
    
    # Get record's data
    msg = reactMsg[0]
    groupName = msg[0]
    mid = msg[1]
    rid = msg[2]
    emoji = msg[3]
    guildID = msg[4]

    # Fetch the role
    role = guild.get_role(rid)
    if role is None:
        return False  # Role not found

    if role not in member.roles:
        await member.add_roles(role)

# Member join event
@bot.event
async def on_member_join(member):
    # Stats
    await Stats.incrementMemberInvites(member)

# Guild join event
@bot.event
async def on_guild_join(guild):
    # Get guildID
    newGuildID = guild.id
    print(f'{Fore.GREEN}NEW SERVER ADDED: {Fore.CYAN}{newGuildID}{Style.RESET_ALL}')

    # Get owner's userID (not memberID)
    ownerUser = await bot.fetch_user(guild.owner_id)
    ownerUserID = ownerUser.id
    print(f'{Fore.GREEN}ownerUserID: {Fore.CYAN}{ownerUserID}{Style.RESET_ALL}')

    # Get owner's memberID (not userID)
    ownerMember = guild.get_member(ownerUserID)
    ownerMemberID = None # Init ownerMemberID
    if ownerMember:
        ownerMemberID = ownerMember.id
        print(f'{Fore.GREEN}ownerMemberID: {Fore.CYAN}{ownerMemberID}{Style.RESET_ALL}')
    else:
        await userDM(ownerUserID, msg="# Thanks for choosing QuietBot! \n### Unfortunately, there was an error creating the member object for you as the owner. Please remove this bot from your server, and add it again to re-try. This should fix the issue! \n# Sorry for the inconvenience!")
        print(f'{Fore.YELLOW}WARNING: Could not create member object for the owner! Aborted, and a DM has been sent to the owner!{Style.RESET_ALL}')
        return False
    
    # Insert guild into DB
    guildInserted = await insert("INSERT INTO guilds (guildID, ownerUserID, ownerMemberID) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE ownerUserID=VALUES(ownerUserID), ownerMemberID=VALUES(ownerMemberID);", (newGuildID, ownerUserID, ownerMemberID))
    if not guildInserted:
        await userDM(ownerUserID, msg="# Thanks for choosing QuietBot! \n### Unfortunately, there was an error inserting or updating your server in our database. Please remove this bot from your server, and add it again to re-try. This should fix the issue! \n# Sorry for the inconvenience!")
        print(f'{Fore.YELLOW}WARNING: Could not insert or update guild in database! Aborted, and a DM has been sent to the owner!{Style.RESET_ALL}')
        return False

# Start the bot with your token
bot.run(env('BOT'))
