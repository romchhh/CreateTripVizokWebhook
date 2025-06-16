from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from ulits.translate import translate, SUPPORTED_LANGUAGES
import calendar
from database.client_db import check_user_language
from data.texts import today_text, month_names, week_days, back_button, am_header_text, pm_header_text

def get_start_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton(translate("Створити поїздку", user_id)), KeyboardButton(translate("Знайти поїздку", user_id)))
    keyboard.row(KeyboardButton(translate("Мій профіль", user_id)), KeyboardButton(translate("Шукати користувача", user_id)))
    keyboard.row(KeyboardButton(translate("Про нас", user_id)), KeyboardButton(translate("Мої поїздки", user_id)))
    return keyboard


def language_keyboard():
    languages = [
        ("Українська", "uk"),
        ("Polski", "pl"),
        ("English", "en"),
        ("Deutsch", "de"),
        ("Čeština", "cs"),
        ("Български", "bg"),
        ("Română", "ro"),
        ("Magyar", "hu"),
        ("Italiano", "it"),
        ("Español", "es"),
    ]

    language_buttons = [
        InlineKeyboardButton(text=lang[0], callback_data=f"set_language_{lang[1]}")
        for lang in languages
        ]

    inline_keyboard = InlineKeyboardMarkup(row_width=2).add(*language_buttons)
    return inline_keyboard


def my_profile_keybpard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("📸 Особисте фото", user_id), callback_data="my_photo"),
        InlineKeyboardButton(translate("👤 Оновити телеграм юзернейм", user_id), callback_data="refresh_username"),
        InlineKeyboardButton(translate("✏️ Змінити ім'я", user_id), callback_data="change_name"),
        InlineKeyboardButton(translate("🌎 Змінити мову інтерфейсу", user_id), callback_data="change_lang"),
        InlineKeyboardButton(translate("📞 Мої номери", user_id), callback_data="my_numbers"),
        InlineKeyboardButton(translate("🚘 Мої авто", user_id), callback_data="my_cars")
    )
    return keyboard


def change_language_keyboard():
    languages = [
        ("Українська", "uk"),
        ("Polski", "pl"),
        ("English", "en"),
        ("Deutsch", "de"),
        ("Čeština", "cs"),
        ("Български", "bg"),
        ("Română", "ro"),
        ("Magyar", "hu"),
        ("Italiano", "it"),
        ("Español", "es"),
    ]
    language_buttons = [
        InlineKeyboardButton(text=lang[0], callback_data=f"set_language_{lang[1]}")
        for lang in languages
    ]
    back_button = InlineKeyboardButton("← Назад", callback_data="back_to_profile")
    inline_keyboard = InlineKeyboardMarkup(row_width=2).add(*language_buttons, back_button)
    return inline_keyboard


def edit_trip_keyboard(user_id, trip_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("📅 Змінити дату", user_id), callback_data=f"changedate_{trip_id}"),
        InlineKeyboardButton(translate("🕒 Змінити час", user_id), callback_data=f"changetime_{trip_id}"),
        InlineKeyboardButton(translate("🚗 Змінити авто", user_id), callback_data=f"changecar_{trip_id}"),
        InlineKeyboardButton(translate("👥 Змінити кількість місць", user_id), callback_data=f"changeseats_{trip_id}"),
        InlineKeyboardButton(translate("📍 Змінити маршрут", user_id), callback_data=f"changestops_{trip_id}"),
        InlineKeyboardButton(translate("← Назад", user_id), callback_data="cancel_delete_trip_")
    )
    return keyboard


def back_to_profile(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_profile"),
    )
    return keyboard


def get_cancel_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(translate("← Скасувати", user_id)))
    return keyboard


def confirm_car_adding(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    confirm_button = InlineKeyboardButton(translate("✅ Підтвердити", user_id), callback_data="confirm_car")
    cancel_button = InlineKeyboardButton(translate("❌ Скасувати", user_id), callback_data="cancel_car")
    keyboard.add(confirm_button, cancel_button)
    return keyboard

def get_car_info_keyboard(car_id, user_id):
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(translate("Видалити авто", user_id), callback_data=f"delete_car_{car_id}"),
        InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_from_photo")
    )
    
    
