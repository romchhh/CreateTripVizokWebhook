from main import bot, dp, scheduler
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import *
from ulits.filters import *
from datetime import datetime, timedelta
from keyboards.client_keyboards import create_edit_calendar, create_trip_calendar
from aiogram.dispatcher import FSMContext
from keyboards.admin_keyboards import get_admin_keyboard
from keyboards.client_keyboards import (get_start_keyboard, get_cancel_keyboard, edit_trip_keyboard, 
                                       create_trip_calendar_repeat, create_hour_keyboard, create_minutes_keyboard,
                                       create_edit_hour_keyboard, create_edit_minutes_keyboard)
from ulits.client_states import AddTrip, ChangeTrip
import re, asyncio, json
from database.client_db import cursor, conn, update_trip_date, update_trip_stops, update_trip_time, get_trip_by_id
from ulits.translate import translate, get_user_lang
from ulits.client_functions import start_message, get_trip_text
from data.texts import *
from handlers.my_profile_handlers import my_trips
import aiohttp


TIME_RANGE_REGEX = r"^(?:[01]?\d|2[0-3]):[0-5]?\d$"


user_trip_data = {}

async def handle_webhook_data(trip_data):
    """Обробляє дані з webhook"""
    user_id = trip_data.get('user_id')
    route = trip_data.get('route')
    lang = trip_data.get('lang', 'uk')
    
    if user_id and route:
        # Обробляємо отримані дані
        formatted_route = " ➔ ".join(route.split(" -> "))
        user_trip_data[user_id] = {
            "stops": formatted_route,
            "original_route": route
        }
        
        # Відправляємо повідомлення користувачу
        user_lang = get_user_lang(user_id)
        keyboard = InlineKeyboardMarkup(row_width=2)
        repeat_options = [
            ('norepeat', repeat_options_text[user_lang]['norepeat']),
            ('daily', repeat_options_text[user_lang]['daily']),
            ('every1day', repeat_options_text[user_lang]['every1day']),
            ('every2days', repeat_options_text[user_lang]['every2days']),
            ('every3days', repeat_options_text[user_lang]['every3days']),
            ('every4days', repeat_options_text[user_lang]['every4days']),
            ('every5days', repeat_options_text[user_lang]['every5days']),
            ('every6days', repeat_options_text[user_lang]['every6days']),
            ('every7days', repeat_options_text[user_lang]['every7days']),
        ]
        for callback, text in repeat_options:
            keyboard.add(InlineKeyboardButton(text, callback_data=f"repeat_{callback}"))
        
        await bot.send_message(
            chat_id=user_id,
            text=translate(f"✅ <b>Маршрут збережено:</b>\n{formatted_route}\n\n{repeat_options_text[user_lang]['repeat_prompt']}", user_id),
            parse_mode="HTML",
            reply_markup=keyboard
        )
       
        state = FSMContext(storage=dp.storage, chat=user_id, user=user_id)
        await state.set_state(AddTrip.waiting_for_repeat.state)


@dp.message_handler(lambda message: message.text.lower() in map(str.lower, create_trip_text.values()), state='*')
async def my_parcel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    user_id = message.from_user.id
    await message.answer(select_date_text[get_user_lang(user_id)], parse_mode="HTML", reply_markup=create_trip_calendar(user_id))
    

