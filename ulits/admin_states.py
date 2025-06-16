from aiogram.dispatcher.filters.state import State, StatesGroup
    
class Form(StatesGroup):
    content = State()
    media = State()
    description = State()
    url_buttons = State()
    
    
class Admin(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    


class DriverStats(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()