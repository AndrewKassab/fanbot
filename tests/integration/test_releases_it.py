from tests.integration.base_bot_integration import BotIntegrationTest


class ReleasesIntegrationTest(BotIntegrationTest):

    @classmethod
    def setUpClass(cls):
        super(ReleasesIntegrationTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(ReleasesIntegrationTest, cls).tearDownClass()

    def asyncSetUp(self):
        super().setUp()

    def asyncTearDown(self):
        super().tearDown()
