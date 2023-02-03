# Fanbot **[(Invite to Server)](https://discord.com/api/oauth2/authorize?client_id=885000888131915799&permissions=34628258880&scope=bot%20applications.commands)**
Fanbot is the ultimate music fanboy! Keep your discord server updated on releases from the spotify artists you love.   

**Commands:** (Works with discord slash commands)
1. /setchannel - sets the current channel as the channel that release updates will send to
2. /follow {artist_spotify_link} - follow an artist
3. /listfollow - list all artists the bot is currently following.
4. To unfollow an artist, delete their corresponding role.

![Follow Example](https://github.com/andrewkassab/fanbot/blob/main/resources/followexample.png?raw=true)
![Notification Example](https://github.com/andrewkassab/fanbot/blob/main/resources/notificationexample.png?raw=true)
![List Roles Example](https://github.com/andrewkassab/fanbot/blob/main/resources/listrolesexample.png?raw=true)

# Development

Use python 3.8 - 3.9, otherwise there will be unexpected behaviors when Spotify rate limits you.

Create an app on [Spotify](https://developer.spotify.com/dashboard/applications), copy over the client id and client secret.  

Create an app and bot on [Discord](https://discord.com/developers/applications) and add the bot to your test server.  
- Scopes: bot, applications.commands  
- Bot Permissions:  Manage Roles, Read Messages/View Channels, Send Messages, Embed Links, Read Message History, Add Reactions (268520512)

Create a database, the default is mysql.connector, but can be configured through `settings.py`

**Environment Variables:**  
 
 In a .env file in root, fill out the following:
- SP_CLIENT_ID
- SP_CLIENT_SECRET
- DISCORD_TOKEN
- DB_HOST
- DB_USER
- DB_PASSWORD
- DB_NAME
