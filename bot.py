from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from config.emojis import FOLLOW_ROLE_EMOJI, UNFOLLOW_ROLE_EMOJI
from config.commands import *
from utils.spotify import *
from utils.database import MusicDatabase, Guild
from discord.ext import commands
from cogs.releases import ReleasesCog
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s;%(levelname)s;%(message)s")

db = MusicDatabase()

bot = commands.Bot(command_prefix="/")
bot.add_cog(ReleasesCog(bot, db))

slash = SlashCommand(bot, sync_commands=True)



@bot.event
async def on_ready():
    logging.info('We have logged in as {0.user}'.format(bot))


@slash.slash(
    name=SET_COMMAND,
    description="Set the current channel to the update channel",
)
async def set_update_channel(ctx: SlashContext):
    message = await ctx.send("Attempting to configure current channel for updates...")
    if not db.is_guild_in_db(ctx.guild_id):
        db.add_guild(Guild(ctx.guild_id, ctx.channel_id))
        await message.edit(content="Current channel successfully configured for updates. "
                                   f"You may begin following artists using `/{FOLLOW_COMMAND}`.")
    else:
        db.update_guild_channel_id(ctx.guild_id, ctx.channel_id)
        await message.edit(content="Current channel successfully configured for updates.")


@slash.slash(
    name=FOLLOW_COMMAND,
    description="follow a spotify artist by providing their spotify profile link",
    options=[
        create_option(
            name="artist_link",
            description="The artist's spotify share link",
            option_type=3,
            required=True
        )
    ]
)
async def follow_artist(ctx: SlashContext, artist_link: str):
    message = await ctx.send('Attempting to follow artist...')

    if not db.is_guild_in_db(ctx.guild_id):
        await message.edit(content=f"You must first use `/{SET_COMMAND}` to configure a channel to send updates to.")
        return
    try:
        artist_id = extract_artist_id(artist_link)
        artist = await get_artist_by_id(artist_id)
    except InvalidArtistException:
        await message.edit(content="Artist not found, please make sure you are providing a valid spotify artist url")
        return

    artist_in_db = db.get_artist_for_guild(artist.id, ctx.guild_id)
    if artist_in_db is not None:
        role = ctx.guild.get_role(int(artist_in_db.role_id))
        await message.edit(content='This server is already following %s! We\'ve assigned '
                                   'you the corresponding role.' % artist_in_db.name)
    else:
        role = await ctx.guild.create_role(name=(artist.name.replace(" ", "") + 'Fan'))
        artist.role_id = role.id
        artist.guild_id = ctx.guild.id
        try:
            db.add_artist(artist)
        except Exception as e: # TODO: Make specific
            await message.edit(content="Failed to follow artist.")
            await role.delete()
            logging.exception('Failure to follow artist and add to db: ', str(e))
            return

        logging.info(f"Guild {ctx.guild_id} has followed a new artist: {artist.name} {artist.id}")
        await message.edit(
            content="<@&%s> %s has been followed!\n:white_check_mark:: Assign Role. :x:: Remove Role."
                    % (artist.role_id, artist.name))
        await message.add_reaction(FOLLOW_ROLE_EMOJI)
        await message.add_reaction(UNFOLLOW_ROLE_EMOJI)

    await ctx.author.add_roles(role)


@slash.slash(
    name=LIST_COMMAND,
    description="list followed artists",
)
async def list_follows(ctx: SlashContext):
    message = await ctx.send('Attempting to list all followed artists...')
    artists = db.get_all_artists_for_guild(guild_id=ctx.guild_id)
    await message.edit(content="Following Artists: %s" % list(artist.name for artist in artists.values()))


@bot.event
async def on_raw_reaction_add(payload):
    # Make sure this is a reaction to a valid message (one with a role)
    user = await bot.fetch_user(payload.user_id)
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != bot.user or user == bot.user or len(message.content) < 1 or message.content[1] != '@':
        return
    guild = channel.guild
    member = payload.member
    reaction = payload.emoji
    role_string = message.content.split()[0]
    role_id = int(role_string[3:len(role_string) - 1])
    role = guild.get_role(role_id=role_id)
    if role is None:
        return
    if reaction.name == FOLLOW_ROLE_EMOJI:
        await member.add_roles(role)
    elif reaction.name == UNFOLLOW_ROLE_EMOJI:
        await member.remove_roles(role)


async def add_role_reactions_to_message(message):
    await message.add_reaction(FOLLOW_ROLE_EMOJI)
    await message.add_reaction(UNFOLLOW_ROLE_EMOJI)


bot.run(os.environ.get('FANBOT_DISCORD_TOKEN'))
