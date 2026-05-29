import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message, Update

from app.bot.keyboards import main_keyboard, start_inline_keyboard
from app.bot.states import LeadForm
from app.services.knowledge_service import (
    KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE,
    KnowledgeService,
)
from app.services.lead_service import LeadService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = Router()

UNSUPPORTED_MESSAGE = (
    "Пока я понимаю только текстовые вопросы. Напишите вопрос сообщением."
)
ERROR_MESSAGE = "Произошла ошибка. Попробуйте ещё раз или свяжитесь с менеджером."
EMPTY_TEXT_MESSAGE = "Напишите вопрос текстом, и я постараюсь помочь."
LONG_TEXT_MESSAGE = (
    "Сообщение получилось слишком длинным. Пожалуйста, сократите вопрос "
    "до главных деталей и отправьте снова."
)
MAX_USER_QUESTION_LENGTH = 4000
LEAD_REQUEST_PHRASES = (
    "хочу заявку",
    "нужен расчет",
    "нужен расчёт",
    "нужна консультация",
)


def is_lead_request(text: str | None) -> bool:
    if text is None:
        return False

    normalized = text.lower().replace("ё", "е")
    return any(phrase.replace("ё", "е") in normalized for phrase in LEAD_REQUEST_PHRASES)


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    log_message_event(message, "command_start")
    text = (
        "Здравствуйте! Я отвечаю на вопросы по строительству и ремонту.\n\n"
        "Можно спросить про услуги, этапы работ, сроки, материалы, цены, "
        "гарантии, замер, договор, оплату или контакты."
    )
    await message.answer(text, reply_markup=start_inline_keyboard())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    log_message_event(message, "command_help")
    text = (
        "Примеры вопросов:\n\n"
        "- Сколько стоит ремонт?\n"
        "- Какие этапы строительства?\n"
        "- Делаете ли замер?\n"
        "- Какие сроки?\n"
        "- Есть ли гарантия?\n"
        "- Как заказать консультацию?\n\n"
        "Если точной информации нет в базе знаний, я предложу связаться с менеджером."
    )
    await message.answer(text, reply_markup=main_keyboard())


@router.message(Command("contacts"))
async def contacts_command(
    message: Message,
    knowledge_service: KnowledgeService,
) -> None:
    log_message_event(message, "command_contacts")
    contacts = knowledge_service.get_contacts()
    await message.answer(contacts, reply_markup=main_keyboard())


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    log_message_event(message, "command_cancel")
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Сейчас нет активной заявки.")
        return

    await state.clear()
    await message.answer(
        "Заявка отменена. Если понадобится консультация или расчет, напишите снова.",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data == "menu:services")
async def services_callback(callback: CallbackQuery) -> None:
    log_callback_event(callback, "callback_services")
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        "Мы можем помочь с консультацией, замером, сметой, подбором материалов, "
        "ремонтными, отделочными, монтажными и демонтажными работами. "
        "Напишите, какие работы нужны и что за объект."
    )


@router.callback_query(F.data == "menu:prices")
async def prices_callback(callback: CallbackQuery) -> None:
    log_callback_event(callback, "callback_prices")
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        "Стоимость зависит от площади, состояния объекта, выбранных материалов "
        "и сложности работ. Для точного расчета можно оставить заявку на консультацию "
        "или замер."
    )


@router.callback_query(F.data == "menu:timelines")
async def timelines_callback(callback: CallbackQuery) -> None:
    log_callback_event(callback, "callback_timelines")
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        "Сроки зависят от вида работ, площади, состояния объекта и наличия материалов. "
        "Напишите, какие работы нужны и примерную площадь, чтобы менеджер мог "
        "сориентировать точнее."
    )


@router.callback_query(F.data == "menu:contacts")
async def contacts_callback(
    callback: CallbackQuery,
    knowledge_service: KnowledgeService,
) -> None:
    log_callback_event(callback, "callback_contacts")
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(knowledge_service.get_contacts())


@router.callback_query(F.data == "menu:lead")
async def lead_callback(callback: CallbackQuery, state: FSMContext) -> None:
    log_callback_event(callback, "callback_lead")
    await callback.answer()
    if callback.message is None:
        return

    await start_lead_form(callback.message, state)


@router.message(StateFilter(None), F.text.func(is_lead_request))
async def lead_request_message(message: Message, state: FSMContext) -> None:
    log_message_event(message, "lead_request_text")
    await start_lead_form(message, state)


@router.message(LeadForm.name, F.text)
async def lead_name_received(message: Message, state: FSMContext) -> None:
    log_message_event(message, "lead_name_received")
    await state.update_data(name=message.text.strip())
    await state.set_state(LeadForm.phone)
    await message.answer("Укажите телефон для связи.")


