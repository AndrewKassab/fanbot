# Fanbot **[(Invite to Server)](https://discord.com/api/oauth2/authorize?client_id=885000888131915799&permissions=34628258880&scope=bot%20applications.commands)**
Fanbot is the ultimate music fanboy! Keep your discord server updated on releases from the spotify artists you love.   

**Commands:** (Works with discord slash commands)
1. /setchannel - sets the current channel as the channel that release updates will send to
2. /follow {artist_spotify_link} - follow an artist
3. /list - list all artists the bot is currently following.
4. To unfollow an artist, delete their corresponding role.

![Example Image](https://github.com/andrewkassab/mrmusic/blob/main/example.png?raw=true)

# Development

Use python 3.8 - 3.9, otherwise there will be unexpected behaviors when Spotify rate limits you.

1. Create an app on [Spotify](https://developer.spotify.com/dashboard/applications), copy over the client id and client secret.
2. Create an app and bot on [Discord](https://discord.com/developers/applications) and add the bot to your test server.
- Scopes: bot, applications.commands
- Bot Permissions:  Manage Roles, Read Messages/View Channels, Send Messages, Embed Links, Read Message History, Add Reactions (268520512)

**Environment Variables:**  
- FANBOT_SPOTIFY_CLIENT_ID
- FANBOT_SPOTIFY_CLIENT_SECRET
- FANBOT_DISCORD_TOKEN
