from main import bot, dp, scheduler

from config import *
from ulits.filters import *

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from database.client_db import update_user_language
from ulits.translate import translate
from keyboards.client_keyboards import *
from keyboards.admin_keyboards import get_admin_keyboard
from ulits.client_functions import my_profile, get_trip_text
from ulits.client_states import ChangeProfile, AddCar, ReviewStates
from aiogram.types.message import ContentType
from database.client_db import conn, cursor, update_user_username
import asyncio, os
from data.texts import cancel_texts, my_profile_text, my_trips_text



    
@dp.message_handler(lambda message: message.text.lower() in map(str.lower, my_profile_text.values()), state='*')
async def my_profile_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await my_profile(message)
    

@dp.message_handler(lambda message: message.text.lower() in map(str.lower, my_trips_text.values()), state='*')
async def my_trips(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    user_id = message.from_user.id

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("🚗 Активні поїздки", user_id), callback_data="active_trips"),
        InlineKeyboardButton(translate("📚 Архів поїздок", user_id), callback_data="archived_trips")
    )

    await message.answer(
        translate("Оберіть тип поїздок для перегляду:", user_id),
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data in ["active_trips", "archived_trips"])
async def show_trips(call: types.CallbackQuery):
    user_id = call.from_user.id
    is_archive = call.data == "archived_trips"
    
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    if is_archive:
        cursor.execute(
            """
            SELECT id, date, time, car_mark, car_number, stops, seats, watched 
            FROM trips 
            WHERE user_id = ? AND date < ? 
            ORDER BY date DESC, time DESC
            """,
            (user_id, today_str)
        )
    else:
        cursor.execute(
            """
            SELECT id, date, time, car_mark, car_number, stops, seats, watched 
            FROM trips 
            WHERE user_id = ? AND date >= ? 
            ORDER BY date ASC, time ASC
            """,
            (user_id, today_str)
        )
    
    trips = cursor.fetchall()
    
    if not trips:
        no_trips_text = translate("У вас немає поїздок в архіві.", user_id) if is_archive else translate("У вас немає активних поїздок.", user_id)
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_trips")
        )
        await call.message.edit_text(no_trips_text, reply_markup=keyboard)
        return
    
    current_page = 0  
    trip = trips[current_page]
    trip_text = get_trip_text(trip, user_id) 

    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if not is_archive:
        keyboard.add(
            InlineKeyboardButton(translate("✏ Редагувати", user_id), callback_data=f"edit_trip_{trip[0]}"),
            InlineKeyboardButton(translate("🗑 Видалити", user_id), callback_data=f"deletetrip_{trip[0]}")
        )
    
    navigation_buttons = []
    if len(trips) > 1:
        repeat_button = InlineKeyboardButton(
            translate("♻️ Повторити поїздку", user_id), 
            callback_data=f"repeat_trip_{trip[0]}"
        )
        prev_button = InlineKeyboardButton(
            translate("⬅ Попередня", user_id) if current_page > 0 else " ",
            callback_data=f"prevpage_{current_page - 1}_{is_archive}" if current_page > 0 else "none"
        )
        next_button = InlineKeyboardButton(
            translate("➡ Наступна", user_id) if current_page < len(trips) - 1 else " ",
            callback_data=f"nextpage_{current_page + 1}_{is_archive}" if current_page < len(trips) - 1 else "none"
        )
        navigation_buttons = [prev_button, next_button]
        keyboard.add(repeat_button)
        keyboard.row(*navigation_buttons)
    

    
    keyboard.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_trips"))

    await call.message.edit_text(
        trip_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "back_to_trips")
