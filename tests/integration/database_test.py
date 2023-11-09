from tests.integration.base_integration import BaseIntegrationTest


class DatabaseTest(BaseIntegrationTest):

    @classmethod
    def setUpClass(cls):
        super(DatabaseTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DatabaseTest, cls).tearDownClass()

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_get_guild_by_id(self):
        returned_guild = self.db.get_guild_by_id(self.existing_guild.id)
        self.assertEqual(self.existing_guild.id, returned_guild.id)