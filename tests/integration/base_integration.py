from unittest import TestCase

from services.fanbotdatabase import *
from settings import DB_URL, TEST_GUILD_ONE_ID, TEST_GUILD_ONE_MUSIC_CHANNEL_ID, TEST_GUILD_TWO_ID, TEST_GUILD_TWO_MUSIC_CHANNEL_ID


class IntegrationTest(TestCase):
    """
    Setup:

    - Sets up the test database with models
    - Populates with artist_one and guild_one following artist_one
    """

    @classmethod
    def setUpClass(cls):
        try:
            cls.engine = create_engine(DB_URL)
            Base.metadata.create_all(cls.engine)
            cls.Session = sessionmaker(bind=cls.engine)

            cls.guild_one = GuildDTO(id=TEST_GUILD_ONE_ID, music_channel_id=TEST_GUILD_ONE_MUSIC_CHANNEL_ID)
            cls.artist_one = ArtistDTO(id='4pb4rqWSoGUgxm63xmJ8xc', name='Madeon')

            cls.guild_two = GuildDTO(id=TEST_GUILD_TWO_ID, music_channel_id=TEST_GUILD_TWO_MUSIC_CHANNEL_ID)
            cls.artist_two = ArtistDTO(id='3dz0NnIZhtKKeXZxLOxCam', name='Porter Robinson')

            session = cls.Session()

            guild_created = Guild(id=cls.guild_one.id, music_channel_id=cls.guild_one.music_channel_id)
            artist_created = Artist(id=cls.artist_one.id, name=cls.artist_one.name)
            session.add(guild_created)
            session.add(artist_created)

            guild_created.artists.append(artist_created)
            session.commit()

            session.close()
        except:
            cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