def get_phone_numbers_keyboard(phone, phone2, user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if phone:
        keyboard.add(InlineKeyboardButton(f"Телефон 1: {phone}", callback_data=f"phone_{phone}"))
        if not phone2:
            keyboard.add(InlineKeyboardButton(translate("➕ Додати номер", user_id), callback_data="create_number"))
    if phone2:
        keyboard.add(InlineKeyboardButton(f"Телефон 2: {phone2}", callback_data=f"phone2_{phone2}"))   
    if not phone and not phone2:
        keyboard.add(InlineKeyboardButton(translate("➕ Додати номер", user_id), callback_data="create_number"))  
    keyboard.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_profile"))
    return keyboard


def change_photo_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    delete_button = InlineKeyboardButton(translate("🗑 Видалити фото", user_id), callback_data="delete_photo")
    change_button = InlineKeyboardButton(translate("🔄 Змінити фото", user_id), callback_data="change_photo")
    back_button = InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_from_photo")
    keyboard.add(delete_button, change_button)
    keyboard.add(back_button)
    return keyboard


def add_photo_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    add_button = InlineKeyboardButton(translate("➕ Додати фото", user_id), callback_data="addphoto")
    back_button = InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_profile")
    keyboard.add(add_button)
    keyboard.add(back_button)
    return keyboard



def no_trips_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    add_button = InlineKeyboardButton(translate("🔎 Новий пошук", user_id), callback_data="new_search")
    back_button = InlineKeyboardButton(translate("Ⓜ️ Головне меню", user_id), callback_data="back_to_main_menu")
    keyboard.add(add_button)
    keyboard.add(back_button)
    return keyboard



def create_search_calendar(user_id, year=None, month=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    user_language = check_user_language(user_id)
    if user_language not in SUPPORTED_LANGUAGES:
        user_language = 'uk'  # За замовчуванням українська

    calendar_markup = []
    
    header = [InlineKeyboardButton(f"{month_names[user_language][month]} {year}", callback_data="ignore")]
    calendar_markup.append(header)

    week_header = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days[user_language]]
    calendar_markup.append(week_header)

    month_calendar = calendar.monthcalendar(year, month)

    for week in month_calendar:
        week_buttons = []
        for day in week:
            if day == 0:
                week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                current_date = datetime(year, month, day)
                if current_date.date() < now.date():
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    week_buttons.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"search_{year}-{month:02d}-{day:02d}"
                    ))
        calendar_markup.append(week_buttons)

    navigation = [
        InlineKeyboardButton("←", callback_data=f"calendar_nav_search_prev_{year}_{month}"),
        InlineKeyboardButton(today_text[user_language], callback_data=f"search_{now.year}-{now.month:02d}-{now.day:02d}"),
        InlineKeyboardButton("→", callback_data=f"calendar_nav_search_next_{year}_{month}")
    ]
    calendar_markup.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=calendar_markup)




def create_trip_calendar(user_id, year=None, month=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    user_language = check_user_language(user_id)
    if user_language not in SUPPORTED_LANGUAGES:
        user_language = 'uk'  # За замовчуванням українська

    calendar_markup = []
    
    header = [InlineKeyboardButton(f"{month_names[user_language][month]} {year}", callback_data="ignore")]
    calendar_markup.append(header)

    week_header = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days[user_language]]
    calendar_markup.append(week_header)

    month_calendar = calendar.monthcalendar(year, month)

    for week in month_calendar:
        week_buttons = []
        for day in week:
            if day == 0:
                week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                current_date = datetime(year, month, day)
                if current_date.date() < now.date():
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    week_buttons.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"createtrip_{year}-{month:02d}-{day:02d}"
                    ))
        calendar_markup.append(week_buttons)

    navigation = [
        InlineKeyboardButton("←", callback_data=f"calendar_nav_create_prev_{year}_{month}"),
        InlineKeyboardButton(today_text[user_language], callback_data=f"createtrip_{now.year}-{now.month:02d}-{now.day:02d}"),
        InlineKeyboardButton("→", callback_data=f"calendar_nav_create_next_{year}_{month}")
    ]
    calendar_markup.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=calendar_markup)



