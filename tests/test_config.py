import os
import unittest
from unittest.mock import patch

from app.config import Settings


REQUIRED_ENV = {
    "TELEGRAM_BOT_TOKEN": "test-token",
    "OPENROUTER_API_KEY": "test-api-key",
    "OPENROUTER_MODEL": "test-model",
    "OPENROUTER_BASE_URL": "https://example.com/api/v1",
}


class SettingsTestCase(unittest.TestCase):
    @patch("app.config.load_dotenv")
    def test_bot_admin_ids_override_non_numeric_user_id(self, load_dotenv) -> None:
        env = {
            **REQUIRED_ENV,
            "BOT_ADMIN_IDS": "1250232776",
            "USER_ID": "elvtap",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        self.assertEqual(settings.bot_admin_ids, (1250232776,))

    @patch("app.config.load_dotenv")
    def test_user_id_is_used_as_fallback(self, load_dotenv) -> None:
        env = {
            **REQUIRED_ENV,
            "BOT_ADMIN_IDS": "",
            "USER_ID": "8570106541",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

        self.assertEqual(settings.bot_admin_ids, (8570106541,))


if __name__ == "__main__":
    unittest.main()