@router.message(LeadForm.phone, F.text)
async def lead_phone_received(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    log_message_event(
        message,
        "lead_phone_received",
        extra=f"masked_phone={mask_phone(phone)}",
    )
    await state.update_data(phone=phone)
    await state.set_state(LeadForm.location)
    await message.answer("Укажите город или район объекта.")


@router.message(LeadForm.location, F.text)
async def lead_location_received(message: Message, state: FSMContext) -> None:
    log_message_event(message, "lead_location_received")
    await state.update_data(location=message.text.strip())
    await state.set_state(LeadForm.service)
    await message.answer("Какая услуга нужна?")


@router.message(LeadForm.service, F.text)
async def lead_service_received(message: Message, state: FSMContext) -> None:
    log_message_event(message, "lead_service_received")
    await state.update_data(service=message.text.strip())
    await state.set_state(LeadForm.description)
    await message.answer("Кратко опишите задачу.")


@router.message(LeadForm.description, F.text)
async def lead_description_received(
    message: Message,
    state: FSMContext,
    lead_service: LeadService,
    bot_admin_ids: tuple[int, ...],
) -> None:
    log_message_event(message, "lead_description_received")
    data = await state.get_data()
    await state.clear()

    lead = lead_service.save_lead(
        telegram_id=message.from_user.id if message.from_user else 0,
        username=message.from_user.username or "" if message.from_user else "",
        name=data["name"],
        phone=data["phone"],
        location=data["location"],
        service=data["service"],
        description=message.text.strip(),
    )

    await message.answer(
        "Спасибо, заявка принята. Менеджер свяжется с вами.",
        reply_markup=main_keyboard(),
    )
    await notify_admins(message, lead, bot_admin_ids)


@router.message(StateFilter(None), F.text)
async def answer_question(
    message: Message,
    knowledge_service: KnowledgeService,
    llm_service: LLMService,
) -> None:
    log_message_event(message, "text_question")
    question = (message.text or "").strip()
    if not question:
        await message.answer(EMPTY_TEXT_MESSAGE)
        return

    if len(question) > MAX_USER_QUESTION_LENGTH:
        logger.info(
            "telegram_id=%s username=%s event_type=long_text_rejected length=%s",
            get_telegram_id(message),
            get_username(message),
            len(question),
        )
        await message.answer(LONG_TEXT_MESSAGE)
        return

    thinking_message = await message.answer("Думаю над ответом...")

    knowledge_base = knowledge_service.read_knowledge_base()
    if knowledge_base == KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE:
        await thinking_message.edit_text(KNOWLEDGE_BASE_UNAVAILABLE_MESSAGE)
        return

    answer = await llm_service.answer_client_question(
        question=question,
        knowledge_base=knowledge_base,
    )

    await thinking_message.edit_text(answer)


@router.message(F.photo | F.document | F.voice | F.sticker)
async def unsupported_attachment(message: Message) -> None:
    log_message_event(message, "unsupported_attachment")
    await message.answer(UNSUPPORTED_MESSAGE)


@router.message()
async def unsupported_message(message: Message) -> None:
    log_message_event(message, "unsupported_message")
    await message.answer(UNSUPPORTED_MESSAGE)


@router.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    message = extract_message_from_update(event.update)
    telegram_id = get_telegram_id(message) if message else "unknown"
    username = get_username(message) if message else "unknown"

    logger.error(
        "telegram_id=%s username=%s event_type=error exception=%s",
        telegram_id,
        username,
        event.exception.__class__.__name__,
        exc_info=(
            event.exception.__class__,
            event.exception,
            event.exception.__traceback__,
        ),
    )

    if message is not None:
        try:
            await message.answer(ERROR_MESSAGE)
        except TelegramAPIError:
            logger.warning(
                "telegram_id=%s username=%s event_type=error_reply_failed",
                telegram_id,
                username,
            )

    return True


async def start_lead_form(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.name)
    await message.answer(
        "Давайте оформим заявку. Как вас зовут?\n\n"
        "Чтобы отменить заявку, отправьте /cancel."
    )


async def notify_admins(
    message: Message,
    lead: dict[str, str],
    bot_admin_ids: tuple[int, ...],
) -> None:
    if not bot_admin_ids:
        return

    username = f"@{lead['username']}" if lead["username"] else "не указан"
    text = (
        "Новая заявка\n\n"
        f"Дата: {lead['created_at']}\n"
        f"Telegram ID: {lead['telegram_id']}\n"
        f"Username: {username}\n"
        f"\nИмя: {lead['name']}\n"
        f"Телефон: {lead['phone']}\n"
        f"Город/район: {lead['location']}\n"
        f"Услуга: {lead['service']}\n"
        f"Описание: {lead['description']}"
    )

    for admin_id in bot_admin_ids:
        try:
            await message.bot.send_message(admin_id, text)
        except TelegramAPIError:
            logger.warning("event_type=admin_notification_failed admin_id=%s", admin_id)


def log_message_event(message: Message, event_type: str, extra: str = "") -> None:
    suffix = f" {extra}" if extra else ""
    logger.info(
        "telegram_id=%s username=%s event_type=%s%s",
        get_telegram_id(message),
        get_username(message),
        event_type,
        suffix,
    )


def log_callback_event(callback: CallbackQuery, event_type: str) -> None:
    logger.info(
        "telegram_id=%s username=%s event_type=%s callback_data=%s",
        callback.from_user.id,
        callback.from_user.username or "",
        event_type,
        callback.data or "",
    )


def get_telegram_id(message: Message) -> int | str:
    if message.from_user is None:
        return "unknown"
    return message.from_user.id


def get_username(message: Message) -> str:
    if message.from_user is None:
        return ""
    return message.from_user.username or ""


def mask_phone(phone: str) -> str:
    digits_count = sum(char.isdigit() for char in phone)
    if digits_count < 7:
        return "***"

    visible_seen = 0
    masked_chars: list[str] = []
    for char in phone:
        if not char.isdigit():
            masked_chars.append(char)
            continue

        visible_seen += 1
        if visible_seen <= 4 or visible_seen > digits_count - 4:
            masked_chars.append(char)
        else:
            masked_chars.append("*")

    return "".join(masked_chars)


def extract_message_from_update(update: Update) -> Message | None:
    if update.message is not None:
        return update.message

    if update.edited_message is not None:
        return update.edited_message

    if update.callback_query is not None:
        callback_message = update.callback_query.message
        if isinstance(callback_message, Message):
            return callback_message

    return None
