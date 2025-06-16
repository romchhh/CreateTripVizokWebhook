from main import bot, dp, scheduler

from config import *
from ulits.filters import *
from datetime import datetime, timedelta
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from keyboards.admin_keyboards import get_admin_keyboard
from keyboards.client_keyboards import get_start_keyboard, get_cancel_keyboard, edit_trip_keyboard, no_trips_keyboard, create_search_calendar
from ulits.client_states import AddTrip, SearchTrip
import re, asyncio
from database.client_db import cursor, conn, get_driver_reviews_text, find_username_by_id
from ulits.translate import translate, Translator
from ulits.client_functions import start_message, get_trip_text, get_driver_full_info
from data.texts import *
import calendar
from aiogram.types import CallbackQuery

TIME_RANGE_REGEX = r"^(?:[01]?\d|2[0-3]):[0-5]?\d$"

user_trip_data = {}

user_calendar_state = {}

@dp.message_handler(lambda message: message.text.lower() in map(str.lower, start_trip_text.values()), state='*')
async def my_parcel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    user_id = message.from_user.id
    current_date = datetime.now()
    
    user_calendar_state[user_id] = {
        'year': current_date.year,
        'month': current_date.month
    }
    
    await message.answer(
        translate("<b>Оберіть дату вашої поїздки:</b>", user_id),
        parse_mode="HTML",
        reply_markup=create_search_calendar(user_id, current_date.year, current_date.month)
    )
    
@dp.callback_query_handler(lambda c: c.data.startswith("search_"))
async def handle_search_selection(callback_query: types.CallbackQuery):    
    selected_date_str = callback_query.data.split("_")[1]
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    user_id = callback_query.from_user.id

    if selected_date < today:
        await callback_query.answer(translate("❕ Ви не можете обирати дату, яка вже пройшла!", user_id), show_alert=True)
    else:
        user_id = callback_query.from_user.id
        user_trip_data[user_id] = {"date": selected_date}
        await callback_query.message.answer(translate(
                f"📅 Ви обрали дату: <b>{selected_date.strftime('%d.%m.%Y')}.</b>\n\n"
                "Введіть початкову точку та кінцеву точку поїздки у форматі: <b>Місто - Місто</b>\n"
                "Наприклад: <b>Київ - Варшава</b>", user_id),
                parse_mode="HTML",
                reply_markup=get_cancel_keyboard(user_id)
            )
        await callback_query.answer()
        await SearchTrip.waiting_for_points.set()




translator = Translator()

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

