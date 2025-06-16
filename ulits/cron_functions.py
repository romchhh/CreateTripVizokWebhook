import sqlite3
from datetime import datetime
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import bot
from database.client_db import cursor, conn
from ulits.translate import translate

async def send_order_review_message(user_id, driver_id, trip_route):
    try:
        message = translate(f"🤔 Кілька днів тому ви цікавилися поїздкою за маршрутом: <b>{trip_route}</b>.\n\n" \
                  "🚗 Як все пройшло? \n\n" \
                  "💬 Поділіться своїм відгуком, щоб ми могли покращити наш сервіс. Нам важлива ваша думка!", user_id)

        keyboard = InlineKeyboardMarkup(row_width=1)
        review_button = InlineKeyboardButton(text=translate("🚘 Залишити відгук", user_id), callback_data=f"send_review_{driver_id}")
        keyboard.add(review_button)
        await bot.send_message(user_id, message, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Error sending review message: {e}")



async def send_reviews_to_users():
    try:
        today_date = datetime.now().strftime('%d.%m.%Y')
        
        cursor.execute('''SELECT user_id, driver_id, trip_stops FROM send_review 
                          WHERE date_to_send = ? AND sent = 0''', (today_date,))
        users_to_send_review = cursor.fetchall()

        for user_id, driver_id, trip_stops in users_to_send_review:
            trip_route = trip_stops 
            
            await send_order_review_message(user_id, driver_id, trip_route)

            cursor.execute('''UPDATE send_review 
                              SET sent = 1 
                              WHERE user_id = ? AND date_to_send = ?''', (user_id, today_date))
            conn.commit()

    except Exception as e:
        print(f"Error in sending reviews to users: {e}")