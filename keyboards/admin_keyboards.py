from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from ulits.translate import translate

def get_admin_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.row(KeyboardButton("Адмін панель 💻"))
    keyboard.row(KeyboardButton(translate("Створити поїздку", user_id)), KeyboardButton(translate("Знайти поїздку", user_id)))
    keyboard.row(KeyboardButton(translate("Мій профіль", user_id)), KeyboardButton(translate("Шукати користувача", user_id)))
    keyboard.row(KeyboardButton(translate("Про нас", user_id)), KeyboardButton(translate("Мої поїздки", user_id))),
    
    return keyboard


def admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Розсилка"))
    keyboard.row(KeyboardButton("Статистика"), KeyboardButton("Вигрузити БД"))
    keyboard.row(KeyboardButton("Список водіїв"), KeyboardButton("Список пасажирів"))
    keyboard.row(KeyboardButton("Головне меню"), KeyboardButton("Популярні маршрути"))
    keyboard.row(KeyboardButton("Статистика посилань"))
    return keyboard


def get_broadcast_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    back_button = InlineKeyboardButton("Зробити розсилку", callback_data="create_post")
    keyboard.add(back_button)
    return keyboard


def create_post(user_data, user_id, url_buttons=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if url_buttons:
        for row in url_buttons:
            keyboard.row(*[InlineKeyboardButton(button_text, url=button_url) for button_text, button_url in row])

    keyboard.add(
        InlineKeyboardButton("Медіа", callback_data=f"media_"),
        InlineKeyboardButton("Додати опис", callback_data=f"add_"),
        InlineKeyboardButton("🔔" if user_data.get(user_id, {}).get('bell', 0) == 1 else "🔕", callback_data=f"bell_"),
        InlineKeyboardButton("URL-кнопки", callback_data=f"url_buttons_"),
    )
    keyboard.add(
        InlineKeyboardButton("← Відміна", callback_data=f"back_to"),
        InlineKeyboardButton("Далі →", callback_data=f"next_")
    )

    return keyboard

def publish_post(user_data, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("💈 Опублікувати", callback_data=f"publish_"),
        InlineKeyboardButton("← Назад", callback_data=f"back_to")
    )

    return keyboard

def post_keyboard(user_data, user_id, url_buttons=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    rating = user_data[user_id].get('rating', 0) 

    if url_buttons:
        for row in url_buttons:
            keyboard.row(*[InlineKeyboardButton(button_text, url=button_url) for button_text, button_url in row]) 
    return keyboard


def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("← Скасувати"))
    return keyboard
