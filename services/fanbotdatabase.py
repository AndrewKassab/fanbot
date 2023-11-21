from contextlib import contextmanager

from settings import DB_URL
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, create_engine, Table
from sqlalchemy.orm import relationship, sessionmaker, joinedload, make_transient
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()


FollowedArtist = Table('FollowedArtist', Base.metadata,
                       Column('id', Integer, primary_key=True, autoincrement=True),
                       Column('artist_id', String(25), ForeignKey('Artists.id')),
                       Column('guild_id', BigInteger, ForeignKey('Guilds.id'))
)


class Artist(Base):
    __tablename__ = 'Artists'

    id = Column(String(25), primary_key=True)
    name = Column(String(100))
    latest_release_id = Column(String(25))
    latest_release_name = Column(String(100))

    guilds = relationship(
        "Guild",
        secondary=FollowedArtist,
        back_populates="artists",
        cascade="all, delete"
    )


class Guild(Base):
    __tablename__ = "Guilds"

    id = Column(BigInteger, primary_key=True)
    music_channel_id = Column(BigInteger)

    artists = relationship(
        "Artist",
        secondary=FollowedArtist,
        back_populates="guilds",
        cascade="all, delete"
    )


class ArtistDTO:
    def __init__(self, id, name, latest_release_id=None, latest_release_name=None, guild_ids=None):
        self.id = id
        self.name = name
        self.latest_release_id = latest_release_id
        self.latest_release_name = latest_release_name
        if guild_ids is not None:
            self.guild_ids = set(guild_ids)
        else:
            self.guild_ids = set()


class GuildDTO:
    def __init__(self, id, music_channel_id=None, artist_ids=None):
        self.id = id
        self.music_channel_id = music_channel_id
        self.artist_ids = artist_ids


def artist_to_dto(artist):
    guild_ids = {guild.id for guild in artist.guilds}
    return ArtistDTO(artist.id, artist.name, artist.latest_release_id, artist.latest_release_name, guild_ids)


def guild_to_dto(guild):
    artist_ids = {artist.id for artist in guild.artists}
    return GuildDTO(guild.id, guild.music_channel_id, artist_ids)


class FanbotDatabase:

    def __init__(self, session=None):
        self.engine = create_engine(DB_URL)
        self.Session = sessionmaker(bind=self.engine)
        self._session = session

        self.guilds = {}
        self.artists = {}
        self.load_cache()

    @contextmanager
    def session_scope(self):
        if self._session:
            yield self._session
        else:
            session = self.Session()
            try:
                yield session
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()

    def load_cache(self):
        self.guilds = {}
        self.artists = {}
        with self.session_scope() as session:
            for guild in session.query(Guild).all():
                self.guilds[guild.id] = guild_to_dto(guild)
            for artist in session.query(Artist).all():
                self.artists[artist.id] = artist_to_dto(artist)

    def get_guild_by_id(self, guild_id):
        return self.guilds.get(guild_id)

    def get_all_guilds(self):
        return list(self.guilds.values())

    def add_guild(self, guild_id, music_channel_id):
        with self.session_scope() as session:
            guild = Guild(id=guild_id, music_channel_id=music_channel_id)
            session.add(guild)
            self.guilds[guild_id] = guild_to_dto(guild)

    def update_guild(self, updated_guild):
        with self.session_scope() as session:
            guild = session.query(Guild).filter_by(id=updated_guild.id).first()
            if guild:
                guild.music_channel_id = updated_guild.music_channel_id
                self.guilds[updated_guild.id] = updated_guild
                session.commit()

    def delete_guild_by_id(self, guild_id):
        with self.session_scope() as session:
            guild = session.query(Guild).filter_by(id=guild_id).first()
            if guild:
                for artist in guild.artists:
                    if artist.id in self.artists:
                        self.artists[artist.id].guild_ids.remove(guild_id)
                        if len(self.artists[artist.id].guild_ids) == 0:
                            self.delete_artist_by_id(artist.id)
                session.delete(guild)
                if guild_id in self.guilds:
                    del self.guilds[guild_id]
                logging.info(f"Deleted guild {guild_id} and updated artist associations.")

    def is_guild_exist(self, guild_id):
        return guild_id in self.guilds.keys()

    def get_artist_by_id(self, artist_id):
        return self.artists.get(artist_id)

    def get_all_artists(self):
        return list(self.artists.values())

    # Artists are only ever added when a guild initially follows them
    def add_new_artist(self, artist_id, artist_name, guild_id):
        artist = Artist(id=artist_id, name=artist_name)
        with self.session_scope() as session:
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            if guild is not None:
                session.add(artist)
                artist.guilds.append(guild)
                self.artists[artist.id] = artist_to_dto(artist)
                self.guilds[guild_id].artist_ids.add(artist_id)

    def update_artist(self, updated_artist):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(id=updated_artist.id).first()
            artist.name = updated_artist.name
            artist.latest_release_name = updated_artist.latest_release_name
            artist.latest_release_id = updated_artist.latest_release_id

            if artist:
                self.artists[updated_artist.id] = updated_artist

    def delete_artist_by_id(self, artist_id):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if artist:
                for guild_id in self.artists[artist_id].guild_ids:
                    if guild_id in self.guilds:
                        self.guilds[guild_id].artist_ids.remove(artist.id)
                session.delete(artist)
                if artist_id in self.artists:
                    del self.artists[artist_id]

    def is_artist_exist(self, artist_id):
        return artist_id in self.artists.keys()

    def unfollow_artist_for_guild(self, artist_id, guild_id):
        with self.session_scope() as session:
            session.query(FollowedArtist).filter_by(
                artist_id=artist_id, guild_id=guild_id).delete(synchronize_session='fetch')
            session.flush()
            session.expire_all()
            artist = self.artists.get(artist_id)
            if guild_id in artist.guild_ids:
                artist.guild_ids.remove(guild_id)
                self.guilds.get(guild_id).artist_ids.remove(artist_id)
            if len(artist.guild_ids) == 0:
                self.delete_artist_by_id(artist_id)

    def follow_existing_artist_for_guild(self, artist_id, guild_id):
        with self.session_scope() as session:
            artist = session.query(Artist).filter(Artist.id == artist_id).first()
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            artist.guilds.append(guild)
            self.artists[artist_id] = artist_to_dto(artist)
            self.guilds[guild_id].artist_ids.add(artist_id)

    def does_guild_follow_artist(self, guild_id, artist_id):
        return artist_id in self.guilds.get(guild_id).artist_ids
