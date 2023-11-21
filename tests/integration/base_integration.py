from unittest import TestCase

from services.fanbotdatabase import *
from settings import DB_URL, TEST_GUILD_ONE_ID, TEST_GUILD_ONE_MUSIC_CHANNEL_ID


class IntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.engine = create_engine(DB_URL)
            Base.metadata.create_all(cls.engine)
            cls.Session = sessionmaker(bind=cls.engine)

            cls.existing_guild = GuildDTO(id=TEST_GUILD_ONE_ID, music_channel_id=TEST_GUILD_ONE_MUSIC_CHANNEL_ID)
            cls.existing_artist = ArtistDTO(id='4pb4rqWSoGUgxm63xmJ8xc', name='Madeon')

            cls.new_guild = Guild(id=1032787094474600461, music_channel_id=1032787094474600461)
            cls.new_artist = Artist(id='3dz0NnIZhtKKeXZxLOxCam', name='Porter Robinson')

            session = cls.Session()

            guild_created = Guild(id=cls.existing_guild.id, music_channel_id=cls.existing_guild.music_channel_id)
            artist_created = Artist(id=cls.existing_artist.id, name=cls.existing_artist.name)
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

