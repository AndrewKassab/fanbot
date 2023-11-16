from unittest import TestCase

from services.fanbotdatabase import *
from settings import DB_URL, TEST_GUILD_ONE_ID, TEST_GUILD_ONE_MUSIC_CHANNEL_ID


class BaseIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(DB_URL)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

        cls.existing_guild = Guild(id=TEST_GUILD_ONE_ID, music_channel_id=TEST_GUILD_ONE_MUSIC_CHANNEL_ID)
        cls.existing_artist = Artist(id='4pb4rqWSoGUgxm63xmJ8xc', name='Madeon')

        session = cls.Session()

        guild_created = Guild(id=cls.existing_guild.id, music_channel_id=cls.existing_guild.music_channel_id)
        artist_created = Artist(id=cls.existing_artist.id, name=cls.existing_artist.name)
        session.add(guild_created)
        session.add(artist_created)

        guild_created.artists.append(artist_created)
        session.commit()

        session.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.new_guild = Guild(id=1032787094474600461, music_channel_id=1032787094474600461)
        self.new_artist = Artist(id='3dz0NnIZhtKKeXZxLOxCam', name='Porter Robinson', latest_release_id=None,
                                latest_release_name=None)

        self.session = self.Session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