def create_edit_calendar(user_id, trip_id, year=None, month=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    today_day = now.day if (year == now.year and month == now.month) else None

    user_language = check_user_language(user_id)
    if user_language not in SUPPORTED_LANGUAGES:
        user_language = 'uk'  # За замовчуванням українська

    keyboard = []
    keyboard.append([
        InlineKeyboardButton(
            text=f"{month_names[user_language][month]} {year}",
            callback_data="ignore"
        )
    ])
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in week_days[user_language]])
    
    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:  
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                day_text = f"🔹{day}" if day == today_day else str(day)
                row.append(
                    InlineKeyboardButton(
                        text=day_text,
                        callback_data=f"edittrip_{year}-{month:02d}-{day:02d}_{trip_id}"
                    )
                )
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("←", callback_data=f"calendar_nav_edit_prev_{year}_{month}_{trip_id}"),
        InlineKeyboardButton(today_text[user_language], callback_data=f"edittrip_{now.year}-{now.month:02d}-{now.day:02d}_{trip_id}"),
        InlineKeyboardButton("→", callback_data=f"calendar_nav_edit_next_{year}_{month}_{trip_id}"),
    ])  
    keyboard.append([
        InlineKeyboardButton(
            text=translate("← Назад", user_id),
            callback_data="cancel_delete_trip_"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_rating_keyboard(driver_id):
    keyboard = InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        button = InlineKeyboardButton(text=f"{i}", callback_data=f"rate_{i}_{driver_id}")
        keyboard.insert(button)

    return keyboard





def create_trip_calendar_repeat(user_id, year=None, month=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    user_language = check_user_language(user_id)
    if user_language not in SUPPORTED_LANGUAGES:
        user_language = 'uk'  # За замовчуванням українська

    calendar_markup = []
    
    header = [InlineKeyboardButton(f"{month_names[user_language][month]} {year}", callback_data="ignore")]
    calendar_markup.append(header)

    week_header = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days[user_language]]
    calendar_markup.append(week_header)

    month_calendar = calendar.monthcalendar(year, month)

    for week in month_calendar:
        week_buttons = []
        for day in week:
            if day == 0:
                week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                current_date = datetime(year, month, day)
                if current_date.date() < now.date():
                    week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
                else:
                    week_buttons.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"repeattrip_{year}-{month:02d}-{day:02d}"
                    ))
        calendar_markup.append(week_buttons)

    navigation = [
        InlineKeyboardButton("←", callback_data=f"calendar_nav_repeat_prev_{year}_{month}"),
        InlineKeyboardButton(today_text[user_language], callback_data=f"repeattrip_{now.year}-{now.month:02d}-{now.day:02d}"),
        InlineKeyboardButton("→", callback_data=f"calendar_nav_repeat_next_{year}_{month}")
    ]
    calendar_markup.append(navigation)
    
    # Додаємо кнопку "Назад"
    back_btn = [InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_trips")]
    calendar_markup.append(back_btn)

    return InlineKeyboardMarkup(inline_keyboard=calendar_markup)


def get_trip_keyboard(trip_id: int, user_id: int, is_archive: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if not is_archive:
        keyboard.add(
            InlineKeyboardButton(translate("✏ Редагувати", user_id), callback_data=f"edit_trip_{trip_id}"),
            InlineKeyboardButton(translate("🗑 Видалити", user_id), callback_data=f"deletetrip_{trip_id}"),
        )
    keyboard.add(
        InlineKeyboardButton(
            translate("🔄 Повторити поїздку", user_id),
            callback_data=f"repeat_trip_{'archive' if is_archive else 'active'}_{trip_id}"
        )
    )
    return keyboard


def create_hour_keyboard(user_id):
    """Створює клавіатуру для вибору години (0-23) у два стовпці з позначенням AM/PM"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Заголовки стовпців
    user_lang = check_user_language(user_id)
    keyboard.add(
        InlineKeyboardButton(am_header_text[user_lang], callback_data="ignore"),
        InlineKeyboardButton(pm_header_text[user_lang], callback_data="ignore")
    )
    
    # Створюємо кнопки для годин у два стовпці
    for i in range(12):
        am_hour = i  # 0-11 (00:00 - 11:59)
        pm_hour = i + 12  # 12-23 (12:00 - 23:59)
        
        am_text = f"{am_hour:02d}:00"
        pm_text = f"{pm_hour:02d}:00"
        
        keyboard.add(
            InlineKeyboardButton(text=am_text, callback_data=f"select_hour_{am_hour}"),
            InlineKeyboardButton(text=pm_text, callback_data=f"select_hour_{pm_hour}")
        )
    
    # Додаємо кнопку "Назад"
    keyboard.add(InlineKeyboardButton(back_button[user_lang], callback_data="back_to_date"))
    
    return keyboard


def create_minutes_keyboard(user_id, selected_hour):
    """Створює клавіатуру для вибору хвилин (00, 10, 20, 30, 40, 50)"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Створюємо кнопки для хвилин
    minutes = [0, 10, 20, 30, 40, 50]
    minute_buttons = []
    
    for minute in minutes:
        minute_str = f"{minute:02d}"
        button = InlineKeyboardButton(
            text=minute_str, 
            callback_data=f"select_minute_{selected_hour}_{minute}"
        )
        minute_buttons.append(button)
    
    # Додаємо кнопки рядами по 3
    for i in range(0, len(minute_buttons), 3):
        keyboard.add(*minute_buttons[i:i+3])
    
    # Додаємо кнопку "Назад"
    user_lang = check_user_language(user_id)
    keyboard.add(InlineKeyboardButton(back_button[user_lang], callback_data="back_to_hour"))
    
    return keyboard


def create_edit_hour_keyboard(user_id, trip_id):
    """Створює клавіатуру для вибору години при редагуванні поїздки у два стовпці з позначенням AM/PM"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Заголовки стовпців
    user_lang = check_user_language(user_id)
    keyboard.add(
        InlineKeyboardButton(am_header_text[user_lang], callback_data="ignore"),
        InlineKeyboardButton(pm_header_text[user_lang], callback_data="ignore")
    )
    
    # Створюємо кнопки для годин у два стовпці
    for i in range(12):
        am_hour = i  # 0-11 (00:00 - 11:59)
        pm_hour = i + 12  # 12-23 (12:00 - 23:59)
        
        am_text = f"{am_hour:02d}:00"
        pm_text = f"{pm_hour:02d}:00"
        
        keyboard.add(
            InlineKeyboardButton(text=am_text, callback_data=f"edit_select_hour_{am_hour}_{trip_id}"),
            InlineKeyboardButton(text=pm_text, callback_data=f"edit_select_hour_{pm_hour}_{trip_id}")
        )
    
    # Додаємо кнопку "Назад"
    keyboard.add(InlineKeyboardButton(back_button[user_lang], callback_data=f"back_to_edit_trip_{trip_id}"))
    
    return keyboard


def create_edit_minutes_keyboard(user_id, selected_hour, trip_id):
    """Створює клавіатуру для вибору хвилин при редагуванні поїздки"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Створюємо кнопки для хвилин
    minutes = [0, 10, 20, 30, 40, 50]
    minute_buttons = []
    
    for minute in minutes:
        minute_str = f"{minute:02d}"
        button = InlineKeyboardButton(
            text=minute_str, 
            callback_data=f"edit_select_minute_{selected_hour}_{minute}_{trip_id}"
        )
        minute_buttons.append(button)
    
    # Додаємо кнопки рядами по 3
    for i in range(0, len(minute_buttons), 3):
        keyboard.add(*minute_buttons[i:i+3])
    
    # Додаємо кнопку "Назад"
    user_lang = check_user_language(user_id)
    keyboard.add(InlineKeyboardButton(back_button[user_lang], callback_data=f"back_to_edit_hour_{trip_id}"))
    
    return keyboard