@dp.callback_query_handler(lambda c: c.data.startswith("createtrip_"))
async def handle_date_selection(callback_query: types.CallbackQuery):
    try:
        # Розбираємо callback_data
        selected_date_str = callback_query.data.split("_")[1]
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        user_id = callback_query.from_user.id

        if selected_date < today:
            await callback_query.answer(past_date_error[get_user_lang(user_id)], show_alert=True)
            return

        user_trip_data[user_id] = {"date": selected_date} 
        await callback_query.message.edit_text(
            select_time_text[get_user_lang(user_id)],
            parse_mode="HTML",
            reply_markup=create_hour_keyboard(user_id)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in date selection: {e}")
        await callback_query.answer(date_selection_error[get_user_lang(user_id)], show_alert=True)


# Обробник вибору години
@dp.callback_query_handler(lambda c: c.data.startswith("select_hour_"))
async def handle_hour_selection(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        selected_hour = int(callback_query.data.split("_")[2])
        
        # Показуємо клавіатуру для вибору хвилин
        await callback_query.message.edit_text(
            select_minutes_text[get_user_lang(user_id)].format(f"{selected_hour:02d}"),
            parse_mode="HTML",
            reply_markup=create_minutes_keyboard(user_id, selected_hour)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in hour selection: {e}")
        await callback_query.answer("Помилка при виборі години", show_alert=True)


# Обробник вибору хвилин
@dp.callback_query_handler(lambda c: c.data.startswith("select_minute_"))
async def handle_minute_selection(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        data_parts = callback_query.data.split("_")
        selected_hour = int(data_parts[2])
        selected_minute = int(data_parts[3])
        
        # Формуємо час у форматі HH:MM
        selected_time = f"{selected_hour:02d}:{selected_minute:02d}"
        user_trip_data[user_id]["time"] = selected_time

        # Перевіряємо, чи це повторення поїздки
        if "repeat_date" in user_trip_data[user_id]:
            # Це повторення поїздки - показуємо попередній перегляд
            trip_data = user_trip_data[user_id]
            selected_date = trip_data["repeat_date"]
            
            preview_text = translate(f"""
�� <b>Попередній перегляд поїздки:</b>

📅 <b>Дата:</b> {selected_date.strftime('%d.%m.%Y')}
🕒 <b>Час:</b> {selected_time}
🚙 <b>Автомобіль:</b> {trip_data['car_mark']}, {trip_data['car_number']}
👥 <b>Вільних місць:</b> {trip_data['seats']}
📍 <b>Маршрут:</b> {trip_data['stops']}
""", user_id)
            
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton(translate("✅ Підтвердити", user_id), callback_data="confirm_repeat_trip"),
                InlineKeyboardButton(translate("❌ Скасувати", user_id), callback_data="cancel_repeat_trip")
            )
            
            await callback_query.message.edit_text(preview_text, parse_mode="HTML", reply_markup=keyboard)
            await callback_query.answer()
            return

        # Звичайне створення поїздки - перевіряємо наявність автомобілів
        cursor.execute("SELECT id, mark, number FROM users_cars WHERE user_id = ?", (user_id,))
        cars = cursor.fetchall()

        if not cars:
            user_trip_data[user_id]["car_id"] = None

            keyboard = InlineKeyboardMarkup(row_width=4)
            buttons = [InlineKeyboardButton(text=str(i), callback_data=f"choose_seats_{i}") for i in range(1, 17)]
            keyboard.add(*buttons)
            keyboard.add(
                InlineKeyboardButton(back_button[get_user_lang(user_id)], callback_data="back_to_car"),
            )
            await callback_query.message.edit_text(
                time_selected_text[get_user_lang(user_id)].format(selected_time) + "\n\n" + select_seats_text[get_user_lang(user_id)],
                parse_mode="HTML",
                reply_markup=keyboard
            )
            await callback_query.answer()
            return

        # Показуємо список автомобілів
        keyboard = InlineKeyboardMarkup(row_width=1)
        for car_id, mark, number in cars:
            button_text = f"{mark} : {number}"
            button = InlineKeyboardButton(text=button_text, callback_data=f"choose_car_{car_id}")
            keyboard.add(button)
        
        # Додаємо кнопку "Назад" для повернення до вибору часу
        keyboard.add(InlineKeyboardButton(back_button[get_user_lang(user_id)], callback_data="back_to_time"))

        await callback_query.message.edit_text(
            time_selected_text[get_user_lang(user_id)].format(selected_time) + "\n\n" + select_car_text[get_user_lang(user_id)],
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in minute selection: {e}")
        await callback_query.answer("Помилка при виборі хвилин", show_alert=True)


# Обробник кнопки "Назад" до вибору дати
@dp.callback_query_handler(lambda c: c.data == "back_to_date")
async def back_to_date_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        select_date_text[get_user_lang(user_id)],
        parse_mode="HTML",
        reply_markup=create_trip_calendar(user_id)
    )
    await callback_query.answer()


# Обробник кнопки "Назад" до вибору години
@dp.callback_query_handler(lambda c: c.data == "back_to_hour")
async def back_to_hour_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        select_time_text[get_user_lang(user_id)],
        parse_mode="HTML",
        reply_markup=create_hour_keyboard(user_id)
    )
    await callback_query.answer()


# Обробник кнопки "Назад" до вибору часу (з вибору автомобіля)
@dp.callback_query_handler(lambda c: c.data == "back_to_time")
async def back_to_time_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        select_time_text[get_user_lang(user_id)],
        parse_mode="HTML",
        reply_markup=create_hour_keyboard(user_id)
    )
    await callback_query.answer()
    
    
    
@dp.callback_query_handler(lambda c: c.data.startswith("choose_car_"))
async def handle_car_selection(callback_query: types.CallbackQuery):
    car_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    user_trip_data[user_id]["car_id"] = car_id

    keyboard = InlineKeyboardMarkup(row_width=4)

    buttons = [InlineKeyboardButton(text=str(i), callback_data=f"choose_seats_{i}") for i in range(1, 17)]

    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton(back_button[get_user_lang(user_id)], callback_data="back_to_car"),
    )
    await callback_query.message.edit_text(select_seats_text[get_user_lang(user_id)], reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("back_to_car"), state=[AddTrip.waiting_for_stops, None])
