import discord
from colorama import Fore, Style
from Utils.DB import select, validateSelect
from Utils.Emojis import encodeEmoji, decodeEmoji, normalizeEmoji
from Utils.DB import insert

class DynGroupsMenu(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)  # No timeout
        for opt in options:
            label = opt["name"]
            id = opt["name"]
            button = discord.ui.Button(
                label=label,
                custom_id=id,
                style=discord.ButtonStyle.primary
            )
            button.callback = self.button_click
            self.add_item(button)

    # Dynamically handle button clicks based on customID
    async def button_click(self, interaction: discord.Interaction,):
        # Get the channel and channelID
        channel = interaction.channel
        channelID = interaction.channel.id

        # Get the guildID
        guildID = interaction.guild_id

        # When user clicks on the button to select a group
        groupName = interaction.data["custom_id"]

        # Send message title
        await interaction.response.send_message(f"Creating...", ephemeral=True)
        await channel.send(f"# Reaction Roles")

        # Select all roles from that group
        result = await select("SELECT * FROM roles WHERE groupName=%s AND guildID=%s;", (groupName, guildID))
        roles = await validateSelect(result)
        if roles == None:
            await interaction.response.send_message(f"# OOPS! \n### You haven't added any roles to the group '{groupName}'! Please run the '/addrole' command and try again!", ephemeral=True)
            print(f'{Fore.YELLOW}WARNING: A user tried creating a reaction role message, but they did not add any roles to it yet: {Fore.CYAN}{groupName}{Fore.YELLOW}. The user was prompted to add roles, and try the command again.{Style.RESET_ALL}')
            return False
        
        # Loop through roles
        for role in roles:
            # Get the role data
            ID = role[0]
            mention = f"<@&{ID}>"
            group = role[1]
            title = role[2]
            descr = role[3]
            emoji = await encodeEmoji(role[4])
            
            # Send message to the channel
            reactMsg = await channel.send(f"# {title} \n### {mention} \n### {descr}")
            reactMsgID = reactMsg.id

            # React to the message
            await reactMsg.add_reaction(emoji)

            # Decode emoji & normalize it
            decodedEmoji = await decodeEmoji(emoji)
            normalizedEmoji = normalizeEmoji(decodedEmoji)

            # Store the reaction message in the database
            insertedRole = await insert("INSERT INTO reactMsgs (guildID, groupName, msgID, roleID, emoji) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE guildID=VALUES(guildID), groupName=VALUES(groupName), msgID=VALUES(msgID), roleID=VALUES(roleID), emoji=VALUES(emoji);", (guildID, group, reactMsgID, ID, normalizedEmoji))
            if not insertedRole:
                await interaction.response.send_message(f"# OOPS! \n### Could not insert reactMsg '{reactMsgID}' into the database! Please try again!", ephemeral=True)
                print(f'{Fore.YELLOW}WARNING: A user tried creating a reaction role message, and it could not be inserted into the database: {Fore.CYAN}{reactMsgID}{Fore.YELLOW}. The user was prompted to try the command again.{Style.RESET_ALL}')
                return False