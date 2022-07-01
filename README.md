# Fanbot (Public invite link coming soon, in final testing phases)
Fanbot is the ultimate music fanboy! Keep your discord server updated on releases from the spotify artists you love.

**Commands:** (Works with discord slash commands)
1. /setchannel - sets the current channel as the channel that release updates will send to
2. /follow {artist_spotify_link} - follow an artist
3. /list - list all artists the bot is currently following.
4. To unfollow an artist, delete their corresponding role.

# Example

![Example Image](https://github.com/andrewkassab/mrmusic/blob/main/example.png?raw=true)

# Development

* Use python 3.7 or 3.8, otherwise there are unexpected behaviors when spotify rate limits. 

**Environment Variables:**  
- FANBOT_SPOTIFY_CLIENT_ID
- FANBOT-SPOTIFY_CLIENT_SECRET
- FANBOT_DISCORD_TOKEN
