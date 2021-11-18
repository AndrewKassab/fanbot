# Music Follower (NAME TBD)
Keep your music chat on discord updated on releases from the spotify artists you love! Once you follow an artist, the bot will notify your server's music channel with any new releases by that artist.

**Commands:** (Works with discord slash commands)
1. /follow - follow an artist
2. /unfollow - unfollow an artist
3. /list - list all artists the bot is currently following.

# Creating your own music bot:

The existing bot only works on my server, but I will update the bot later to be able to be added to other servers. 
For the time being, if you wish to get this working on your own server, you'll have to deploy the code yourself on your own bot through the following steps:
1. Create an application on [Spotify for Developers](https://developer.spotify.com/). Take note of the Client ID and Client Secret given to you. 
2. For your bot's server environment, set the `MUSIC_BOT_CLIENT_ID` and `MUSIC_BOT_CLIENT_SECRET` values respectively.
3. In `music_bot.py`, set the guild_ids and music_channel_id to the respective ids for your server. (Get these by right clicking each in discord and clicking copy id)
4. Create a bot on the [Discord Developer Portal](https://discord.com/developers), and add that bot to your server. Make sure you give the bot permission for Slash Commands. 
It's easiest if you just make the bot an admin.
5. Generate a token for the bot, and set the `MUSIC_BOT_TOKEN` environment variable to the token given to you.

The bot should now be good to go on your sever! Run it and start giving it commands.