@dp.message_handler(state=SearchTrip.waiting_for_points)
async def handle_points_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await state.finish()
        return
    
    points_input = message.text.strip()

    # Перевірка на правильний формат
    if "-" not in points_input:
        await message.answer(translate("❕ Неправильний формат! Використовуйте формат: Місто - Місто.", user_id))
        return

    # Перевірка, чи є пробіли перед і після дефісу
    if " - " not in points_input:
        await message.answer(translate("❕ Неправильний формат! Використовуйте формат: Місто - Місто, з пробілами перед і після дефісу.", user_id))
        return
    
    await message.answer(translate("Зачекайте будь ласка, перевіряємо нашу базу маршрутів.", user_id))

    try:
        start_city, end_city = [city.strip() for city in points_input.split(" - ")]

        start_city_translations = {}
        end_city_translations = {}

        # Переклад міст на інші мови
        for lang in SUPPORTED_LANGUAGES.keys():
            start_city_translations[lang] = translator.translate(start_city, dest=lang).text
            end_city_translations[lang] = translator.translate(end_city, dest=lang).text

        # Збереження даних користувача
        user_trip_data[user_id]["start_city"] = start_city
        user_trip_data[user_id]["end_city"] = end_city
        user_trip_data[user_id]["start_city_translations"] = start_city_translations
        user_trip_data[user_id]["end_city_translations"] = end_city_translations

        # Збереження пошукового запиту в базу даних
        search_date = datetime.now().strftime('%Y-%m-%d')
        wanted_date = user_trip_data[user_id]["date"].strftime('%Y-%m-%d')
        search_stops = f"{start_city} - {end_city}"

        cursor.execute('''
            INSERT INTO users_search (user_id, search_date, wanted_date, search_stops, found)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, search_date, wanted_date, search_stops, 0))
        conn.commit()

        # Підготовка попереднього перегляду маршруту
        trip_preview = (
            f"📅 <b>Дата поїздки:</b> {user_trip_data[user_id]['date'].strftime('%d.%m.%Y')}\n"
            f"🛣️ <b>Маршрут:</b> {start_city} - {end_city}"
        )

        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(translate("🔎 Почати пошук", user_id), callback_data="start_search")
        )

        await message.answer(
            translate(f"🔎 <b>Попередній перегляд:</b>\n\n{trip_preview}", user_id),
            parse_mode="HTML",
            reply_markup=markup
        )

        await state.finish()

    except Exception as e:
        await message.answer(translate("❕ Сталася помилка. Спробуйте ще раз.", user_id))
        print(f"Error: {e}")
        
@dp.callback_query_handler(lambda c: c.data == "start_search")
async def start_search(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_date = user_trip_data[user_id]["date"]
    start_city_translations = user_trip_data[user_id]["start_city_translations"]
    end_city_translations = user_trip_data[user_id]["end_city_translations"]

    await callback_query.message.answer(translate("Починаю пошук...", user_id), reply_markup=get_start_keyboard(user_id))

    try:
        query = '''
            SELECT t.id, t.car_id, t.date, t.time, t.car_mark, t.car_number, t.seats, t.stops, u.user_name, u.phone, u.phone2, u.user_id AS driver_id, t.watched
            FROM trips t
            JOIN users u ON u.user_id = t.user_id
            WHERE t.date = ?
        '''
        
        trips = []
        cursor.execute(query, (user_date.strftime('%Y-%m-%d'),))
        all_trips = cursor.fetchall()

        for trip in all_trips:
            trip_stops = trip[7].lower() 
            stops_list = [stop.strip() for stop in trip_stops.split(",")]  

            start_city_found = None
            end_city_found = None

            for start_city in start_city_translations.values():
                if start_city.lower() in stops_list:
                    start_city_found = stops_list.index(start_city.lower())
                    break

            for end_city in end_city_translations.values():
                if end_city.lower() in stops_list:
                    end_city_found = stops_list.index(end_city.lower())
                    break
                
            if start_city_found is not None and end_city_found is not None and start_city_found < end_city_found:
                trips.append(trip)

        if trips:
            search_stops = f"{user_trip_data[user_id]['start_city']} - {user_trip_data[user_id]['end_city']}"
            cursor.execute('''
                UPDATE users_search
                SET found = 1
                WHERE user_id = ? AND search_stops = ? AND wanted_date = ?
            ''', (user_id, search_stops, user_date.strftime('%Y-%m-%d')))
            conn.commit()
            
            for trip in trips:
                trip_id, car_id, date, time, car_mark, car_number, seats, stops, user_name, phone, phone2, driver_id, watched = trip
                formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
                phone = f"+{phone.lstrip('+')}"
                if phone2:
                    phone2 = f"+{phone2.lstrip('+')}"

                trip_preview = (
                    f"<b>👤 Водій:</b> @{user_name}\n"
                    f"<b>Телефон:</b> {phone} {phone2 if phone2 else ''}\n\n"
                    f"<b>📅 Дата поїздки:</b> {formatted_date}\n"
                    f"<b>Час виїзду:</b> {time}\n"
                    f"<b>Авто:</b> {car_mark}, {car_number}\n"
                    f"<b>📍 Маршрут:</b> {stops}\n"
                    f"<b>Місця:</b> {seats}\n"
                    f"<b>👀 Переглядів:</b> {watched}\n\n"
                    "<b>❗️ Попередження: В жодному разі не сплачуйте водіям аванс! Не дайте себе обманути!</b>"
                )

                cursor.execute('''
                    UPDATE trips
                    SET watched = watched + 1
                    WHERE id = ?
                ''', (trip_id,))
                conn.commit()

                markup = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(translate("Переглянути інформацію про водія", user_id), callback_data=f"view_driver_{driver_id}_{trip_id}"),
                    InlineKeyboardButton(translate("Переглянути авто", user_id), callback_data=f"view_car_{car_id}"),
                )

                await callback_query.message.answer(
                    translate(f"<b>✅ Знайдено поїздку:</b>\n\n{trip_preview}", user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )
        else:
            await callback_query.message.answer(
                translate("На жаль, на обрану дату поїздок не знайдено. Спробуйте пошукати пізніше або змініть параметри пошуку.", user_id), reply_markup=no_trips_keyboard(user_id)
            )
    except Exception as e:
        await callback_query.message.answer(translate("Сталася помилка під час пошуку поїздок. Спробуйте ще раз.", user_id), reply_markup=no_trips_keyboard(user_id))
        print(f"Error: {e}")
        
        
   
@dp.callback_query_handler(lambda c: c.data == "new_search")
async def start_search(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.message.edit_text(translate("<b>Оберіть дату вашої поїздки:</b>", user_id), parse_mode="HTML", reply_markup=create_search_calendar(user_id))
    
@dp.callback_query_handler(lambda c: c.data == "back_to_main_menu")
async def start_search(call: types.CallbackQuery):
    user_id = call.from_user.id 
    await call.message.answer(translate("Головне меню:", user_id), reply_markup=get_start_keyboard(user_id))
              
              
        
@dp.callback_query_handler(lambda c: c.data.startswith("view_car_"))
async def view_car(callback_query: types.CallbackQuery):
    car_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id

    try:
        query = '''
            SELECT mark, number, photo_path 
            FROM users_cars 
            WHERE id = ?
        '''
        cursor.execute(query, (car_id,))
        car_data = cursor.fetchone()

        if car_data:
            mark, number, photo_path = car_data
            description = f"<b>🚗 Авто:</b>\n\nМарка та модель: {mark}\nНомер: {number}"
            markup = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton("← Назад", callback_data=f"back_from_car")
            )

            if photo_path:
                with open(photo_path, "rb") as photo:
                    await callback_query.message.answer_photo(
                        photo=photo,
                        caption=translate(description, user_id),
                        parse_mode="HTML",
                        reply_markup=markup
                    )
            else:
                await callback_query.message.answer(
                    translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )
        else:
            await callback_query.message.answer(
                translate("❕ Інформація про автомобіль не знайдена.", user_id)
            )
    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні інформації про авто.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")
        
        
        
        
@dp.callback_query_handler(lambda c: c.data.startswith("view_driver_"))
async def view_driver(callback_query: types.CallbackQuery):
    driver_user_id = int(callback_query.data.split("_")[2])
    trip_id = int(callback_query.data.split("_")[3])
    user_id = callback_query.from_user.id
    
    cursor.execute('SELECT date, stops FROM trips WHERE id = ?', (trip_id,))
    trip = cursor.fetchone()
    
    trip_date = datetime.strptime(trip[0], '%Y-%m-%d')  
    date_to_send = trip_date + timedelta(days=3)  
    formatted_date_to_send = date_to_send.strftime('%d.%m.%Y')
    stops = trip[1] 
    
    cursor.execute('''
        SELECT 1 FROM send_review 
        WHERE user_id = ? AND driver_id = ? AND trip_stops = ? AND date_to_send = ? AND sent = 0
    ''', (user_id, driver_user_id, stops, formatted_date_to_send))
    existing_record = cursor.fetchone()

    if not existing_record:
        cursor.execute('''
            INSERT INTO send_review (user_id, driver_id, trip_stops, date_to_send)
            VALUES (?, ?, ?, ?)
        ''', (user_id, driver_user_id, stops, formatted_date_to_send))
        conn.commit()  
    else:
        print(f"A record with the same data already exists and has not been sent yet.")
    
    
    try:
        driver_name = find_username_by_id(driver_user_id)
        description, photo = get_driver_full_info(driver_user_id)

        if description:
            markup = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(translate("Переглянути відгуки", user_id), callback_data=f"view_reviews_{driver_user_id}_1"),
                InlineKeyboardButton(translate("Зв'язатися з водієм", user_id), url=f"https://t.me/{driver_name}"),
                InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_from_car")
            )

            if photo:
                with open(photo, "rb") as driver_photo:
                    await callback_query.message.answer_photo(
                        photo=driver_photo,
                        caption=translate(description, user_id),
                        parse_mode="HTML",
                        reply_markup=markup
                    )
            else:
                await callback_query.message.answer(
                    translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )

        else:
            await callback_query.message.answer(
                translate("❕ Не вдалося знайти інформацію про водія.", user_id)
            )

    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні інформації про водія.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("view_reviews_"))
async def view_reviews(callback_query: types.CallbackQuery):
    driver_user_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id
    page = int(callback_query.data.split("_")[3])
    reviews_per_page = 5

    try:
        reviews = get_driver_reviews_text(driver_user_id)

        if reviews:
            start_index = (page - 1) * reviews_per_page
            end_index = page * reviews_per_page
            reviews_to_show = reviews[start_index:end_index]

            reviews_text = "\n\n".join(
                [f"<b>Рейтинг:</b> {'⭐' * r[0]} {'☆' * (5 - r[0])}\n"
                 f"<b>Коментар:</b> {r[1]}\n"
                 f"<b>Дата:</b> {datetime.strptime(r[2][:10], '%Y-%m-%d').strftime('%d.%m.%Y')} {r[2][11:16]}"
                 for r in reviews_to_show]
            )
            markup = InlineKeyboardMarkup(row_width=2)

            if page > 1:
                markup.add(InlineKeyboardButton(translate("← Попередня сторінка", user_id), callback_data=f"view_reviews_{driver_user_id}_{page - 1}"))

            if len(reviews) > page * reviews_per_page:
                markup.add(InlineKeyboardButton(translate("Наступна сторінка →", user_id), callback_data=f"view_reviews_{driver_user_id}_{page + 1}"))

            markup.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data=f"back_from_driver_{driver_user_id}"))
            description, photo = get_driver_full_info(driver_user_id)
            if photo:
                await callback_query.message.edit_caption(
                    caption=reviews_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )
            else:
                await callback_query.message.edit_text(
                    reviews_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )

        else:
            await callback_query.message.answer(
                translate("❕ Відгуки відсутні.", user_id)
            )

    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні відгуків.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("back_from_driver_"))
async def back_from_driver(callback_query: types.CallbackQuery):
    driver_user_id = int(callback_query.data.split("_")[3])
    user_id = callback_query.from_user.id
    try:
        description, photo = get_driver_full_info(driver_user_id)
        driver_name = find_username_by_id(driver_user_id)

        if description:
            markup = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(translate("Переглянути відгуки", user_id), callback_data=f"view_reviews_{driver_user_id}_1"),  # Початкова сторінка відгуків
                InlineKeyboardButton(translate("Зв'язатися з водієм", user_id), url=f"https://t.me/{driver_name}"),
                InlineKeyboardButton(translate("← Назад", user_id), callback_data="back_from_car")
            )
            
            if photo:
                await callback_query.message.edit_caption(
                    caption=translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )
            else:
                await callback_query.message.edit_text(
                    translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )

        else:
            await callback_query.message.answer(
                translate("❕ Не вдалося знайти інформацію про водія.", user_id)
            )

    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні інформації про водія.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")








@dp.callback_query_handler(lambda c: c.data.startswith("view_profilereviews_"))
async def view_reviews(callback_query: types.CallbackQuery):
    driver_user_id = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id
    page = int(callback_query.data.split("_")[3])
    reviews_per_page = 5

    try:
        reviews = get_driver_reviews_text(driver_user_id)

        if reviews:
            start_index = (page - 1) * reviews_per_page
            end_index = page * reviews_per_page
            reviews_to_show = reviews[start_index:end_index]

            reviews_text = "\n\n".join(
                [f"<b>Рейтинг:</b> {'⭐' * r[0]} {'☆' * (5 - r[0])}\n"
                 f"<b>Коментар:</b> {r[1]}\n"
                 f"<b>Дата:</b> {datetime.strptime(r[2][:10], '%Y-%m-%d').strftime('%d.%m.%Y')} {r[2][11:16]}"
                 for r in reviews_to_show]
            )
            markup = InlineKeyboardMarkup(row_width=2)

            if page > 1:
                markup.add(InlineKeyboardButton(translate("← Попередня сторінка", user_id), callback_data=f"view_profilereviews_{driver_user_id}_{page - 1}"))

            if len(reviews) > page * reviews_per_page:
                markup.add(InlineKeyboardButton(translate("Наступна сторінка →", user_id), callback_data=f"view_profilereviews_{driver_user_id}_{page + 1}"))

            markup.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data=f"back_from_driverprofile_{driver_user_id}"))
            description, photo = get_driver_full_info(driver_user_id)
            if photo:
                await callback_query.message.edit_caption(
                    caption=reviews_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )
            else:
                await callback_query.message.edit_text(
                    reviews_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )

        else:
            await callback_query.message.answer(
                translate("❕ Відгуки відсутні.", user_id)
            )

    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні відгуків.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("back_from_driverprofile_"))
async def back_from_driver(callback_query: types.CallbackQuery):
    driver_user_id = int(callback_query.data.split("_")[3])
    user_id = callback_query.from_user.id
    try:
        description, photo = get_driver_full_info(driver_user_id)

        if description:
            markup = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(translate("Переглянути відгуки", user_id), callback_data=f"view_profilereviews_{driver_user_id}_1"),  # Початкова сторінка відгуків
                InlineKeyboardButton(translate("Зв'язатися з водієм", user_id), url=f"https://t.me/{driver_user_id}"),
            )
            
            if photo:
                await callback_query.message.edit_caption(
                    caption=translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )
            else:
                await callback_query.message.edit_text(
                    translate(description, user_id),
                    parse_mode="HTML",
                    reply_markup=markup
                )

        else:
            await callback_query.message.answer(
                translate("❕ Не вдалося знайти інформацію про водія.", user_id)
            )

    except Exception as e:
        await callback_query.answer(
            translate("Сталася помилка при отриманні інформації про водія.", user_id),
            show_alert=True
        )
        print(f"Error: {e}")



@dp.callback_query_handler(lambda c: c.data == "back_from_car")
async def delete_message(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
      


      
@dp.callback_query_handler(lambda c: c.data.startswith("searchprev:") or c.data.startswith("searchnext:"))
async def handle_calendar_navigation(callback_query: CallbackQuery):
    try:
        # Отримуємо напрямок (prev чи next) та дату
        direction = "prev" if callback_query.data.startswith("searchprev:") else "next"
        year, month = map(int, callback_query.data.split(":")[1].split("-"))
        
        # Обчислюємо новий місяць та рік
        if direction == "prev":
            if month == 1:
                new_month = 12
                new_year = year - 1
            else:
                new_month = month - 1
                new_year = year
        else:  # next
            if month == 12:
                new_month = 1
                new_year = year + 1
            else:
                new_month = month + 1
                new_year = year
        
        user_id = callback_query.from_user.id
        await callback_query.message.edit_reply_markup(
            reply_markup=create_search_calendar(user_id, new_year, new_month)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in calendar navigation: {e}")
        await callback_query.answer("Помилка при навігації", show_alert=True)



@dp.callback_query_handler(lambda c: c.data.startswith("search_") and not (c.data.startswith("searchprev:") or c.data.startswith("searchnext:")))
async def handle_calendar_selection(callback_query: CallbackQuery):
    try:
        # Отримуємо вибрану дату
        date_str = callback_query.data.replace("search_", "")
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        user_id = callback_query.from_user.id

        if selected_date < today:
            await callback_query.answer(translate("❕ Ви не можете обирати дату, яка вже пройшла!", user_id), show_alert=True)
            return

        user_trip_data[user_id] = {"date": selected_date}
        await callback_query.message.answer(
            translate(f"📅 Ви обрали дату: <b>{selected_date.strftime('%d.%m.%Y')}.</b>\n\n"
                     "Введіть початкову точку та кінцеву точку поїздки у форматі: <b>Місто - Місто</b>\n"
                     "Наприклад: <b>Київ - Варшава</b>", user_id),
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(user_id)
        )
        await SearchTrip.waiting_for_points.set()
        await callback_query.answer()
    except Exception as e:
        print(f"Error in calendar selection: {e}")
        await callback_query.answer("Помилка при виборі дати", show_alert=True)




@dp.callback_query_handler(lambda c: c.data.startswith("calendar_nav_search_"))
async def handle_calendar_navigation(callback_query: types.CallbackQuery):
    try:
        parts = callback_query.data.split("_")
        direction = parts[3]
        current_year = int(parts[4])
        current_month = int(parts[5])
        
        if direction == "prev":
            if current_month == 1:
                new_month = 12
                new_year = current_year - 1
            else:
                new_month = current_month - 1
                new_year = current_year
        else:  # next
            if current_month == 12:
                new_month = 1
                new_year = current_year + 1
            else:
                new_month = current_month + 1
                new_year = current_year
        
        user_id = callback_query.from_user.id
        
        markup = create_search_calendar(user_id, new_year, new_month)
            
        await callback_query.message.edit_reply_markup(reply_markup=markup)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Error in calendar navigation: {e}")
        await callback_query.answer(translate("❕ Помилка при навігації календаря", user_id), show_alert=True)
    
    
