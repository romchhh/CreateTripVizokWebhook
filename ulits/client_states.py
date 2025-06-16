from aiogram.dispatcher.filters.state import State, StatesGroup
    
class ChangeProfile(StatesGroup):
    name = State()
    number = State()
    add_number = State()
    add_photo = State()
    

class AddCar(StatesGroup):
    waiting_for_mark = State()
    waiting_for_number = State()
    waiting_for_photo = State()
    confirm_car = State()
    
class PhoneState(StatesGroup):
    waiting_for_phone = State()
    
    
class SearchUser(StatesGroup):
    waiting_for_user = State()
    
class AddTrip(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_stops = State()
    waiting_for_repeat_time = State()
    waiting_for_repeat = State()
    waiting_for_repeat_confirmation = State()
    

class ChangeTrip(StatesGroup):
    waiting_for_changetime = State()
    waiting_for_changestops = State()
    
class SearchTrip(StatesGroup):
    waiting_for_points = State()
    waiting_for_stops = State()
    
class ReviewStates(StatesGroup):
    rating = State()
    text = State()