from collections import defaultdict

from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER, db_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, create_engine
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
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def load_all_artists(self):
        session = self.Session
        try:
            for artist in session.query(Artist).all():
                self.artists[artist.id] = artist
        except SQLAlchemyError as e:
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def get_guild_by_id(self, guild_id):
        return self.guilds.get(guild_id)

    def get_all_guilds(self):
        return self.guilds.values()

    def add_guild(self, guild_id, music_channel_id):
        session = self.Session()
        try:
            new_guild = Guild(id=guild_id, music_channel_id=music_channel_id)

            session.add(new_guild)
            session.commit()

            self.guilds[guild_id] = new_guild
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
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
                logging.warning(f"Guild with id {updated_guild.id} not found.")
        except Exception as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def delete_guild_by_id(self, guild_id):
        session = self.Session()
        try:
            guild = session.query(Guild).filter_by(id=guild_id).first()
            if guild:
                for artist in guild.artists:
                    artist.guilds.remove(guild)
                    if artist.id in self.artists:
                        self.artists[artist.id].guilds.remove(guild)

                session.delete(guild)
                session.commit()

                if guild_id in self.guilds:
                    del self.guilds[guild_id]

                logging.info(f"Successfully deleted guild {guild_id} and updated artist associations.")
            else:
                logging.warning(f"Guild with id {guild_id} not found.")
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def is_guild_exist(self, guild_id):
        return guild_id in self.guilds.keys()

    def get_artist_by_id(self, artist_id):
        return self.artists.get(artist_id)

    def get_all_artists(self):
        return self.artists.values()

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
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def update_artist(self, updated_artist):
        session = self.Session()
        try:
            artist = session.query(Artist).filter_by(id=updated_artist.id).update({
                'name': updated_artist.name,
                'latest_release_id': updated_artist.latest_release_id,
                'latest_release_name': updated_artist.latest_release_name,
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
        session = self.Session()
        try:
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if artist:
                for guild in artist.guilds:
                    guild.artists.remove(artist)
                    if guild.id in self.guilds:
                        self.guilds[guild.id].artists.remove(artist)

                session.delete(artist)
                session.commit()

                if artist_id in self.artists:
                    del self.artists[artist_id]

                logging.info(f"Successfully deleted artist {artist_id} and updated guild associations.")
            else:
                logging.warning(f"Artist with id {artist_id} not found.")
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()

    def unfollow_artist_for_guild(self, artist_id, guild_id):
        session = self.Session()
        try:
            # Find the association in the FollowedArtist table
            association = session.query(FollowedArtist).filter_by(artist_id=artist_id, guild_id=guild_id).first()
            if association:
                session.delete(association)  # Delete the association
                session.commit()
                logging.info(f"Successfully removed association between guild {guild_id} and artist {artist_id}")
                artist = self.artists.get(artist_id)
                guild = self.guilds.get(guild_id)
                if artist and guild:
                    guild.artists.remove(artist)
                    artist.guilds.remove(guild)
            else:
                logging.warning(f"No association found between guild {guild_id} and artist {artist_id}")
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            session.close()