async def handle_car_selection(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    cursor.execute("SELECT id, mark, number FROM users_cars WHERE user_id = ?", (user_id,))
    cars = cursor.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for car_id, mark, number in cars:
        button_text = f"{mark} : {number}"
        button = InlineKeyboardButton(text=button_text, callback_data=f"choose_car_{car_id}")
        keyboard.add(button)
    
    # Додаємо кнопку "Назад" для повернення до вибору часу
    keyboard.add(InlineKeyboardButton(back_button[get_user_lang(user_id)], callback_data="back_to_time"))
    
    await callback_query.message.edit_text(select_car_text[get_user_lang(user_id)], reply_markup=keyboard)




@dp.callback_query_handler(lambda c: c.data.startswith("choose_seats_"))
async def handle_seats_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    seats = int(callback_query.data.split("_")[-1])

    user_trip_data[user_id]["seats"] = seats

    # Створюємо URL для GitHub Pages веб-додатка
    webapp_url = f"https://romchhh.github.io/CreateTripVizokWebhook/?lang={get_user_lang(user_id)}&user_id={user_id}&create=trip&webhook_url=http://139.59.208.152:8001/webhook"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(
            "🗺️ Додати маршрут", 
            url=webapp_url
        ),
        InlineKeyboardButton(back_button[get_user_lang(user_id)], callback_data="back_to_car")
    )

    await callback_query.message.edit_text(
        translate("🗺️ <b>Додавання маршруту</b>\n\nНатисніть кнопку нижче, щоб відкрити зручний інтерфейс для додавання міст вашого маршруту.", user_id),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dp.message_handler(state=AddTrip.waiting_for_stops)
async def handle_stops_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(cancel_action_text[get_user_lang(user_id)], reply_markup=get_start_keyboard(user_id))
        await state.finish()
        return
    
    user_input = message.text.strip()
    
    # Очищаємо введений текст від зайвих символів та форматуємо
    cleaned_stops = []
    for stop in user_input.split():  # Розділяємо по пробілах
        stop = stop.strip()
        if stop:  # Перевіряємо, що зупинка не пуста після очистки
            cleaned_stops.append(stop)
    
    if len(cleaned_stops) < 2:
        await message.reply(min_stops_error[get_user_lang(user_id)])
        return

    # З'єднуємо зупинки через кому для збереження в БД
    formatted_stops = ", ".join(cleaned_stops)
    user_trip_data[user_id]["stops"] = formatted_stops

    # Запитуємо частоту повторення
    user_lang = get_user_lang(user_id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    repeat_options = [
        ('norepeat', repeat_options_text[user_lang]['norepeat']),
        ('daily', repeat_options_text[user_lang]['daily']),
        ('every1day', repeat_options_text[user_lang]['every1day']),
        ('every2days', repeat_options_text[user_lang]['every2days']),
        ('every3days', repeat_options_text[user_lang]['every3days']),
        ('every4days', repeat_options_text[user_lang]['every4days']),
        ('every5days', repeat_options_text[user_lang]['every5days']),
        ('every6days', repeat_options_text[user_lang]['every6days']),
        ('every7days', repeat_options_text[user_lang]['every7days']),
    ]
    for callback, text in repeat_options:
        keyboard.add(InlineKeyboardButton(text, callback_data=f"repeat_{callback}"))
    
    await message.answer(
        repeat_options_text[user_lang]['repeat_prompt'],
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await AddTrip.waiting_for_repeat.set()


@dp.callback_query_handler(lambda c: c.data.startswith("repeat_"), state=AddTrip.waiting_for_repeat)
async def handle_repeat_selection(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_lang = get_user_lang(user_id)
    repeat_choice = callback_query.data.split("_")[1]
    
    # Отримуємо переклад для вибраного варіанту повторення
    repeat_text = repeat_options_text[user_lang][repeat_choice]
    
    # Зберігаємо вибір повторення (зберігаємо ключ, а не переклад)
    user_trip_data[user_id]["repeat"] = repeat_choice
    user_trip_data[user_id]["repeat_text"] = repeat_text  # Зберігаємо переклад окремо для відображення
    
    # Показуємо попередній перегляд поїздки
    cursor.execute("SELECT mark, number FROM users_cars WHERE id = ?", (user_trip_data[user_id]["car_id"],))
    car_data = cursor.fetchone()

    if car_data:
        car_mark, car_number = car_data
    else:
        car_mark, car_number = "Невідомо", "Невідомо"

    trip_data = user_trip_data[user_id]
    trip_preview_text = new_trip_preview[user_lang].format(
        trip_data['date'].strftime('%d.%m.%Y'),
        trip_data['time'],
        car_mark,
        car_number,
        trip_data['seats'],
        trip_data['stops'],
        trip_data['repeat_text']  # Використовуємо переклад для відображення
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(confirm_trip_button[user_lang], callback_data="confirm_trip"),
        InlineKeyboardButton(cancel_trip_button[user_lang], callback_data="cancel_trip")
    )
    await callback_query.message.edit_text(
        trip_preview_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.finish()
    
@dp.callback_query_handler(lambda c: c.data == "confirm_trip")
async def confirm_trip(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    trip_data = user_trip_data[user_id]
    user_lang = get_user_lang(user_id)

    # Отримуємо дані про автомобіль
    cursor.execute("SELECT mark, number FROM users_cars WHERE id = ?", (trip_data["car_id"],))
    car_data = cursor.fetchone()

    if car_data:
        car_mark, car_number = car_data
    else:
        car_mark, car_number = "Невідомо", "Невідомо"

    # Функція для збереження поїздки
    def save_trip(date, time, created_at):
        cursor.execute("""
            INSERT INTO trips (user_id, car_id, date, time, car_mark, car_number, seats, stops, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            trip_data["car_id"] if trip_data["car_id"] is not None else 0,
            date.strftime('%Y-%m-%d'),
            time,
            car_mark,
            car_number,
            trip_data["seats"],
            trip_data["stops"],
            created_at
        ))
        return cursor.lastrowid

    # Поточна дата та час для поля created_at
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Зберігаємо основну поїздку
    trip_id = save_trip(trip_data["date"], trip_data["time"], created_at)
    conn.commit()  # Зберігаємо зміни після основної поїздки

    # Обробка повторюваних поїздок
    repeat_choice = trip_data.get("repeat", "norepeat")
    
    # Визначаємо інтервал повторення
    intervals = {
        'norepeat': 0,
        'daily': 1,
        'every1day': 1,
        'every2days': 2,
        'every3days': 3,
        'every4days': 4,
        'every5days': 5,
        'every6days': 6,
        'every7days': 7
    }
    
    interval = intervals.get(repeat_choice, 0)  # Якщо ключ не знайдено, повертаємо 0 (без повторень)
    repeated_trips_count = 0  # Лічильник повторюваних поїздок
    
    if interval > 0:  # Створюємо повторювані поїздки тільки якщо є валідний інтервал
        # Обмеження: 2 місяці вперед (60 днів)
        max_date = trip_data["date"] + timedelta(days=60)
        current_date = trip_data["date"] + timedelta(days=interval)
        
        while current_date <= max_date:
            if current_date >= datetime.now().date():  # Не створюємо поїздки в минулому
                save_trip(current_date, trip_data["time"], created_at)
                repeated_trips_count += 1
            current_date += timedelta(days=interval)
        conn.commit()  # Зберігаємо зміни після створення повторюваних поїздок

    # Перевіряємо збережені пошуки користувачів (ваш існуючий код)
    try:
        new_trip_date = trip_data["date"].strftime('%Y-%m-%d')
        new_trip_stops = trip_data["stops"].lower()
        new_trip_stops_list = [stop.strip() for stop in new_trip_stops.split(",")]

        cursor.execute('''
            SELECT id, user_id, wanted_date, search_stops
            FROM users_search
            WHERE found = 0
        ''')
        saved_searches = cursor.fetchall()

        for search in saved_searches:
            search_id, search_user_id, wanted_date, search_stops = search
            wanted_date_obj = datetime.strptime(wanted_date, '%Y-%m-%d').date()
            new_trip_date_obj = datetime.strptime(new_trip_date, '%Y-%m-%d').date()

            if abs((wanted_date_obj - new_trip_date_obj).days) <= 3:
                search_stops_list = [stop.strip().lower() for stop in search_stops.split(" - ")]
                if all(city in new_trip_stops_list for city in search_stops_list):
                    try:
                        start_index = new_trip_stops_list.index(search_stops_list[0])
                        end_index = new_trip_stops_list.index(search_stops_list[1], start_index + 1)
                        if start_index < end_index:
                            cursor.execute('''
                                UPDATE users_search
                                SET found = 1
                                WHERE id = ?
                            ''', (search_id,))
                            conn.commit()
                            
                            cursor.execute('''
                                UPDATE trips
                                SET watched = watched + 1
                                WHERE id = ?
                            ''', (trip_id,))
                            conn.commit()

                            trip_preview = (
                                f"🚗 <b>За вашим недавнім запитом з'явилась нова поїздка!</b>\n\n"
                                f"📅 <b>Дата:</b> {new_trip_date_obj.strftime('%d.%m.%Y')}\n"
                                f"🕒 <b>Час:</b> {trip_data['time']}\n"
                                f"🚙 <b>Автомобіль:</b> {car_mark}, {car_number}\n"
                                f"📍 <b>Маршрут:</b> {new_trip_stops}\n"
                                f"👥 <b>Місць:</b> {trip_data['seats']}\n\n"
                                "<b>❗️ Попередження: В жодному разі не сплачуйте водіям аванс! Не дайте себе обманути!</b>"
                            )
                            
                            markup = InlineKeyboardMarkup(row_width=1).add(
                                InlineKeyboardButton(
                                    text=translate("Переглянути інформацію про водія", search_user_id),
                                    callback_data=f"view_driver_{user_id}_{trip_id}"
                                ),
                                InlineKeyboardButton(
                                    text=translate("Переглянути авто", search_user_id),
                                    callback_data=f"view_car_{trip_data['car_id']}"
                                ),
                            )

                            await bot.send_message(
                                chat_id=search_user_id,
                                text=translate(trip_preview, search_user_id),
                                parse_mode="HTML",
                                reply_markup=markup
                            )
                    except ValueError:
                        pass

    except Exception as e:
        print(f"Помилка під час перевірки збережених пошуків: {e}")

    # Повідомляємо користувача про успішне підтвердження
    success_message = translate("✅ <b>Поїздку успішно створено!</b>", user_id)
    if repeated_trips_count > 0:
        success_message += translate(f"\n📅 Додатково заплановано ще {repeated_trips_count} поїздок", user_id)
    success_message += translate("\n\nУправляти вашими поїздками ви можете в розділі <b>'Мої поїздки'</b>", user_id)
    
    await callback_query.message.edit_text(
        success_message,
        parse_mode="HTML",
        reply_markup=None
    )
    await asyncio.sleep(0.5)
    await start_message(callback_query.message)
        


@dp.callback_query_handler(lambda c: c.data == "cancel_trip")
async def cancel_trip(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()
    await callback_query.message.answer(translate("<b>Поїздку скасовано.</b>", user_id), reply_markup=get_start_keyboard(user_id))



@dp.callback_query_handler(lambda c: c.data.startswith('prevpage_') or c.data.startswith('nextpage_'))
async def navigate_trips(callback_query: types.CallbackQuery):
    current_page = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    today_minus_3_days = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE user_id = ? AND date > ?",
        (user_id, today_minus_3_days)
    )
    trips = cursor.fetchall()

    if not trips:
        await callback_query.message.answer(translate("У вас немає поїздок.", user_id))
        return

    # Реалізуємо циклічну навігацію
    total_trips = len(trips)
    if callback_query.data.startswith('nextpage_'):
        current_page = (current_page + 1) % total_trips
    else:  # prevpage
        current_page = (current_page - 1) % total_trips

    trip = trips[current_page]
    trip_text = get_trip_text(trip, user_id=callback_query.from_user.id)

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("✏ Редагувати", user_id), callback_data=f"edit_trip_{trip[0]}"),
        InlineKeyboardButton(translate("🗑 Видалити", user_id), callback_data=f"deletetrip_{trip[0]}"),
    )
    if total_trips > 1:
        navigation_buttons = [
            InlineKeyboardButton(translate("⬅ Попередня", user_id), callback_data=f"prevpage_{current_page}"),
            InlineKeyboardButton(translate("➡ Наступна", user_id), callback_data=f"nextpage_{current_page}"),
        ]
        keyboard.row(*navigation_buttons)

    await callback_query.message.edit_text(
        trip_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    

@dp.callback_query_handler(lambda c: c.data.startswith('deletetrip_'))
async def confirm_delete_trip(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    trip_id = callback_query.data.split('_')[-1]  
    confirm_text = translate("Ви впевнені, що хочете видалити цю поїздку?", user_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(translate("Так, видалити", user_id), callback_data=f"confirmdelete_trip_{trip_id}"),
        InlineKeyboardButton(translate("Скасувати", user_id), callback_data=f"cancel_delete_trip_{trip_id}")
    )
    await callback_query.message.edit_text(
        confirm_text,
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith('confirmdelete_trip_'))
async def delete_trip(callback_query: types.CallbackQuery):
    trip_id = callback_query.data.split('_')[-1]
    user_id = callback_query.from_user.id
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()

    is_archive = False
    await callback_query.message.edit_text(translate("<b>Поїздка була успішно видалена.</b>", user_id), parse_mode="HTML", reply_markup=None)
    
    current_page = 0
    today_minus_3_days = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE user_id = ? AND date > ?",
        (user_id, today_minus_3_days)
    )
    trips = cursor.fetchall()
    if not trips:
        await callback_query.message.answer(translate("У вас немає поїздок."), user_id)
        return
    trip = trips[current_page]
    trip_text = get_trip_text(trip, user_id = callback_query.from_user.id)
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

    await callback_query.message.answer(
        trip_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_delete_trip_'))
async def cancel_delete_trip(callback_query: types.CallbackQuery):
    current_page = 0
    user_id = callback_query.from_user.id
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    is_archive = False
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
        await callback_query.message.answer(translate("У вас немає поїздок.", user_id))
        return
    
    trip = trips[current_page]
    trip_text = get_trip_text(trip, user_id) 
    
    if current_page >= len(trips):
        current_page = len(trips) - 1
    
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

    await callback_query.message.edit_text(
        trip_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
        
        
@dp.callback_query_handler(lambda c: c.data.startswith('edit_trip_'))
async def edit_trip(callback_query: types.CallbackQuery):
    trip_id = int(callback_query.data.split('_')[2])
    user_id = callback_query.from_user.id
    
    cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        await callback_query.message.answer(translate("Поїздку не знайдено."), user_id)
        return
    
    trip_text = get_trip_text(trip, user_id = callback_query.from_user.id)
    await callback_query.message.edit_text(
        f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
        parse_mode="HTML",
        reply_markup=edit_trip_keyboard(user_id, trip_id)
    )

        
        
@dp.callback_query_handler(lambda c: c.data.startswith('changedate_'))
async def edit_trip_date(callback_query: types.CallbackQuery):
    trip_id = int(callback_query.data.split('_')[-1])
    user_id = callback_query.from_user.id   
    await callback_query.message.edit_text(
        translate("<b>Оберіть нову дату поїздки:</b>", user_id), 
        parse_mode="HTML", 
        reply_markup=create_edit_calendar(user_id, trip_id)
    )
        
        
@dp.callback_query_handler(lambda c: c.data.startswith("edittrip_"))
async def handle_edit_date_selection(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        callback_data = callback_query.data.split("_")
        selected_date_str = callback_data[1]
        trip_id = int(callback_data[-1])

        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        if selected_date < today:
            await callback_query.answer(translate(
                "❕ Ви не можете обирати дату, яка вже пройшла!", user_id), show_alert=True
            )
            return
        try:
            update_trip_date(trip_id, selected_date)
            cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
            trip = cursor.fetchone()
            trip_text = get_trip_text(trip, user_id = callback_query.from_user.id)
            await callback_query.message.edit_text(
                f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
                parse_mode="HTML",
                reply_markup=edit_trip_keyboard(user_id, trip_id)
            )

        except Exception as e:
            await callback_query.answer(translate(
                "❕ Сталася помилка під час оновлення дати. Спробуйте пізніше.", user_id),
                show_alert=True
            )
            print(f"Error updating trip date: {e}")
    except Exception as e:
        print(f"Error in edit date selection: {e}")
        await callback_query.answer(translate("❕ Помилка при виборі дати", user_id), show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith("calendar_nav_edit_"))
async def handle_edit_calendar_navigation(callback_query: types.CallbackQuery):
    try:
        parts = callback_query.data.split("_")
        direction = parts[3]
        current_year = int(parts[4])
        current_month = int(parts[5])
        trip_id = int(parts[6])
        
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
        markup = create_edit_calendar(user_id, trip_id, new_year, new_month)
            
        await callback_query.message.edit_reply_markup(reply_markup=markup)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Error in calendar navigation: {e}")
        await callback_query.answer(translate("❕ Помилка при навігації календаря", user_id), show_alert=True)

    
        
        
@dp.callback_query_handler(lambda c: c.data.startswith('changetime_'))
async def edit_trip_time(callback_query: types.CallbackQuery):
    trip_id = int(callback_query.data.split('_')[-1])
    user_id = callback_query.from_user.id

    await callback_query.message.edit_text(
        select_time_text[get_user_lang(user_id)],
        parse_mode="HTML",
        reply_markup=create_edit_hour_keyboard(user_id, trip_id)
    )
    await callback_query.answer()

# Обробник вибору години при редагуванні
@dp.callback_query_handler(lambda c: c.data.startswith("edit_select_hour_"))
async def handle_edit_hour_selection(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        data_parts = callback_query.data.split("_")
        selected_hour = int(data_parts[3])
        trip_id = int(data_parts[4])
        
        # Показуємо клавіатуру для вибору хвилин
        await callback_query.message.edit_text(
            select_minutes_text[get_user_lang(user_id)].format(f"{selected_hour:02d}"),
            parse_mode="HTML",
            reply_markup=create_edit_minutes_keyboard(user_id, selected_hour, trip_id)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in edit hour selection: {e}")
        await callback_query.answer("Помилка при виборі години", show_alert=True)


# Обробник вибору хвилин при редагуванні
@dp.callback_query_handler(lambda c: c.data.startswith("edit_select_minute_"))
async def handle_edit_minute_selection(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        data_parts = callback_query.data.split("_")
        selected_hour = int(data_parts[3])
        selected_minute = int(data_parts[4])
        trip_id = int(data_parts[5])
        
        # Формуємо час у форматі HH:MM
        selected_time = f"{selected_hour:02d}:{selected_minute:02d}"
        
        # Оновлюємо час поїздки в базі даних
        update_trip_time(trip_id, selected_time)
        cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
        trip = cursor.fetchone()
        trip_text = get_trip_text(trip, user_id=user_id)
        
        await callback_query.message.edit_text(
            translate("✅ <b>Час поїздки успішно змінений!</b>", user_id) + f"\n\n{trip_text}\n\nВиберіть, що саме потрібно змінити:",
            parse_mode="HTML",
            reply_markup=edit_trip_keyboard(user_id, trip_id)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in edit minute selection: {e}")
        await callback_query.answer("Помилка при оновленні часу", show_alert=True)


# Обробник кнопки "Назад" до редагування поїздки
@dp.callback_query_handler(lambda c: c.data.startswith("back_to_edit_trip_"))
async def back_to_edit_trip(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        trip_id = int(callback_query.data.split("_")[-1])
        
        cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
        trip = cursor.fetchone()
        
        if not trip:
            await callback_query.answer(translate("❕ Поїздку не знайдено.", user_id), show_alert=True)
            return
        
        trip_text = get_trip_text(trip, user_id=user_id)
        await callback_query.message.edit_text(
            f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
            parse_mode="HTML",
            reply_markup=edit_trip_keyboard(user_id, trip_id)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in back to edit trip: {e}")
        await callback_query.answer("Помилка", show_alert=True)


# Обробник кнопки "Назад" до вибору години при редагуванні
@dp.callback_query_handler(lambda c: c.data.startswith("back_to_edit_hour_"))
async def back_to_edit_hour(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        trip_id = int(callback_query.data.split("_")[-1])
        
        await callback_query.message.edit_text(
            select_time_text[get_user_lang(user_id)],
            parse_mode="HTML",
            reply_markup=create_edit_hour_keyboard(user_id, trip_id)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in back to edit hour: {e}")
        await callback_query.answer("Помилка", show_alert=True)

    
        
        
@dp.callback_query_handler(lambda c: c.data.startswith('changestops_'))
async def edit_trip(callback_query: types.CallbackQuery, state: FSMContext):
    trip_id = int(callback_query.data.split('_')[-1])
    user_id = callback_query.from_user.id
    await state.update_data(trip_id=trip_id)

    await callback_query.message.answer(
        translate(
            "📍 Введіть початкову точку, проміжні зупинки та кінцеву точку поїздки <b>через пробіл</b>\n"
            "Наприклад: <b>Київ Черкаси Вінниця Львів Варшава</b>", 
            user_id
        ),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(user_id)
    )
    await callback_query.answer()
    await ChangeTrip.waiting_for_changestops.set()

@dp.message_handler(state=ChangeTrip.waiting_for_changestops)
async def handle_posting_time_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_input = message.text.strip()

    if message.text.lower() in map(str.lower, cancel_texts.values()) or message.text.lower() == "/start":
        await message.answer(translate("Скасовую..", user_id), reply_markup=get_start_keyboard(user_id))
        await my_trips(message, state)
        await state.finish()
        return

    state_data = await state.get_data()
    trip_id = state_data.get("trip_id")

    if trip_id is None:
        await message.reply(translate("❕ Сталася помилка. Спробуйте ще раз."), user_id)
        await state.finish()
        return

    # Очищаємо введений текст від зайвих символів та форматуємо
    cleaned_stops = []
    for stop in user_input.split():  # Розділяємо по пробілах
        stop = stop.strip()
        if stop:  # Перевіряємо, що зупинка не пуста після очистки
            cleaned_stops.append(stop)
    
    if len(cleaned_stops) < 2:
        await message.reply(translate(
            "❕ Потрібно вказати мінімум 2 зупинки (початкову та кінцеву точки).", 
            user_id
        ))
        return

    # З'єднуємо зупинки через кому для збереження в БД
    formatted_stops = ", ".join(cleaned_stops)

    try:
        update_trip_stops(trip_id, formatted_stops)
        cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
        trip = cursor.fetchone()
        trip_text = get_trip_text(trip, user_id = message.from_user.id)
        await message.answer(
            translate("✅ <b>Зупинки поїздки успішно змінені!</b>", user_id),
            parse_mode="HTML",
            reply_markup=get_start_keyboard(user_id)
        )
        await message.answer(
            f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
            parse_mode="HTML",
            reply_markup=edit_trip_keyboard(user_id, trip_id)
        )
        await state.finish()
    except Exception as e:
        await message.reply(translate("❕ Сталася помилка при оновленні даних. Спробуйте пізніше."), user_id)
        print(f"Error updating trip stops: {e}")
        await state.finish()
        
        
@dp.callback_query_handler(lambda c: c.data.startswith('changecar_'))
async def edit_trip(callback_query: types.CallbackQuery, state: FSMContext):
    trip_id = int(callback_query.data.split('_')[-1])
    user_id = callback_query.from_user.id
    cursor.execute("SELECT id, mark, number FROM users_cars WHERE user_id = ?", (user_id,))
    cars = cursor.fetchall()

    if not cars:
        await callback_query.message.answer(
            translate("❕ У вас немає зареєстрованих авто. Додайте авто для продовження.", user_id),
            reply_markup=get_start_keyboard(user_id)
        )
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    for car_id, mark, number in cars:
        button_text = f"{mark} : {number}"
        button = InlineKeyboardButton(text=button_text, callback_data=f"editchoosecar_{car_id}_{trip_id}")
        keyboard.add(button)
    keyboard.add(InlineKeyboardButton(translate("← Назад", user_id), callback_data="cancel_delete_trip_"))

    await callback_query.message.edit_text(
        translate("🚗 Оберіть авто для поїздки:", user_id),
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("editchoosecar_"))
async def handle_car_selection(callback_query: types.CallbackQuery):
    car_id = int(callback_query.data.split("_")[1])
    trip_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    cursor.execute("SELECT mark, number FROM users_cars WHERE id = ?", (car_id,))
    car_data = cursor.fetchone()

    if car_data:
        car_mark, car_number = car_data
    else:
        await callback_query.answer(translate("❕ Сталася помилка. Автомобіль не знайдено."), show_alert=True)
        return
    cursor.execute(
        "UPDATE trips SET car_id = ?, car_mark = ?, car_number = ? WHERE id = ?",
        (car_id, car_mark, car_number, trip_id)
    )
    conn.commit()
    cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()

    if not trip:
        await callback_query.answer(translate("❕ Помилка. Поїздку не знайдено.", user_id), show_alert=True)
        return
    trip_text = get_trip_text(trip, user_id = callback_query.from_user.id)
    await callback_query.message.edit_text(
        f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
        parse_mode="HTML",
        reply_markup=edit_trip_keyboard(callback_query.from_user.id, trip_id)
    )
    await callback_query.answer(translate("✅ Автомобіль змінено успішно!", user_id))

        
        

@dp.callback_query_handler(lambda c: c.data.startswith('changeseats_'))
async def edit_trip(callback_query: types.CallbackQuery, state: FSMContext):
    trip_id = int(callback_query.data.split('_')[-1])
    user_id = callback_query.from_user.id
    cursor.execute("SELECT id, mark, number FROM users_cars WHERE user_id = ?", (user_id,))
    cars = cursor.fetchall()

    keyboard = InlineKeyboardMarkup(row_width=4)
    buttons = [InlineKeyboardButton(text=str(i), callback_data=f"editchooseseats_{i}_{trip_id}") for i in range(1, 17)]

    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton(translate("← Назад", user_id), callback_data="cancel_delete_trip_"),
    )
    await callback_query.message.edit_text(translate(
        "🚗 Виберіть кількість вільних місць для поїздки:", user_id), reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("editchooseseats_"))
async def handle_car_selection(callback_query: types.CallbackQuery):
    seats = int(callback_query.data.split("_")[1])
    trip_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    cursor.execute(
        "UPDATE trips SET seats = ? WHERE id = ?",
        (seats, trip_id)
    )
    conn.commit()
    cursor.execute("SELECT id, date, time, car_mark, car_number, stops, seats, watched FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()

    if not trip:
        await callback_query.answer(translate("❕ Помилка. Поїздку не знайдено.", user_id), show_alert=True)
        return
    trip_text = get_trip_text(trip, user_id = callback_query.from_user.id)
    
    await callback_query.message.edit_text(
        f"{trip_text}\n\nВиберіть, що саме потрібно змінити:",
        parse_mode="HTML",
        reply_markup=edit_trip_keyboard(callback_query.from_user.id, trip_id)
    )

        
        

@dp.callback_query_handler(lambda c: c.data.startswith("calendar_nav_create_"))
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
        
        markup = create_trip_calendar(user_id, new_year, new_month)
            
        await callback_query.message.edit_reply_markup(reply_markup=markup)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Error in calendar navigation: {e}")
        await callback_query.answer(translate("❕ Помилка при навігації календаря", user_id), show_alert=True)
    
    


@dp.callback_query_handler(lambda c: c.data.startswith("calendar_nav_repeat_"))
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
        
        markup = create_trip_calendar_repeat(user_id, new_year, new_month)
            
        await callback_query.message.edit_reply_markup(reply_markup=markup)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Error in calendar navigation: {e}")
        await callback_query.answer(translate("❕ Помилка при навігації календаря", user_id), show_alert=True)
    

@dp.callback_query_handler(lambda c: c.data.startswith('repeat_trip_'))
async def repeat_trip(callback_query: types.CallbackQuery):
    try:
        trip_id = int(callback_query.data.split('_')[-1])
        user_id = callback_query.from_user.id
        
        # Отримуємо дані про стару поїздку
        cursor.execute("""
            SELECT car_id, car_mark, car_number, stops, seats
            FROM trips 
            WHERE id = ?
        """, (trip_id,))
        trip_data = cursor.fetchone()
        
        if not trip_data:
            await callback_query.answer(translate("❕ Поїздку не знайдено.", user_id), show_alert=True)
            return
            
        # Зберігаємо дані для створення нової поїздки
        user_trip_data[user_id] = {
            "car_id": trip_data[0],
            "car_mark": trip_data[1],
            "car_number": trip_data[2],
            "stops": trip_data[3],
            "seats": trip_data[4]
        }
        
        # Просимо обрати нову дату
        await callback_query.message.edit_text(
            select_date_text[get_user_lang(user_id)],
            parse_mode="HTML",
            reply_markup=create_trip_calendar_repeat(user_id)
        )
        
    except Exception as e:
        print(f"Error in repeat trip: {e}")
        await callback_query.answer(translate("❕ Помилка при повторенні поїздки", user_id), show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('repeattrip_'))
async def handle_repeat_trip_selection(callback_query: types.CallbackQuery):
    date_str = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    
    # Зберігаємо дату
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    user_trip_data[user_id]["repeat_date"] = selected_date
    
    # Показуємо клавіатуру для вибору часу
    await callback_query.message.edit_text(
        select_time_text[get_user_lang(user_id)],
        parse_mode="HTML",
        reply_markup=create_hour_keyboard(user_id)
    )
    await callback_query.answer()



@dp.callback_query_handler(lambda c: c.data == "confirm_repeat_trip")
async def confirm_repeat_trip(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    trip_data = user_trip_data[user_id]
    selected_date = trip_data["repeat_date"]
    selected_time = trip_data["time"]
    
    # Поточна дата та час для поля created_at
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Вставляємо дані про нову поїздку в таблицю trips
    cursor.execute("""
        INSERT INTO trips (user_id, car_id, date, time, car_mark, car_number, seats, stops, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        trip_data["car_id"],
        selected_date.strftime('%Y-%m-%d'),
        selected_time,
        trip_data["car_mark"],
        trip_data["car_number"],
        trip_data["seats"],
        trip_data["stops"],
        created_at
    ))
    conn.commit()
    
    await callback_query.message.edit_text(
        translate("<b>✅ Поїздку успішно створено!</b>", user_id),
        parse_mode="HTML"
    )
    await callback_query.answer()
    
    # Очищаємо дані користувача
    if user_id in user_trip_data:
        del user_trip_data[user_id]

@dp.callback_query_handler(lambda c: c.data == "cancel_repeat_trip")
async def cancel_repeat_trip(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(
        translate("<b>❕ Створення поїздки скасовано.</b>", user_id),
        parse_mode="HTML"
    )
    await callback_query.answer()
    
    # Очищаємо дані користувача
    if user_id in user_trip_data:
        del user_trip_data[user_id]





    
        
        
