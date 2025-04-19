from discord.ext import tasks, commands
from datetime import datetime, timedelta

class StreamAnnouncements:
    def __init__(self, bot):
        # Bot
        self.bot = bot

        # Get streamers list
        self.streamers = [
            472633228436439040, # Skye
            245705786150486016 # Quiet Wind
        ]

        # Get list of stream channels
        self.streamChannels = [
            {
                "channel_id": 1270577996969017377,
                "desired_name": "Skye's Streaming"
            },
            {
                "channel_id": 1270578069891055686,
                "desired_name": "Skye's Gaming"
            }
        ]

        # Get the announcement channelID, announcement role ID, and streaming threshold
        self.announcementChannelID = 1273769557944958987
        self.announcementRoleID = 1273776210333143132
        self.streamingThreshold = 5 # Length in seconds to wait before announcing the user is streaming

        # Initialize active streams object
        self.active_streams = {}

    @tasks.loop(seconds=10)
    async def check_streams(self):
        current_time = datetime.now() # Using .now instead of utcnow() because utcnow() is deprecated

        for user_id, stream_data in list(self.active_streams.items()):
            print(f"Checking user {user_id} in channel {stream_data['channel_id']}")
            if current_time - stream_data["start_time"] >= timedelta(seconds=self.streamingThreshold):
                await self.announceStream(1, user_id, stream_data["channel_id"])
                del self.active_streams[user_id]  # Remove after announcement

    async def announceStream(self, status, userID, channelID):
        # Get the guild
        guild = self.bot.get_guild(1191285208658485248)

        # Get the channel that the user joined & the announcement channel
        channel = guild.get_channel(channelID)
        announceChannel = guild.get_channel(self.announcementChannelID)

        # Get the announcement role
        role = guild.get_role(self.announcementRoleID)

        # Detect which user it is
        user = 0
        if userID in self.streamers:
            print("The user is in streamers whitelist!")
            user = guild.get_member(userID)
        else:
            print("The user is not in the streamers whitelist!")
            return

        if user and channel and announceChannel and role:
            # Check if the status is online or offline (1 or 0)
            if status == 1:
                print(f"Making announcement for {user.display_name} in {channel.name}")
                await announceChannel.send(f"{role.mention}\n\n***{user.mention}*** is now live in ***{channel.name}!!!***\n***({channel.mention})!***\n# Go join them!")
            elif status == 0:
                print(f"Making announcement for {user.display_name} in {channel.name}")
                await announceChannel.send(f"### {user.mention} is no longer streaming.")
        else:
            print("Failed to make an announcement - missing user, channel, announce_channel, or role.")
            return

    async def on_voice_state_update(self, member, before, after):
        # Print voice state update
        print(f"Voice state update for {member.display_name}")


        if member.id in self.streamers and after.channel and after.channel.id in [ch['channel_id'] for ch in self.streamChannels]:
            # If the user just started streaming
            if after.self_stream and not before.self_stream:
                print(f"{member.display_name} started streaming.")
                self.active_streams[member.id] = {"channel_id": after.channel.id, "start_time": datetime.now()}
            elif not after.self_stream and before.self_stream:
                print(f"{member.display_name} stopped streaming.")
                await self.announceStream(0, member.id, after.channel.id)
                if member.id in self.active_streams:
                    del self.active_streams[member.id]
        elif member.id in self.active_streams:
            # If the member leaves the channel or stops streaming, remove from active streams
            del self.active_streams[member.id]

    def start(self):
        self.check_streams.start()