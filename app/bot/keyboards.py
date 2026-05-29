from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="/contacts"),
            KeyboardButton(text="/help"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Задайте вопрос по строительству",
    )


def start_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Услуги", callback_data="menu:services"),
            InlineKeyboardButton(text="Цены", callback_data="menu:prices"),
        ],
        [
            InlineKeyboardButton(text="Сроки", callback_data="menu:timelines"),
            InlineKeyboardButton(text="Контакты", callback_data="menu:contacts"),
        ],
        [
            InlineKeyboardButton(text="Оставить заявку", callback_data="menu:lead"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
