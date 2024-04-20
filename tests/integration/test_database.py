import sqlalchemy.exc

from tests.integration.base_integration import IntegrationTest
from services.fanbotdatabase import Guild, Artist, FanbotDatabase


class DatabaseTest(IntegrationTest):
    '''
    Existing preconditions:

    guild_one exists following artist_one who exists

    guild_two and artist_two do not exist
    '''

    @classmethod
    def setUpClass(cls):
        super(DatabaseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DatabaseTest, cls).tearDownClass()

    def setUp(self):
        super().setUp()
        self.db = FanbotDatabase(self.session)

    def tearDown(self):
        super().tearDown()

    def test_get_guild_by_id(self):
        returned_guild = self.db.get_guild_by_id(self.guild_one.id)

        self.assertEqual(self.guild_one.id, returned_guild.id)

    def test_get_guild_by_id_not_real(self):
        returned_guild = self.db.get_guild_by_id("12345")

        self.assertIsNone(returned_guild)

    def test_get_all_guilds(self):
        returned_guilds = self.db.get_all_guilds()

        self.assertEqual(1, len(returned_guilds))
        self.assertEqual(self.guild_one.id, returned_guilds[0].id)

    def test_get_all_guilds_empty(self):
        guild = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()

        self.session.delete(guild)
        self.db.load_cache()

        returned_guilds = self.db.get_all_guilds()

        self.assertEqual(len(returned_guilds), 0)

    def test_add_guild_new_guild(self):
        self.db.add_guild(self.guild_two.id, self.guild_two.music_channel_id)

        guild_db = self.session.query(Guild).filter(Guild.id == self.guild_two.id).first()
        guild_cached = self.db.get_guild_by_id(self.guild_two.id)

        self.assertIsNotNone(guild_db)
        self.assertEqual(guild_db.music_channel_id, guild_cached.music_channel_id)

    def test_add_guild_existing_guild(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.add_guild(self.guild_one.id, self.guild_one.music_channel_id)
            self.session.flush()

    def test_update_guild(self):
        new_music_channel_id = 12345

        self.guild_one.music_channel_id = new_music_channel_id
        self.db.update_guild(self.guild_one)

        guild_db = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()
        guild_cached = self.db.get_guild_by_id(self.guild_one.id)

        self.assertEqual(new_music_channel_id, guild_db.music_channel_id)
        self.assertEqual(new_music_channel_id, guild_cached.music_channel_id)

    def test_delete_guild(self):
        self.db.delete_guild_by_id(self.guild_one.id)

        guild_db = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()
        guild_cached = self.db.get_guild_by_id(self.guild_one.id)
        artist_cached = self.db.get_artist_by_id(self.artist_one.id)
        artist_db = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()

        self.assertIsNone(guild_db)
        self.assertIsNone(guild_cached)
        self.assertIsNone(artist_cached) # The only guild following this artist is deleted
        self.assertIsNone(artist_db) # The only guild following this artist is deleted

    def test_does_guild_exist_existing_guild_exists(self):
        self.assertTrue(self.db.is_guild_exist(self.guild_one.id))

    def test_does_guild_exist_doesnt_exist(self):
        self.assertFalse(self.db.is_guild_exist("12345"))

    def test_get_artist_by_id(self):
        returned_artist = self.db.get_artist_by_id(self.artist_one.id)

        self.assertEqual(self.artist_one.name, returned_artist.name)

    def test_get_artist_by_id_not_real(self):
        returned_artist = self.db.get_artist_by_id("12345")

        self.assertIsNone(returned_artist)

    def test_get_all_artists(self):
        returned_artists = self.db.get_all_artists()

        self.assertEqual(1, len(returned_artists))
        self.assertEqual(self.artist_one.id, returned_artists[0].id)

    def test_get_all_artists_empty(self):
        artist = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()
        self.session.delete(artist)
        self.db.load_cache()

        returned_artists = self.db.get_all_artists()

        self.assertEqual(0, len(returned_artists))

    def test_add_artist_new_artist(self):
        self.db.add_new_artist(self.artist_two.id, self.artist_two.name, self.guild_one.id)

        added_artist = self.session.query(Artist).filter(Artist.id == self.artist_two.id).first()
        artist_cached = self.db.get_artist_by_id(self.artist_two.id)
        guild_cached = self.db.get_guild_by_id(self.guild_one.id)

        self.assertEqual(self.artist_two.name, added_artist.name)
        self.assertEqual(added_artist.name, artist_cached.name)
        self.assertTrue(self.artist_two.id in guild_cached.artist_ids)

    def test_add_artist_existing_artist(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.add_new_artist(self.artist_one.id, self.artist_one.name, self.guild_one.id)
            self.session.flush()

    def test_update_artist(self):
        new_latest_release_id = '12345'
        self.artist_one.latest_release_id = new_latest_release_id

        self.db.update_artist(self.artist_one)

        artist_db = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()
        artist_cached = self.db.get_artist_by_id(self.artist_one.id)

        self.assertEqual(new_latest_release_id, artist_db.latest_release_id)
        self.assertEqual(new_latest_release_id, artist_cached.latest_release_id)

    def test_delete_artist(self):
        self.db.delete_artist_by_id(self.artist_one.id)

        artist_db = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()
        artist_cache = self.db.get_artist_by_id(self.artist_one.id)
        guild_cache = self.db.get_guild_by_id(self.guild_one.id)

        self.assertIsNone(artist_db)
        self.assertIsNone(artist_cache)
        self.assertEqual(0, len(guild_cache.artist_ids))

    def test_unfollow_artist_for_guild_deleted_artist(self):
        self.db.unfollow_artist_for_guild(self.artist_one.id, self.guild_one.id)

        guild_db = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()
        guild_cached = self.db.get_guild_by_id(self.guild_one.id)
        artist_db = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()
        artist_cached = self.db.get_artist_by_id(self.artist_one.id)

        self.assertEqual(0, len(guild_db.artists))
        self.assertEqual(0, len(guild_cached.artist_ids))
        self.assertIsNone(artist_db)
        self.assertIsNone(artist_cached)

    def test_unfollow_artist_for_guild_artist_still_exists(self):
        artist = self.session.query(Artist).filter(Artist.id == self.artist_one.id).first()
        new_guild_db = Guild(id=self.guild_two.id, music_channel_id=self.guild_two.music_channel_id)
        self.session.add(new_guild_db)
        artist.guilds.append(new_guild_db)
        self.db.load_cache()

        self.db.unfollow_artist_for_guild(artist.id, self.guild_one.id)
        self.session.flush()
        self.session.expire_all()

        existing_guild_db = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()
        existing_guild_cached = self.db.get_guild_by_id(self.guild_one.id)
        new_guild_cached = self.db.get_guild_by_id(self.guild_two.id)
        artist_cached = self.db.get_artist_by_id(self.artist_one.id)

        self.assertEqual(0, len(existing_guild_db.artists))
        self.assertEqual(1, len(new_guild_db.artists))
        self.assertEqual(1, len(artist.guilds))
        self.assertEqual(0, len(existing_guild_cached.artist_ids))
        self.assertEqual(1, len(new_guild_cached.artist_ids))
        self.assertEqual(1, len(artist_cached.guild_ids))

    def test_follow_existing_artist_for_guild(self):
        new_artist_db = Artist(id=self.artist_two.id, name=self.artist_two.name)
        self.session.add(new_artist_db)

        self.db.follow_existing_artist_for_guild(self.artist_two.id, self.guild_one.id)
        self.session.flush()
        self.session.expire_all()

        guild_db = self.session.query(Guild).filter(Guild.id == self.guild_one.id).first()
        guild_cached = self.db.get_guild_by_id(self.guild_one.id)
        artist_cached = self.db.get_artist_by_id(self.artist_two.id)

        self.assertEqual(2, len(guild_db.artists))
        self.assertEqual(2, len(guild_cached.artist_ids))
        self.assertEqual(1, len(new_artist_db.guilds))
        self.assertEqual(1, len(artist_cached.guild_ids))

    def test_does_guild_follow_artist_true(self):
        self.assertTrue(self.db.does_guild_follow_artist(self.guild_one.id, self.artist_one.id))

    def test_does_guild_follow_artist_false(self):
        new_artist_db = Artist(id=self.artist_two.id, name=self.artist_two.name)
        self.session.add(new_artist_db)
        self.assertFalse(self.db.does_guild_follow_artist(self.guild_one.id, self.artist_two.id))