async def back_to_trips_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("🚗 Активні поїздки", user_id), callback_data="active_trips"),
        InlineKeyboardButton(translate("📚 Архів поїздок", user_id), callback_data="archived_trips")
    )

    await call.message.edit_text(
        translate("Оберіть тип поїздок для перегляду:", user_id),
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith(("nextpage_", "prevpage_")))
async def navigate_trips(call: types.CallbackQuery):
    if call.data == "none":
        await call.answer()
        return
        
    user_id = call.from_user.id
    parts = call.data.split("_")
    action = parts[0]  # nextpage або prevpage
    page = int(parts[1])  # номер сторінки
    is_archive = parts[2].lower() == "true"  # конвертуємо рядок в булеве значення
    
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    if is_archive:
        cursor.execute(
            """
            SELECT id, date, time, car_mark, car_number, stops, seats, watched 
            FROM trips 
            WHERE user_id = ? AND date < ? 
            ORDER BY date DESC, time DESC
            """,
            (user_id, today_str)
        )
    else:
        cursor.execute(
            """
            SELECT id, date, time, car_mark, car_number, stops, seats, watched 
            FROM trips 
            WHERE user_id = ? AND date >= ? 
            ORDER BY date ASC, time ASC
            """,
            (user_id, today_str)
        )
    
    trips = cursor.fetchall()
    
    if 0 <= page < len(trips):
        trip = trips[page]
        trip_text = get_trip_text(trip, user_id)
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if not is_archive:
            keyboard.add(
                InlineKeyboardButton(translate("✏ Редагувати", user_id), callback_data=f"edit_trip_{trip[0]}"),
                InlineKeyboardButton(translate("🗑 Видалити", user_id), callback_data=f"deletetrip_{trip[0]}")
            )

        repeat_button = InlineKeyboardButton(
            translate("♻️ Повторити поїздку", user_id), 
            callback_data=f"repeat_trip_{trip[0]}"
        )
        
        prev_button = InlineKeyboardButton(
            translate("⬅ Попередня", user_id) if page > 0 else " ",
            callback_data=f"prevpage_{page-1}_{is_archive}" if page > 0 else "none"
        )
        next_button = InlineKeyboardButton(
            translate("➡ Наступна", user_id) if page < len(trips) - 1 else " ",
            callback_data=f"nextpage_{page+1}_{is_archive}" if page < len(trips) - 1 else "none"
        )

        navigation_buttons = [prev_button, next_button]
        keyboard.add(repeat_button)
        keyboard.row(*navigation_buttons)
        
        keyboard.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_trips"))
        
        await call.message.edit_text(trip_text, parse_mode="HTML", reply_markup=keyboard)
    
    await call.answer()



@dp.callback_query_handler(lambda c: c.data == "none")
async def handle_none_callback(call: types.CallbackQuery):
    await call.answer()

