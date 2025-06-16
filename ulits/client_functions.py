from datetime import datetime
from aiogram import types
from config import administrators
from keyboards.admin_keyboards import get_admin_keyboard
from database.client_db import cursor, conn, get_driver_info, get_driver_reviews, get_driver_trips
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ulits.translate import translate, check_user_language 
from keyboards.client_keyboards import get_start_keyboard, my_profile_keybpard
from data.texts import profile_text, trip_text, driver_info_text, not_specified, greeting_text

SUPPORTED_LANGUAGES = {
    "uk": "Українська",
    "pl": "Polski",
    "en": "English",
    "de": "Deutsch",
    "cs": "Čeština",
    "bg": "Български",
    "ro": "Română",
    "hu": "Magyar",
    "it": "Italiano",
    "es": "Español"
}

async def my_profile(message: types.Message, user_id=None, instance=None):
    if not user_id:
        user_id = message.from_user.id  
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_info = cursor.fetchone()

    if user_info:
        user_name = user_info[2]  
        user_real_name = user_info[4] 
        phone = user_info[5]  
        phone2 = user_info[6]  
        
        date_joined = user_info[9] 

        join_date = datetime.strptime(date_joined, "%Y-%m-%d")
        days_since_joined = (datetime.now() - join_date).days
        
        trips_count = 1 
        
        def format_phone(number):
            if number:
                number = str(number)  # Перетворюємо number в рядок
                return f"+{number.lstrip('+')}"
            return not_specified[check_user_language(user_id)]
        
        phone_formatted = format_phone(phone)
        phone2_formatted = format_phone(phone2)
        
        user_language_code = check_user_language(user_id)
        language_name = SUPPORTED_LANGUAGES.get(user_language_code, user_language_code)
        
        profile_response = profile_text[user_language_code].format(
            user_id,
            user_name,
            user_real_name,
            phone_formatted,
            phone2_formatted,
            language_name,
            days_since_joined,
            trips_count
        )
        
        if instance:
            await instance.edit_text(profile_response, parse_mode="html", reply_markup=my_profile_keybpard(user_id))
        else:
            await message.answer(profile_response, parse_mode="html", reply_markup=my_profile_keybpard(user_id))
    else:
        await message.answer(translate("Ваш профіль не знайдено в системі.", user_id), parse_mode="html")

async def start_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    keyboard = get_admin_keyboard(user_id) if user_id in administrators else get_start_keyboard(user_id)
    user_language_code = check_user_language(user_id)
    
    # Якщо мова не визначена, використовуємо англійську за замовчуванням
    if user_language_code is None:
        user_language_code = 'uk'
        
    greeting_message = greeting_text[user_language_code].format(user_name)
    photo_path = 'data/hello.jpg'
    with open(photo_path, 'rb') as photo:
        await message.answer_photo(photo=photo, caption=greeting_message, reply_markup=keyboard)
       
def get_trip_text(trip, user_id):
    if isinstance(trip[1], str):
        try:
            trip_date = datetime.strptime(trip[1], "%Y-%m-%d").date()
        except ValueError:
            trip_date = trip[1] 
    else:
        trip_date = trip[1]

    watched_count = trip[7] if len(trip) > 7 else 0

    user_language_code = check_user_language(user_id)
    return trip_text[user_language_code].format(
        trip[0],
        trip_date.strftime('%d.%m.%Y'),
        trip[2],
        trip[3],
        trip[4],
        trip[5],
        trip[6],
        watched_count
    )
    
def get_driver_full_info(driver_user_id):
    driver_info = get_driver_info(driver_user_id)

    if driver_info:
        user_name, real_name, phone, phone2, photo, lang = driver_info
        trips_count = get_driver_trips(driver_user_id)
        avg_rating, reviews_count = get_driver_reviews(driver_user_id)
        avg_rating_text = f"{avg_rating:.1f}" if avg_rating is not None else "N/A"
        reviews_count_text = reviews_count if reviews_count is not None else 0

        phone = phone.lstrip("+")
        phone = f"+{phone}" if not phone.startswith("+") else phone

        phone2 = phone2.lstrip("+") if phone2 else None
        phone2 = f"+{phone2}" if phone2 and not phone2.startswith("+") else phone2
        if not phone2:
            phone2 = not_specified[lang]

        driver_profile_link = f"https://t.me/{user_name}" if user_name else f"https://t.me/{driver_user_id}"

        description = driver_info_text[lang].format(
            driver_profile_link,
            user_name,
            real_name,
            phone,
            phone2,
            trips_count,
            avg_rating_text,
            reviews_count_text
        )

        return description, photo

    return None, None
