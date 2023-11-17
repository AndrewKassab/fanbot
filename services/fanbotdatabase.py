from contextlib import contextmanager

from settings import DB_URL
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, create_engine, Table
from sqlalchemy.orm import relationship, sessionmaker
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

    guilds = relationship("Guild", secondary=FollowedArtist, back_populates="artists", cascade="all, delete")


class Guild(Base):
    __tablename__ = "Guilds"

    id = Column(BigInteger, primary_key=True)
    music_channel_id = Column(BigInteger)

    artists = relationship("Artist", secondary=FollowedArtist, back_populates="guilds", cascade="all, delete")


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
                self.guilds[guild.id] = guild
                for artist in guild.artists:
                    self.artists[artist.id] = artist

    def get_guild_by_id(self, guild_id):
        return self.guilds.get(guild_id)

    def get_all_guilds(self):
        return list(self.guilds.values())

    def add_guild(self, guild):
        with self.session_scope() as session:
            session.add(guild)
            self.guilds[guild.id] = guild

    def update_guild(self, updated_guild):
        with self.session_scope() as session:
            guild = session.query(Guild).filter_by(id=updated_guild.id).first()
            if guild:
                guild.music_channel_id = updated_guild.music_channel_id
                self.guilds[updated_guild.id] = guild
                session.commit()

    def delete_guild_by_id(self, guild_id):
        with self.session_scope() as session:
            guild = session.query(Guild).filter_by(id=guild_id).first()
            if guild:
                for artist in guild.artists:
                    if artist.id in self.artists:
                        self.artists[artist.id].guilds.remove(guild)
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
            guild = self.guilds.get(guild_id)
            if guild is not None:
                session.add(artist)
                self.artists[artist.id] = artist
                artist.guilds.append(guild)

    def update_artist(self, updated_artist):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(id=updated_artist.id).first()
            artist.name = updated_artist.name
            artist.latest_release_name = updated_artist.latest_release_name
            artist.latest_release_id = updated_artist.latest_release_id

            if artist:
                session.commit()
                self.artists[updated_artist.id] = artist

    def delete_artist_by_id(self, artist_id):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if artist:
                for guild in artist.guilds:
                    if guild.id in self.guilds:
                        self.guilds[guild.id].artists.remove(artist)
                session.delete(artist)
                if artist_id in self.artists:
                    del self.artists[artist_id]

    def is_artist_exist(self, artist_id):
        return artist_id in self.artists.keys()

    def unfollow_artist_for_guild(self, artist_id, guild_id):
        with self.session_scope() as session:
            session.query(FollowedArtist).filter_by(
                artist_id=artist_id, guild_id=guild_id).delete(synchronize_session='fetch')
            artist = self.artists.get(artist_id)
            if len(artist.guilds) == 0:
                self.delete_artist_by_id(artist_id)

    def follow_existing_artist_for_guild(self, artist_id, guild_id):
        with self.session_scope() as session:
            artist = session.query(Artist).filter(Artist.id == artist_id).first()
            artist.guilds.append(self.guilds[guild_id])

    def does_guild_follow_artist(self, guild_id, artist_id):
        with self.session_scope() as session:
            association = session.query(FollowedArtist).filter_by(artist_id=artist_id, guild_id=guild_id).first()
            return association is not None