@dp.callback_query_handler(lambda call: call.data.startswith("set_language_"))
async def set_language(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = call.from_user.username
    language_code = call.data.split("_")[-1]

    update_user_language(user_id, language_code)
    keyboard = get_admin_keyboard(user_id) if user_id in administrators else get_start_keyboard(user_id)

    language_name = {
        "uk": "Українська",
        "pl": "Polski",
        "en": "English",
        "de": "Deutsch",
        "cs": "Čeština",
        "bg": "Български",
        "ro": "Română",
        "hu": "Magyar",
        "it": "Italiano",
        "es": "Español",
    }.get(language_code, "Обрана мова")

    await call.message.edit_reply_markup()  
    caption = translate("Дякуємо! Ви обрали мову: ", user_id)
    await call.message.edit_text(f"{caption}<b>{language_name}</b>.", parse_mode="HTML")
    
    greeting_message = translate(f"Вітаємо, {user_name}! 👋 \nВи звернулися до сервісу спільних поїздок <b>Vizok</b> 🚙.\nЧим можемо бути корисні?", user_id)
    photo_path = 'data/hello.jpg'
    with open(photo_path, 'rb') as photo:
            await call.message.answer_photo(photo=photo, caption=greeting_message, reply_markup=keyboard)
    


@dp.callback_query_handler(lambda call: call.data == "refresh_username")
async def refresh_username(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = call.from_user.username
    update_user_username(user_id, user_name)
    await call.answer(translate("Юзернейм успішно оновлено.", user_id), show_alert=True)
    await asyncio.sleep(0.5)
    await call.message.delete()
    await my_profile(message=call.message, user_id = call.from_user.id)
    await call.answer()

@dp.callback_query_handler(lambda call: call.data == "change_lang")
async def change_language_prompt(call: types.CallbackQuery):
    user_id = call.from_user.id
    keyboard = change_language_keyboard()

    await call.message.edit_text(translate("Оберіть мову інтерфейсу:", user_id), reply_markup=keyboard
    )
    await call.answer() 
    
    
@dp.callback_query_handler(lambda call: call.data == "change_name")
async def change_language_prompt(call: types.CallbackQuery):
    user_id = call.from_user.id

    await call.message.edit_text(translate("Введіть ваше ім'я або поверніться назад до профілю:", user_id), reply_markup=back_to_profile(user_id)
    )
    await call.answer() 
    await ChangeProfile.name.set()
    
    
@dp.message_handler(state=ChangeProfile.name)
async def process_new_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await my_profile(message)
        await state.finish()
        return
    new_name = message.text.strip()
    cursor.execute("UPDATE users SET real_name = ? WHERE user_id = ?", (new_name, user_id))
    conn.commit()
    
    await message.answer(translate("✔ Ваше ім'я успішно оновлено.", user_id))
    await asyncio.sleep(0.5)
    await my_profile(message)
    await state.finish()
    
    

@dp.callback_query_handler(lambda call: call.data == "my_photo")
async def change_language_prompt(call: types.CallbackQuery):
    user_id = call.from_user.id

    cursor.execute("SELECT photo FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    photo_path = result[0] if result else None
    if photo_path:
        with open(photo_path, 'rb') as photo_file:
            await call.message.answer_photo(photo_file, caption=translate("Ось фото вашого профілю:", user_id), reply_markup=change_photo_keyboard(user_id))
    else:
        await call.message.edit_text(translate("Ви ще не додали особистого фото. Ви можете додати його:", user_id), reply_markup=add_photo_keyboard(user_id))
    await call.answer()

    
@dp.callback_query_handler(lambda call: call.data == "delete_photo")
async def delete_photo_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute("SELECT photo FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    photo_path = result[0] if result else None

    if photo_path:
        os.remove(photo_path) 
        cursor.execute("UPDATE users SET photo = NULL WHERE user_id = ?", (user_id,))
        conn.commit()

    await call.message.delete()
    await call.message.answer(translate("Фото успішно видалено.", user_id), reply_markup=back_to_profile(user_id))
    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id = call.from_user.id)

    
@dp.callback_query_handler(lambda call: call.data == "addphoto")
async def add_photo_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.edit_text(translate("Будь ласка, надішліть своє особисте фото, вибравши його з галереї (натисніть на значок скріпки 📎) або напишіть команду /start, якщо хочете відмінити цей крок.", user_id), reply_markup=back_to_profile(user_id))
    await ChangeProfile.add_photo.set()
    

@dp.callback_query_handler(lambda call: call.data == "change_photo")
async def add_photo_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.answer(translate("Будь ласка, надішліть своє особисте фото, вибравши його з галереї (натисніть на значок скріпки 📎) або напишіть команду /start, якщо хочете відмінити цей крок.", user_id), reply_markup=back_to_profile(user_id))
    await ChangeProfile.add_photo.set()
    
    
@dp.message_handler(content_types=[ContentType.PHOTO, ContentType.TEXT], state=ChangeProfile.add_photo)
async def preview_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo = message.photo[-1] 
    file_id = photo.file_id

    await state.update_data(file_id=file_id)

    keyboard = InlineKeyboardMarkup()
    confirm_button = InlineKeyboardButton(translate("✅ Підтвердити", user_id), callback_data="confirm_photo")
    cancel_button = InlineKeyboardButton(translate("❌ Відхилити", user_id), callback_data="cancel_photo")
    keyboard.add(confirm_button, cancel_button)

    await message.answer_photo(photo=file_id, caption=translate("Попередній перегляд фото:", user_id), reply_markup=keyboard)
    

@dp.callback_query_handler(lambda call: call.data == "confirm_photo", state=ChangeProfile.add_photo)
async def confirm_photo_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    data = await state.get_data()
    file_id = data.get("file_id")

    if file_id:
        directory = f"profile/{user_id}"
        file_path = f"{directory}/profile_photo.jpg"

        os.makedirs(directory, exist_ok=True)

        if os.path.exists(file_path):
            os.remove(file_path)

        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, file_path)

        cursor.execute("UPDATE users SET photo = ? WHERE user_id = ?", (file_path, user_id))
        conn.commit()

        await call.message.delete()
        await call.message.answer(translate("Ваше фото збережено!", user_id))
    else:
        await call.message.answer(translate("Щось пішло не так, будь ласка, спробуйте ще раз.", user_id))

    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id=call.from_user.id)
    await state.finish()

    

@dp.callback_query_handler(lambda call: call.data == "cancel_photo", state=ChangeProfile.add_photo)
async def cancel_photo_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.finish()
    await call.message.delete()
    await call.message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id = call.from_user.id)

     

