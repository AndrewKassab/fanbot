from contextlib import contextmanager

from settings import db_url
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, create_engine, Table
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()


FollowedArtist = Table('FollowedArtist', Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('artist_id', String(25), ForeignKey('Artists.id')),
    Column('guild_id', String(25), ForeignKey('Guilds.id'))
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

    id = Column(String(25), primary_key=True)
    music_channel_id = Column(BigInteger)

    artists = relationship("Artist", secondary=FollowedArtist, back_populates="guilds", cascade="all, delete")


class FanbotDatabase:

    def __init__(self):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.guilds = {}
        self.artists = {}
        self.load_cache()

    @contextmanager
    def session_scope(self):
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
        with self.session_scope() as session:
            for guild in session.query(Guild).all():
                self.guilds[guild.id] = guild
                for artist in guild.artists:
                    self.artists[artist.id] = artist

    def get_guild_by_id(self, guild_id):
        return self.guilds.get(guild_id)

    def get_all_guilds(self):
        return self.guilds.values()

    def add_guild(self, guild_id, music_channel_id):
        with self.session_scope() as session:
            new_guild = Guild(id=guild_id, music_channel_id=music_channel_id)
            session.add(new_guild)
            self.guilds[guild_id] = new_guild

    def update_guild(self, updated_guild):
        with self.session_scope() as session:
            guild = session.query(Guild).filter_by(id=updated_guild.id).first()
            if guild:
                guild.music_channel_id = updated_guild.music_channel_id
                self.guilds[updated_guild.id] = guild
                session.commit()
            else:
                logging.warning(f"Attempted to update non-existing guild")

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
        return self.artists.values()

    # Artists are only ever added when a guild initially follows them
    def add_new_artist(self, artist, guild_id):
        with self.session_scope() as session:
            guild = self.guilds[guild_id]
            if self.get_artist_by_id(artist.id) is None:
                session.add(artist)
                self.artists[artist.id] = artist
                artist.guilds.append(guild)

    def update_artist(self, updated_artist):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(id=updated_artist.id).update({
                'name': updated_artist.name,
                'latest_release_id': updated_artist.latest_release_id,
                'latest_release_name': updated_artist.latest_release_name,
            })

            if artist:  # update() returns the number of matched items
                session.commit()
                self.artists[updated_artist.id] = updated_artist

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
            association = session.query(FollowedArtist).filter_by(artist_id=artist_id, guild_id=guild_id).first()
            if association:
                session.delete(association)
                artist = self.artists.get(artist_id)
                guild = self.guilds.get(guild_id)
                if artist and guild:
                    guild.artists.remove(artist)
                    artist.guilds.remove(guild)
                if len(artist.guilds) == 0:
                    self.delete_artist_by_id(artist_id)

    def follow_existing_artist_for_guild(self, artist_id, guild_id):
        with self.session_scope() as session:
            artist = session.query(Artist).filter_by(artist_id=artist_id).first()
            artist.guilds.append(self.guilds[guild_id])

            self.artists[artist_id].guilds.append(self.guilds[guild_id])
            self.guilds[guild_id].artists.append(self.artists[artist_id])

    def does_guild_follow_artist(self, guild_id, artist_id):
        with self.session_scope() as session:
            association = session.query(FollowedArtist).filter_by(artist_id=artist_id, guild_id=guild_id).first()
            return association is not None
