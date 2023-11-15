import sqlalchemy.exc

from tests.integration.base_integration import BaseIntegrationTest
from services.fanbotdatabase import Guild, Artist, FanbotDatabase


class DatabaseTest(BaseIntegrationTest):

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
        returned_guild = self.db.get_guild_by_id(self.existing_guild.id)

        self.assertEqual(self.existing_guild.id, returned_guild.id)

    def test_get_guild_by_id_not_real(self):
        returned_guild = self.db.get_guild_by_id("12345")

        self.assertIsNone(returned_guild)

    def test_get_all_guilds(self):
        returned_guilds = self.db.get_all_guilds()

        self.assertEqual(1, len(returned_guilds))
        self.assertEqual(self.existing_guild.id, returned_guilds[0].id)

    def test_get_all_guilds_empty(self):
        guild = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()

        self.session.delete(guild)
        self.db.load_cache()

        returned_guilds = self.db.get_all_guilds()

        self.assertEqual(len(returned_guilds), 0)

    def test_add_guild_new_guild(self):
        self.db.add_guild(self.new_guild)

        added_guild = self.session.query(Guild).filter(Guild.id == self.new_guild.id).first()

        self.assertEqual(self.new_guild, added_guild)
        self.assertEqual(added_guild, self.db.get_guild_by_id(added_guild.id))

    def test_add_guild_existing_guild(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.add_guild(self.existing_guild)
            self.session.flush()

    def test_update_guild(self):
        new_music_channel_id = '12345'

        self.existing_guild.music_channel_id = new_music_channel_id
        self.db.update_guild(self.existing_guild)

        guild_db = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()

        self.assertEqual(new_music_channel_id, guild_db.music_channel_id)
        self.assertEqual(guild_db, self.db.get_guild_by_id(self.existing_guild.id))

    def test_delete_guild(self):
        self.db.delete_guild_by_id(self.existing_guild.id)

        guild_db = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()
        guild = self.db.get_guild_by_id(self.existing_guild.id)

        self.assertIsNone(guild_db)
        self.assertIsNone(guild)

    def test_does_guild_exist_existing_guild_exists(self):
        self.assertTrue(self.db.is_guild_exist(self.existing_guild.id))

    def test_does_guild_exist_doesnt_exist(self):
        self.assertFalse(self.db.is_guild_exist("12345"))

    def test_get_artist_by_id(self):
        returned_artist = self.db.get_artist_by_id(self.existing_artist.id)

        self.assertEqual(self.existing_artist.id, returned_artist.id)

    def test_get_artist_by_id_not_real(self):
        returned_artist = self.db.get_artist_by_id("12345")

        self.assertIsNone(returned_artist)

    def test_get_all_artists(self):
        returned_artists = self.db.get_all_artists()

        self.assertEqual(1, len(returned_artists))
        self.assertEqual(self.existing_artist.id, returned_artists[0].id)

    def test_get_all_artists_empty(self):
        artist = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()
        self.session.delete(artist)
        self.db.load_cache()

        returned_artists = self.db.get_all_artists()

        self.assertEqual(0, len(returned_artists))

    def test_add_artist_new_artist(self):
        self.db.add_new_artist(self.new_artist, self.existing_guild.id)

        added_artist = self.session.query(Artist).filter(Artist.id == self.new_artist.id).first()

        self.assertEqual(self.new_artist, added_artist)
        self.assertEqual(added_artist, self.db.get_artist_by_id(added_artist.id))

    def test_add_artist_existing_artist(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.db.add_new_artist(self.existing_artist, self.existing_guild.id)
            self.session.flush()

    def test_update_artist(self):
        new_latest_release_id = '12345'
        self.existing_artist.latest_release_id = new_latest_release_id

        self.db.update_artist(self.existing_artist)

        artist_db = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()

        self.assertEqual(new_latest_release_id, artist_db.latest_release_id)
        self.assertEqual(artist_db, self.db.get_artist_by_id(self.existing_artist.id))

    def test_delete_artist(self):
        self.db.delete_artist_by_id(self.existing_artist.id)

        artist_db = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()
        artist_cache = self.db.get_artist_by_id(self.existing_artist.id)
        guild_cache = self.db.get_guild_by_id(self.existing_guild.id)

        self.assertIsNone(artist_db)
        self.assertIsNone(artist_cache)
        self.assertEqual(0, len(guild_cache.artists))

    def test_unfollow_artist_for_guild_deleted_artist(self):
        self.db.unfollow_artist_for_guild(self.existing_artist.id, self.existing_guild.id)
        self.session.flush()
        self.session.expire_all()

        guild_db = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()
        guild_cache = self.db.get_guild_by_id(self.existing_guild.id)
        artist_db = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()
        artist_cache = self.db.get_artist_by_id(self.existing_artist.id)

        self.assertEqual(0, len(guild_db.artists))
        self.assertEqual(0, len(guild_cache.artists))
        self.assertIsNone(artist_db)
        self.assertIsNone(artist_cache)

    def test_unfollow_artist_for_guild_artist_still_exists(self):
        artist = self.session.query(Artist).filter(Artist.id == self.existing_artist.id).first()
        self.session.add(self.new_guild)
        artist.guilds.append(self.new_guild)

        self.db.unfollow_artist_for_guild(artist.id, self.existing_guild.id)
        self.session.flush()
        self.session.expire_all()

        existing_guild = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()

        self.assertEqual(0, len(existing_guild.artists))
        self.assertEqual(1, len(self.new_guild.artists))
        self.assertEqual(1, len(artist.guilds))

    def test_follow_existing_artist_for_guild(self):
        self.session.add(self.new_artist)

        self.db.follow_existing_artist_for_guild(self.new_artist.id, self.existing_guild.id)
        self.session.flush()
        self.session.expire_all()

        guild_db = self.session.query(Guild).filter(Guild.id == self.existing_guild.id).first()
        guild_cache = self.db.get_guild_by_id(self.existing_guild.id)

        self.assertEqual(2, len(guild_db.artists))
        self.assertEqual(2, len(guild_cache.artists))

    def test_does_guild_follow_artist_true(self):
        self.assertTrue(self.db.does_guild_follow_artist(self.existing_guild.id, self.existing_artist.id))

    def test_does_guild_follow_artist_false(self):
        self.session.add(self.new_artist)
        self.assertFalse(self.db.does_guild_follow_artist(self.existing_guild.id, self.new_artist.id))


