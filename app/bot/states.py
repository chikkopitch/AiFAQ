from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    name = State()
    phone = State()
    location = State()
    service = State()
    description = State()