@dp.callback_query_handler(lambda call: call.data == "my_cars")
async def change_language_prompt(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute("SELECT id, mark, number FROM users_cars WHERE user_id = ?", (user_id,))
    cars = cursor.fetchall()

    keyboard = InlineKeyboardMarkup(row_width=1)
    for car_id, mark, number in cars:
        button_text = f"{mark} : {number}"
        button = InlineKeyboardButton(text=button_text, callback_data=f"car_{car_id}")
        keyboard.add(button)

    if len(cars) < 2:
        create_button = InlineKeyboardButton(translate("➕ Додати авто", user_id), callback_data="create_car")
        keyboard.add(create_button)

    back_button = InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_profile")
    keyboard.add(back_button)

    await call.message.edit_text(translate("Ваші автомобілі:", user_id), reply_markup=keyboard)



@dp.callback_query_handler(lambda c: c.data.startswith('car_'))
async def get_car_info(call: types.CallbackQuery):
    car_id = int(call.data.split('_')[1])
    cursor.execute("SELECT mark, number, photo_path FROM users_cars WHERE id = ?", (car_id,))
    car_data = cursor.fetchone()
    
    if car_data:
        mark, number, photo_path = car_data

        car_info = f"<b>Марка та модель:</b> {mark}\n<b>Номер:</b> {number}"
        keyboard = get_car_info_keyboard(car_id, user_id=call.from_user.id)
        
        if photo_path:
            with open(photo_path, 'rb') as photo:
                await call.message.answer_photo(photo, parse_mode="HTML", caption=car_info, reply_markup=keyboard)
        else:
            await call.message.answer(car_info, parse_mode="HTML", reply_markup=keyboard)
    else:
        await call.message.answer("Інформація про авто не знайдена.")
    await call.answer()
    
    
@dp.callback_query_handler(lambda c: c.data.startswith('delete_car_'))
async def delete_car(call: types.CallbackQuery):
    car_id = int(call.data.split('_')[2])
    cursor.execute("SELECT photo_path FROM users_cars WHERE id = ?", (car_id,))
    car_data = cursor.fetchone()
    
    if car_data:
        photo_path = car_data[0]
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
  
        cursor.execute("DELETE FROM users_cars WHERE id = ?", (car_id,))
        conn.commit()
        
        await call.message.delete()
        await call.message.answer("Ваше авто було видалено з профілю.")
        await my_profile(message=call.message, user_id = call.from_user.id)
    else:
        await call.message.answer("Не вдалося знайти авто для видалення.") 
    await call.answer()
    
@dp.callback_query_handler(text="create_car")
async def start_create_car(call: types.CallbackQuery):
    user_id = call.from_user.id
    await AddCar.waiting_for_mark.set()
    await call.message.answer("Введіть марку та модель вашого авто:", reply_markup=get_cancel_keyboard(user_id))


@dp.message_handler(state=AddCar.waiting_for_mark)
async def get_car_mark(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await my_profile(message)
        await state.finish()
        return

    await state.update_data(mark=message.text)
    await AddCar.waiting_for_number.set()
    await message.answer("Введіть реєстраційний номер вашого авто:", reply_markup=get_cancel_keyboard(user_id))


@dp.message_handler(state=AddCar.waiting_for_number)
async def get_car_model(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await my_profile(message)
        await state.finish()
        return
    upper_case_number = message.text.upper()

    await state.update_data(number=upper_case_number)
    await AddCar.waiting_for_photo.set()
    await message.answer("Будь ласка, додайте фото вашого авто, вибравши його з галереї (натисніть на значок скріпки 📎) або напишіть команду /skip, якщо хочете пропустити цей крок.", reply_markup=get_cancel_keyboard(user_id))


@dp.message_handler(state=AddCar.waiting_for_photo, content_types=[ContentType.PHOTO])
async def get_car_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    photo = message.photo[-1]

    await state.update_data(photo_file_id=photo.file_id)
    await proceed_to_preview(message, state)


@dp.message_handler(state=AddCar.waiting_for_photo, content_types=ContentType.TEXT)
async def skip_car_photo(message: Message, state: FSMContext):
    if message.text == "/skip":
        await proceed_to_preview(message, state)
        return

async def proceed_to_preview(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    
    mark = data.get('mark')
    number = data.get('number')
    photo_file_id = data.get('photo_file_id', None)
  
    preview_text = f"Марка: {mark}\nНомер: {number}"
    
    if photo_file_id:
        await message.answer_photo(photo_file_id, caption=preview_text, reply_markup=confirm_car_adding(user_id))
    else:       
        await message.answer(preview_text, reply_markup=confirm_car_adding(user_id))
    
    await AddCar.confirm_car.set()


@dp.callback_query_handler(text="confirm_car", state=AddCar.confirm_car)
async def confirm_car(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    
    mark = data.get('mark')
    number = data.get('number')
    photo_file_id = data.get('photo_file_id', None)

    if photo_file_id:
        photo = await call.bot.get_file(photo_file_id)
        file_path = f"cars/{user_id}/{photo_file_id}.jpg"
        await call.bot.download_file(photo.file_path, file_path)
        photo_path = file_path
    else:
        photo_path = None

    cursor.execute("INSERT INTO users_cars (user_id, mark, number, photo_path) VALUES (?, ?, ?, ?)", 
                   (user_id, mark, number, photo_path))
    conn.commit()
    
    await call.message.delete()
    await call.message.answer("Ваше авто успішно додано до профілю!", reply_markup=get_start_keyboard(user_id))
    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id = call.from_user.id)
    await state.finish()


@dp.callback_query_handler(text="cancel_car", state=AddCar.confirm_car)
async def cancel_car(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await call.message.delete()
    await call.message.answer("Створення авто скасовано.", reply_markup=get_start_keyboard(user_id))
    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id = call.from_user.id)
    await state.finish()




@dp.callback_query_handler(lambda call: call.data == "my_numbers")
async def my_numbers(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute("SELECT phone, phone2 FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        phone, phone2 = user_data
        
        keyboard = get_phone_numbers_keyboard(phone, phone2, user_id)
        
        if phone or phone2:
            await call.message.edit_text("Ось ваші номери:", reply_markup=keyboard)
        else:
            await call.message.edit_text("У вас ще немає номерів.", reply_markup=keyboard)
    else:
        await call.message.answer("Неможливо знайти ваші дані.")
    
    await call.answer()

@dp.callback_query_handler(lambda call: call.data.startswith("phone_") or call.data.startswith("phone2_"))
async def phone_options(call: types.CallbackQuery):
    user_id = call.from_user.id
    phone_data = call.data.split('_')
    phone_type = phone_data[0]
    phone_number = phone_data[1]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("Змінити номер", user_id), callback_data=f"change_{phone_type}_{phone_number}"),
        InlineKeyboardButton(translate("Видалити номер", user_id), callback_data=f"delete_{phone_type}_{phone_number}"),
        InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_to_profile")
    )
    
    await call.message.edit_text(f"Вибрано {phone_type.replace('phone', 'Телефон')} {phone_number}. Оберіть дію:", reply_markup=keyboard)
    await call.answer()
    
    
@dp.callback_query_handler(lambda call: call.data.startswith("change_"))
async def change_phone_number(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    phone_data = call.data.split('_')
    phone_type = phone_data[1]
    old_phone = phone_data[2]

    await call.message.answer(translate(f"Введіть новий номер для {phone_type.replace('phone', 'Телефон')} {old_phone}:", user_id), reply_markup=get_cancel_keyboard(user_id))
    
    await ChangeProfile.number.set()
    await state.update_data(old_phone=old_phone, phone_type=phone_type)
    await call.answer()


@dp.message_handler(state=ChangeProfile.number) 
async def save_new_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_phone = message.text.strip()
    
    # Перевіряємо, чи номер починається з "+" і містить тільки цифри після нього
    if new_phone.startswith('+'):
        digits_only = new_phone[1:]  # Видаляємо "+" для перевірки цифр
    else:
        digits_only = new_phone
        
    if not digits_only.isdigit():
        await message.answer("Номер телефону повинен містити тільки цифри та може починатися з '+'.")
        return
        
    if len(new_phone) < 10 or len(new_phone) > 15:
        await message.answer("Номер телефону повинен містити від 10 до 15 символів. Спробуйте ще раз.")
        return

    cursor.execute("SELECT phone, phone2 FROM users WHERE user_id = ?", (user_id,))
    phones = cursor.fetchone()
    phone, phone2 = phones
    if not phone:
        cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (new_phone, user_id))
        conn.commit()
        await message.answer(f"Номер телефону {new_phone} успішно додано як перший номер.")
  
    elif not phone2:
        cursor.execute("UPDATE users SET phone2 = ? WHERE user_id = ?", (new_phone, user_id))
        conn.commit()
        await message.answer(f"Номер телефону {new_phone} успішно додано як другий номер.")
    
    else:
        await message.answer("У вас вже є два номери телефону.")
    await state.finish()
    await asyncio.sleep(0.5)
    await my_profile(message)


@dp.callback_query_handler(lambda call: call.data.startswith("delete_"))
async def delete_phone_number(call: types.CallbackQuery):
    phone_data = call.data.split('_')
    phone_type = phone_data[1]
    phone_number = phone_data[2]
    
    user_id = call.from_user.id

    if phone_type == "phone":
        cursor.execute("UPDATE users SET phone = NULL WHERE user_id = ? AND phone = ?", 
                       (user_id, phone_number))
    elif phone_type == "phone2":
        cursor.execute("UPDATE users SET phone2 = NULL WHERE user_id = ? AND phone2 = ?", 
                       (user_id, phone_number))

    conn.commit()
    
    await call.message.delete()
    await call.message.answer(f"Номер {phone_number} видалено.")
    await asyncio.sleep(0.5)
    await my_profile(message=call.message, user_id = call.from_user.id)
    await call.answer()


@dp.callback_query_handler(lambda call: call.data == "create_number")
async def create_phone_number(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await call.message.answer("Будь ласка, введіть новий номер телефону:", reply_markup=get_cancel_keyboard(user_id))

    await ChangeProfile.add_number.set()
    await state.update_data(action="create_phone")
    await call.answer()
    
    
@dp.message_handler(state=ChangeProfile.add_number) 
async def save_new_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await my_profile(message)
        await state.finish()
        return
    user_id = message.from_user.id
    new_phone = message.text.strip()
    
    # Перевіряємо, чи номер починається з "+" і містить тільки цифри після нього
    if new_phone.startswith('+'):
        digits_only = new_phone[1:]  # Видаляємо "+" для перевірки цифр
    else:
        digits_only = new_phone
        
    if not digits_only.isdigit():
        await message.answer("Номер телефону повинен містити тільки цифри та може починатися з '+'.")
        return
        
    if len(new_phone) < 10 or len(new_phone) > 15:
        await message.answer("Номер телефону повинен містити від 10 до 15 символів. Спробуйте ще раз.")
        return

    cursor.execute("SELECT phone, phone2 FROM users WHERE user_id = ?", (user_id,))
    phones = cursor.fetchone()
    phone, phone2 = phones
    if not phone:
        cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (new_phone, user_id))
        conn.commit()
        await message.answer(f"Номер телефону {new_phone} успішно додано як перший номер.", reply_markup=get_start_keyboard(user_id))
  
    elif not phone2:
        cursor.execute("UPDATE users SET phone2 = ? WHERE user_id = ?", (new_phone, user_id))
        conn.commit()
        await message.answer(f"Номер телефону {new_phone} успішно додано як другий номер.", reply_markup=get_start_keyboard(user_id))
    
    else:
        await message.answer("У вас вже є два номери телефону.", reply_markup=get_start_keyboard(user_id))
    await state.finish()
    await asyncio.sleep(0.5)
    await my_profile(message)

    
@dp.callback_query_handler(lambda call: call.data == "back_to_profile", state=[ChangeProfile.name, ChangeProfile.add_number, ChangeProfile.add_photo, None])
async def back_to_profile_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await my_profile(call.message, user_id, call.message)

@dp.callback_query_handler(lambda call: call.data == "back_from_photo", state=[ChangeProfile.name, ChangeProfile.add_number, ChangeProfile.add_photo, None])
async def back_to_profile_handler(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await call.message.delete()
    
    

@dp.callback_query_handler(lambda c: c.data.startswith('send_review_'))
async def start_review_process(callback_query: types.CallbackQuery):
    phone_data = callback_query.data.split('_')
    driver_id = phone_data[2]
    user_id = callback_query.from_user.id
    
    await callback_query.message.edit_text("Будь ласка оцініть якість спілкування від 1 до 5. ✔️", reply_markup=get_rating_keyboard(driver_id))

@dp.callback_query_handler(lambda c: c.data.startswith('rate_'), state='*')
async def process_rating(callback_query: types.CallbackQuery, state: FSMContext):
    rating = int(callback_query.data.split('_')[1])
    driver_id = int(callback_query.data.split('_')[2])
    user_id = callback_query.from_user.id
    date_today = datetime.now().strftime('%Y-%m-%d')  

    cursor.execute('''INSERT INTO reviews (receiver_id, sender_id, stars, date)
                      VALUES (?, ?, ?, ?)''', (driver_id, user_id, rating, date_today))
    conn.commit()

    await state.update_data(rating=rating, driver_id=driver_id, user_id=user_id, date_today=date_today)
    await ReviewStates.text.set()
    await callback_query.message.answer("Будь ласка, введіть текст відгуку:", reply_markup=get_cancel_keyboard(user_id))

@dp.message_handler(state=ReviewStates.text)
async def process_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await state.finish()
        return
    user_data = await state.get_data()
    rating = user_data.get('rating')
    driver_id = user_data.get('driver_id')
    date_today = user_data.get('date_today')
    text = message.text

    cursor.execute('''UPDATE reviews 
                      SET text = ? 
                      WHERE receiver_id = ? AND sender_id = ? AND date = ?''', 
                      (text, driver_id, user_id, date_today))
    conn.commit()
    await bot.send_message(message.chat.id, f"Дякуємо за зворотний зв'язок. Ми цінуємо вашу думку 💚", reply_markup=get_start_keyboard(user_id))
    await state.finish()
    
    

