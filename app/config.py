from functools import lru_cache
from os import getenv

from dotenv import load_dotenv


REQUIRED_ENV_VARS = (
    "TELEGRAM_BOT_TOKEN",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "OPENROUTER_BASE_URL",
)


class Settings:
    telegram_bot_token: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    bot_admin_ids: tuple[int, ...]

    def __init__(self) -> None:
        load_dotenv()

        env_values = {
            name: self._get_required_env(name)
            for name in REQUIRED_ENV_VARS
        }

        self.telegram_bot_token = env_values["TELEGRAM_BOT_TOKEN"]
        self.openrouter_api_key = env_values["OPENROUTER_API_KEY"]
        self.openrouter_model = env_values["OPENROUTER_MODEL"]
        self.openrouter_base_url = env_values["OPENROUTER_BASE_URL"]
        user_id = getenv("USER_ID")
        admin_ids = (
            user_id
            if user_id is not None and user_id.strip()
            else getenv("BOT_ADMIN_IDS")
        )
        self.bot_admin_ids = self._parse_admin_ids(admin_ids)

    @staticmethod
    def _get_required_env(name: str) -> str:
        value = getenv(name)
        if value is None or not value.strip():
            raise RuntimeError(f"Missing required env var: {name}")
        return value.strip()

    @staticmethod
    def _parse_admin_ids(value: str | None) -> tuple[int, ...]:
        if value is None or not value.strip():
            return ()

        try:
            return tuple(int(part.strip()) for part in value.split(",") if part.strip())
        except ValueError as exc:
            raise RuntimeError(
                "Invalid env var USER_ID or BOT_ADMIN_IDS: expected comma-separated integer ids"
            ) from exc


@lru_cache
def get_settings() -> Settings:
    return Settings()
