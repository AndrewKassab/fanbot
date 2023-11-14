from unittest import TestCase

from services.fanbotdatabase import *
from settings import test_db_url


class BaseIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(test_db_url)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

        cls.existing_guild = Guild(id='1004184458431315989', music_channel_id='1004184459190480938')
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
        self.new_guild = Guild(id='1032787094474600461', music_channel_id='1032787094474600461')
        self.new_artist = Artist(id='3dz0NnIZhtKKeXZxLOxCam', name='Porter Robinson', latest_release_id=None,
                                latest_release_name=None)

        self.session = self.Session()
        self.db = FanbotDatabase(self.session)

    def tearDown(self):
        self.session.rollback()
        self.session.close()
