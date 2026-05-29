import asyncio
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import router
from app.config import get_settings
from app.services.knowledge_service import KnowledgeService
from app.services.lead_service import LeadService
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger


async def main() -> None:
    logger = setup_logger()
    settings = get_settings()

    bot = Bot(token=settings.telegram_bot_token)
    knowledge_service = KnowledgeService()
    lead_service = LeadService()
    llm_service = LLMService(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        model=settings.openrouter_model,
    )

    dispatcher = Dispatcher(
        storage=MemoryStorage(),
        knowledge_service=knowledge_service,
        lead_service=lead_service,
        llm_service=llm_service,
        bot_admin_ids=settings.bot_admin_ids,
    )
    dispatcher.include_router(router)

    logger.info("Starting Telegram bot")
    await dispatcher.start_polling(
        bot,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())
