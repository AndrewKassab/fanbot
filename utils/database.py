from collections import defaultdict

from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER, db_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, String, Integer, ForeignKey, Date, BigInteger, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()


class Artist(Base):
    __tablename__ = 'Artists'

    id = Column(String(25), primary_key=True)
    name = Column(String(100))
    latest_release_id = Column(String(25))
    latest_release_name = Column(String(100))
    latest_release_date = Column(Date)

    guilds = relationship("Guild", secondary="FollowedArtist", back_populates="followed_artists")


class Guild:
    __tablename__ = "Guilds"

    id = Column(String(25), primary_key=True)
    music_channel_id = Column(BigInteger)

    artists = relationship("Artist", secondary="FollowedArtist", back_populates="guilds")


class FollowedArtist:
    __tablename__ = 'FollowedArtists'

    id = Column(Integer, primary_key=True, autoincrement=True)
    artist_id = Column(String(25), ForeignKey('Artist.id'))
    guild_id = Column(String(25), ForeignKey('Guild.id'))


class Database:

    def __init__(self):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        # Populate cache
        self.guild_to_artists = self.get_all_guilds_to_artists()
        self.guilds = {}
        self.artists = {}
        self.load_all_guilds()
        self.load_all_artists()

    def load_all_guilds(self):
        session = self.Session()
        try:
            for guild in session.query(Guild).all():
                self.guilds[guild.id] = guild
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def load_all_artists(self):
        session = self.Session
        try:
            for artist in session.query(Artist).all():
                self.artists[artist.id] = artist
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def get_guild_by_id(self, guild_id):
        return self.guilds.get(guild_id)

    def add_guild(self, guild_id, music_channel_id):
        session = self.Session()
        try:
            # Create a new Guild object
            new_guild = Guild(id=guild_id, music_channel_id=music_channel_id)

            # Add the new guild to the database
            session.add(new_guild)
            session.commit()

            # Add the new guild to the cache
            self.guilds[guild_id] = new_guild
        except SQLAlchemyError as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def update_guild(self, updated_guild):
        session = self.Session()
        try:
            guild = session.query(Guild).filter_by(id=updated_guild.id).first()
            if guild:
                guild.music_channel_id = updated_guild.music_channel_id
                self.guilds[updated_guild.id] = guild
                session.commit()
            else:
                print(f"Guild with id {updated_guild.id} not found.")
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def delete_guild_by_id(self, guild_id):
        self._generic_delete(Guild, guild_id, self.guilds)

    def is_guild_exist(self, guild_id):
        return guild_id in self.guilds.keys()

    def get_artist_by_id(self, artist_id):
        return self.artists.get(artist_id)

    def add_artist(self, artist_id, name):
        session = self.Session()
        try:
            new_artist = Artist(
                id=artist_id,
                name=name,
            )
            session.add(new_artist)
            session.commit()
            self.artists[artist_id] = new_artist
        except SQLAlchemyError as e:
            session.rollback()
            print(f"An error occurred: {e}")
        finally:
            session.close()

    def update_artist(self, updated_artist):
        session = self.Session()
        try:
            artist = session.query(Artist).filter_by(id=updated_artist.id).update({
                'name': updated_artist.name,
                'latest_release_id': updated_artist.latest_release_id,
                'latest_release_name': updated_artist.latest_release_name,
                'latest_release_date': updated_artist.latest_release_date
            })

            if artist:  # update() returns the number of matched items
                session.commit()
                self.artists[updated_artist.id] = updated_artist
            else:
                logging.warning(f"Artist with id {updated_artist.id} not found.")

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def delete_artist_by_id(self, artist_id):
        self._generic_delete(Artist, artist_id, self.artists)

    def _generic_delete(self, model_class, id, cache):
        session = self.Session()
        try:
            entity = session.query(model_class).filter_by(id=id).first()
            if entity:
                session.delete(entity)
                session.commit()
                if id in cache:
                    del cache[id]
            else:
                logging.warning(f"{model_class.__name__} with id {id} not found.")
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

