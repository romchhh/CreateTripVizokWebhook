from main import bot, dp, scheduler

from config import *
from ulits.filters import *

from aiogram import types
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext
from keyboards.client_keyboards import get_start_keyboard
from keyboards.admin_keyboards import *
from database.client_db import *
from database.admin_db import *
import pandas as pd
import datetime, os

from ulits.admin_states import *
import asyncio
from aiogram import types, Dispatcher
from ulits.admin_states import Form
from aiogram.dispatcher.filters import Text
from ulits.admin_functions import format_entities, parse_url_buttons
from ulits.translate import translate



html = 'HTML'


async def antiflood(*args, **kwargs):
    m = args[0]
    await m.answer("Не поспішай :)")

async def on_startup(dp):
    me = await bot.get_me()
    print(f'Bot: @{me.username} запущений!')

async def on_shutdown(dp):
    me = await bot.get_me()
    print(f'Bot: @{me.username} зупинений!')


@dp.message_handler(IsAdmin(), lambda message: message.text == "Адмін панель 💻")
async def my_parcel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in administrators:
        await message.answer("Вітаємо в Адмін панелі 💻", parse_mode="HTML", reply_markup=admin_keyboard())
    else:
        return
    
    
@dp.message_handler(IsAdmin(), lambda message: message.text == "Головне меню")
async def my_parcel(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = message.from_user.id
    if user_id in administrators:
        keyboard = get_admin_keyboard(user_id)
    else:
        keyboard = get_start_keyboard(user_id)
            
    greeting_message = f"Вітаємо, {user.username}! 👋 \nВи звернулися до сервісу спільних поїздок <b>Vizok</b> 🚙.\nЧим можемо бути корисні?"
    photo_path = 'data/hello.jpg'
    with open(photo_path, 'rb') as photo:
        await message.answer_photo(photo=photo, caption=greeting_message, reply_markup=keyboard)
        
@dp.message_handler(IsAdmin(), lambda message: message.text == "Статистика")
async def statistic_handler(message: types.Message):
    total_users = get_users_count()
    active_users = get_active_users_count()

    response_message = (
            f"👥 Загальна кількість користувачів: {total_users}\n"
            f"📱 Кількість активних користувачів: {active_users}\n"
        )
    await message.answer(response_message, parse_mode="HTML")
        
        
        
        
@dp.message_handler(IsAdmin(), lambda message: message.text == "Список пасажирів")
async def export_database(message: types.Message):
    today = datetime.datetime.now()
    last_month = today - datetime.timedelta(days=30)
    last_month_str = last_month.strftime("%Y-%m-%d")

    # Отримуємо user_id з таблиці users_search за останні 30 днів
    query = """
    SELECT
        user_id,
        COUNT(*) AS search_count,
        GROUP_CONCAT(search_stops, ', ') AS search_stops
    FROM
        users_search
    WHERE
        search_date >= ?
    GROUP BY
        user_id
    """
    cursor.execute(query, (last_month_str,))
    user_search_data = cursor.fetchall()

    if not user_search_data:
        await message.reply("No search data found for the last month.")
        return

    # Отримуємо деталі користувачів з таблиці users
    user_ids = [row[0] for row in user_search_data]
    placeholders = ','.join('?' * len(user_ids))
    query = f"""
    SELECT
        user_id,
        user_name,
        real_name,
        phone
    FROM
        users
    WHERE
        user_id IN ({placeholders})
    """
    cursor.execute(query, user_ids)
    user_details = cursor.fetchall()

    # Створюємо словник для швидкого доступу до деталей користувачів
    user_details_dict = {row[0]: row[1:] for row in user_details}

    # Формуємо DataFrame з даними
    data = []
    for row in user_search_data:
        user_id = row[0]
        search_count = row[1]
        search_stops = row[2]
        user_info = user_details_dict.get(user_id, ("Невідомо", "Невідомо", "Невідомо"))
        data.append([user_id, *user_info, search_count, search_stops])

    df = pd.DataFrame(data, columns=['ІД пасажира', 'Телеграм юзернейм', 'Справжнє імя', 'Телефон', 'Кількість пошуків за останні 30 днів', 'Маршрути пошуку'])

    # Додаємо колонку з номером рядка
    df.index += 1
    df.reset_index(inplace=True)
    df.rename(columns={'index': '№'}, inplace=True)

    # Створюємо Excel файл з форматуванням
    writer = pd.ExcelWriter('user_statistics.xlsx', engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Статистика')
    
    # Отримуємо об'єкти для роботи з Excel
    workbook = writer.book
    worksheet = writer.sheets['Статистика']
    
    # Створюємо формати
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'center',
        'fg_color': '#D9E1F2',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'left',
        'border': 1
    })
    
    number_format = workbook.add_format({
        'valign': 'vcenter',
        'align': 'center',
        'border': 1
    })

    # Застосовуємо формати до заголовків
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    # Встановлюємо ширину стовпців та формат для кожного типу даних
    worksheet.set_column('A:A', 8, number_format)  # №
    worksheet.set_column('B:B', 15, number_format)  # ІД пасажира
    worksheet.set_column('C:C', 25, cell_format)  # Телеграм юзернейм
    worksheet.set_column('D:D', 30, cell_format)  # Справжнє імя
    worksheet.set_column('E:E', 20, cell_format)  # Телефон
    worksheet.set_column('F:F', 25, number_format)  # Кількість пошуків
    worksheet.set_column('G:G', 70, cell_format)  # Маршрути пошуку

    # Застосовуємо формати до даних
    for row in range(1, len(df) + 1):
        worksheet.set_row(row, 30)  # Висота рядка
        for col in range(len(df.columns)):
            if col in [0, 1, 5]:  # Числові стовпці
                worksheet.write(row, col, df.iloc[row-1, col], number_format)
            else:  # Текстові стовпці
                worksheet.write(row, col, df.iloc[row-1, col], cell_format)

    # Додаємо автофільтр
    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    
    # Закріплюємо верхній рядок
    worksheet.freeze_panes(1, 0)
    
    # Додаємо заголовок з датою
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    worksheet.merge_range(f'A1:G1', f'Статистика пасажирів за період {last_month_str} - {today.strftime("%Y-%m-%d")}', title_format)
    worksheet.write_row(1, 0, df.columns, header_format)
    
    # Зміщуємо дані на один рядок вниз
    for row in range(len(df) + 1, 1, -1):
        for col in range(len(df.columns)):
            if col in [0, 1, 5]:  # Числові стовпці
                worksheet.write(row + 1, col, df.iloc[row-2, col] if row > 1 else None, number_format)
            else:  # Текстові стовпці
                worksheet.write(row + 1, col, df.iloc[row-2, col] if row > 1 else None, cell_format)

    writer.close()

    # Перевіряємо, чи файл створився
    excel_file = 'user_statistics.xlsx'
    import os
    if os.path.exists(excel_file):
        print(f"File {excel_file} created successfully.")
    else:
        print(f"File {excel_file} creation failed.")

    # Відправляємо файл користувачу
    await message.reply_document(
        InputFile(excel_file), 
        caption=f"📊 Статистика пасажирів за період {last_month_str} - {today.strftime('%Y-%m-%d')}", 
        reply_markup=admin_keyboard()
    )
    os.remove(excel_file)  # Видаляємо файл після відправки
    
    
    
    
@dp.message_handler(IsAdmin(), lambda message: message.text == "Популярні маршрути")
async def popular_routes(message: types.Message):
    user_id = message.from_user.id

    try:
        # Отримуємо топ-30 популярних маршрутів
        cursor.execute('''
            SELECT search_stops, COUNT(*) AS search_count
            FROM users_search
            GROUP BY search_stops
            ORDER BY search_count DESC
            LIMIT 30
        ''')
        popular_routes = cursor.fetchall()

        if popular_routes:
            # Форматуємо результат у зручний для читання вигляд
            result_message = "🚗 <b>Топ-30 популярних маршрутів:</b>\n\n"
            for index, (route, count) in enumerate(popular_routes, start=1):
                result_message += f"{index}. <b>{route}</b> — <i>{count} пошуків</i>\n"

            await message.answer(result_message, parse_mode="HTML")
        else:
            await message.answer("🔍 Немає даних про популярні маршрути.", parse_mode="HTML")

    except Exception as e:
        await message.answer("❕ Сталася помилка під час отримання даних. Спробуйте ще раз.", parse_mode="HTML")
        print(f"Error: {e}")



# Обробник команди "Список водіїв"
@dp.message_handler(IsAdmin(), lambda message: message.text == "Список водіїв")
async def ask_start_date(message: types.Message):
    await message.reply("Будь ласка, введіть початкову дату у форматі РРРР-ММ-ДД:", reply_markup=get_cancel_keyboard())
    await DriverStats.waiting_for_start_date.set()

# Обробник для отримання початкової дати
@dp.message_handler(state=DriverStats.waiting_for_start_date)
async def ask_end_date(message: types.Message, state: FSMContext):
    if message.text == "← Скасувати":
        await message.reply("Ви відмінили операцію.", reply_markup=admin_keyboard())
        await state.finish()
        return
    try:
        start_date = datetime.datetime.strptime(message.text, "%Y-%m-%d")
        await state.update_data(start_date=start_date.strftime("%Y-%m-%d"))
        await message.reply("Тепер введіть кінцеву дату у форматі РРРР-ММ-ДД:")
        await DriverStats.waiting_for_end_date.set()
    except ValueError:
        await message.reply("Невірний формат дати. Будь ласка, введіть дату у форматі РРРР-ММ-ДД.")

# Обробник для отримання кінцевої дати та формування звіту
@dp.message_handler(state=DriverStats.waiting_for_end_date)
async def export_database(message: types.Message, state: FSMContext):
    if message.text == "← Скасувати":
        await message.reply("Ви відмінили операцію.", reply_markup=admin_keyboard())
        await state.finish()
        return
    try:
        end_date = datetime.datetime.strptime(message.text, "%Y-%m-%d")
        user_data = await state.get_data()
        start_date = user_data['start_date']

        if start_date > end_date.strftime("%Y-%m-%d"):
            await message.reply("Початкова дата не може бути пізніше кінцевої. Спробуйте ще раз.")
            return

        # Перший запит - отримуємо статистику водіїв
        drivers_query = """
        SELECT 
            t.user_id,
            COUNT(t.user_id) AS trip_count,
            AVG(CASE WHEN r.stars IS NOT NULL THEN r.stars END) AS avg_rating,
            MAX(t.date) AS last_trip_date
        FROM trips t
        LEFT JOIN reviews r ON t.user_id = r.receiver_id
        WHERE t.date BETWEEN ? AND ?
        GROUP BY t.user_id
        """
        cursor.execute(drivers_query, (start_date, end_date.strftime("%Y-%m-%d")))
        drivers_stats = cursor.fetchall()

        if not drivers_stats:
            await message.reply("Дані про водіїв за вказаний період відсутні.")
            return

        driver_ids = [str(row[0]) for row in drivers_stats]
        
        # Формуємо запит з дужками для IN clause
        users_query = f"""
        SELECT user_id, user_name, real_name, phone
        FROM users 
        WHERE user_id IN ({','.join(driver_ids)})
        """
        print("Full Query:", users_query)
        
        cursor.execute(users_query)
        users_data = {str(row[0]): row[1:] for row in cursor.fetchall()}
        
        print("Users Data:", users_data)
        # Формуємо фінальні дані
        data = []
        for driver_stat in drivers_stats:
            user_id = str(driver_stat[0])
            user_info = users_data.get(user_id, ("Невідомо", "Невідомо", "Невідомо"))
            data.append([
                user_id,
                user_info[0] or "Невідомо",  # username
                user_info[1] or "Невідомо",  # real_name
                user_info[2] or "Невідомо",  # phone
                driver_stat[1],              # trip_count
                round(driver_stat[2], 2) if driver_stat[2] else 0,  # avg_rating
                driver_stat[3]               # last_trip_date
            ])

        # Створення DataFrame
        df = pd.DataFrame(data, columns=[
            'ІД водія', 'Телеграм юзернейм водія', 'Реальне імя водія', 
            'Номер телефону водія', 'Кількість поїздок', 'Середній рейтинг', 
            'Дата останньої поїздки'
        ])

        # Додаємо колонку з номером рядка
        df.index += 1
        df.reset_index(inplace=True)
        df.rename(columns={'index': '№'}, inplace=True)

        # Налаштовуємо ширину стовпців
        writer = pd.ExcelWriter('driver_statistics.xlsx', engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        worksheet = writer.sheets['Sheet1']
        workbook = writer.book

        # Створюємо формати
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#D9E1F2',
            'border': 1
        })

        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'left',
            'border': 1
        })

        number_format = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1
        })

        # Застосовуємо формати до заголовків
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Встановлюємо ширину стовпців та формат для кожного типу даних
        worksheet.set_column('A:A', 8, number_format)  # №
        worksheet.set_column('B:B', 15, number_format)  # ІД водія
        worksheet.set_column('C:C', 25, cell_format)  # Телеграм юзернейм
        worksheet.set_column('D:D', 30, cell_format)  # Реальне ім'я
        worksheet.set_column('E:E', 20, cell_format)  # Телефон
        worksheet.set_column('F:F', 20, number_format)  # Кількість поїздок
        worksheet.set_column('G:G', 15, number_format)  # Середній рейтинг
        worksheet.set_column('H:H', 25, cell_format)  # Дата останньої поїздки

        # Встановлюємо висоту рядків та застосовуємо формати до даних
        for row in range(1, len(df) + 1):
            worksheet.set_row(row, 30)  # Висота рядка
            for col in range(len(df.columns)):
                if col in [0, 1, 5, 6]:  # Числові стовпці
                    worksheet.write(row, col, df.iloc[row-1, col], number_format)
                else:  # Текстові стовпці
                    worksheet.write(row, col, df.iloc[row-1, col], cell_format)

        # Додаємо автофільтр
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        
        # Закріплюємо верхній рядок
        worksheet.freeze_panes(1, 0)

        # Додаємо заголовок з датою
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        worksheet.merge_range(f'A1:H1', f'Статистика водіїв за період {start_date} - {end_date.strftime("%Y-%m-%d")}', title_format)
        worksheet.write_row(1, 0, df.columns, header_format)

        # Зміщуємо дані на один рядок вниз
        for row in range(len(df) + 1, 1, -1):
            for col in range(len(df.columns)):
                if col in [0, 1, 5, 6]:  # Числові стовпці
                    worksheet.write(row + 1, col, df.iloc[row-2, col] if row > 1 else None, number_format)
                else:  # Текстові стовпці
                    worksheet.write(row + 1, col, df.iloc[row-2, col] if row > 1 else None, cell_format)

        writer.close()

        await message.reply_document(InputFile('driver_statistics.xlsx'), caption="Статистика водіїв за обраний період", reply_markup=admin_keyboard())
        os.remove('driver_statistics.xlsx')

    except ValueError:
        await message.reply("Невірний формат дати. Будь ласка, введіть дату у форматі РРРР-ММ-ДД.")
    finally:
        await state.finish()
         
         
@dp.message_handler(IsAdmin(), lambda message: message.text == "Вигрузити БД")
async def export_database(message: types.Message):
    cursor.execute('SELECT * FROM users')
    users_data = cursor.fetchall()
    users_columns = [description[0] for description in cursor.description]

    cursor.execute('SELECT * FROM trips')
    trips_data = cursor.fetchall()
    trips_columns = [description[0] for description in cursor.description]

    cursor.execute('SELECT * FROM reviews')
    reviews_data = cursor.fetchall()
    reviews_columns = [description[0] for description in cursor.description]

    users_df = pd.DataFrame(users_data, columns=users_columns)
    trips_df = pd.DataFrame(trips_data, columns=trips_columns)
    reviews_df = pd.DataFrame(reviews_data, columns=reviews_columns)

    with pd.ExcelWriter('database_export.xlsx', engine='xlsxwriter') as writer:
        # Записуємо кожен DataFrame на окремий лист
        users_df.to_excel(writer, sheet_name='Users', index=False)
        trips_df.to_excel(writer, sheet_name='Trips', index=False)
        reviews_df.to_excel(writer, sheet_name='Reviews', index=False)

        # Отримуємо об'єкт книги
        workbook = writer.book

        # Створюємо формати
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#D9E1F2',
            'border': 1
        })

        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'left',
            'border': 1
        })

        number_format = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1
        })

        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd hh:mm',
            'valign': 'vcenter',
            'align': 'center',
            'border': 1
        })

        # Форматуємо таблицю Users
        worksheet_users = writer.sheets['Users']
        for col_num, value in enumerate(users_columns):
            worksheet_users.write(0, col_num, value, header_format)
        
        worksheet_users.set_column('A:A', 15)  # user_id
        worksheet_users.set_column('B:B', 25)  # user_name
        worksheet_users.set_column('C:C', 30)  # real_name
        worksheet_users.set_column('D:D', 20)  # phone
        worksheet_users.set_column('E:E', 15)  # role
        worksheet_users.set_column('F:F', 20)  # registration_date
        worksheet_users.set_column('G:G', 15)  # status

        # Форматуємо таблицю Trips
        worksheet_trips = writer.sheets['Trips']
        for col_num, value in enumerate(trips_columns):
            worksheet_trips.write(0, col_num, value, header_format)
        
        worksheet_trips.set_column('A:A', 15)  # trip_id
        worksheet_trips.set_column('B:B', 15)  # user_id
        worksheet_trips.set_column('C:C', 25)  # from_location
        worksheet_trips.set_column('D:D', 25)  # to_location
        worksheet_trips.set_column('E:E', 20)  # date
        worksheet_trips.set_column('F:F', 15)  # time
        worksheet_trips.set_column('G:G', 15)  # seats
        worksheet_trips.set_column('H:H', 20)  # car
        worksheet_trips.set_column('I:I', 15)  # status

        # Форматуємо таблицю Reviews
        worksheet_reviews = writer.sheets['Reviews']
        for col_num, value in enumerate(reviews_columns):
            worksheet_reviews.write(0, col_num, value, header_format)
        
        worksheet_reviews.set_column('A:A', 15)  # review_id
        worksheet_reviews.set_column('B:B', 15)  # sender_id
        worksheet_reviews.set_column('C:C', 15)  # receiver_id
        worksheet_reviews.set_column('D:D', 15)  # stars
        worksheet_reviews.set_column('E:E', 40)  # comment
        worksheet_reviews.set_column('F:F', 20)  # date

        # Застосовуємо формати до даних та встановлюємо висоту рядків для всіх таблиць
        for worksheet, df in [
            (worksheet_users, users_df),
            (worksheet_trips, trips_df),
            (worksheet_reviews, reviews_df)
        ]:
            # Встановлюємо висоту рядків
            for row in range(1, len(df) + 1):
                worksheet.set_row(row, 30)
                
                # Записуємо дані з відповідним форматуванням
                for col in range(len(df.columns)):
                    value = df.iloc[row-1, col]
                    
                    # Визначаємо формат в залежності від типу даних
                    if isinstance(value, (int, float)):
                        worksheet.write(row, col, value, number_format)
                    elif isinstance(value, (datetime.date, datetime.datetime)):
                        worksheet.write(row, col, value, date_format)
                    else:
                        worksheet.write(row, col, value, cell_format)

            # Додаємо автофільтр
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            # Закріплюємо верхній рядок
            worksheet.freeze_panes(1, 0)

    # Відправляємо файл
    with open('database_export.xlsx', 'rb') as file:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        await bot.send_document(
            message.chat.id,
            document=file,
            caption=f"📊 Експорт бази даних від {current_date}"
        )
    
    # Видаляємо тимчасовий файл
    os.remove('database_export.xlsx')



@dp.message_handler(IsAdmin(), lambda message: message.text == "Статистика посилань")
async def show_referral_stats(message: types.Message):
    # Отримуємо загальну кількість користувачів
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Отримуємо статистику по реферальним посиланням
    cursor.execute('''
        SELECT platform, name, code, clicks 
        FROM referral_links 
        ORDER BY platform, clicks DESC
    ''')
    stats = cursor.fetchall()
    
    # Рахуємо загальну кількість переходів за реферальними посиланнями
    total_ref_clicks = sum(row[3] for row in stats)
    
    # Рахуємо кількість користувачів, що прийшли без реферального посилання
    other_users = total_users - total_ref_clicks
    
    response = "📊 <b>Статистика переходів за посиланнями:</b>\n\n"
    current_platform = None
    
    for platform, name, code, clicks in stats:
        if platform != current_platform:
            response += f"\n<b>{platform}:</b>\n"
            current_platform = platform
            
        if total_users > 0:
            percentage = (clicks / total_users) * 100
        else:
            percentage = 0
            
        full_link = f"https://t.me/VizokUAbot?start={code}"
        response += f"- {full_link}\n  Переходів: {clicks} ({percentage:.1f}%)\n"
    
    # Додаємо статистику по користувачам без реферального посилання
    if total_users > 0:
        other_percentage = (other_users / total_users) * 100
    else:
        other_percentage = 0
        
    response += f"\n<b>Інше джерело:</b>\n"
    response += f"- Прямі переходи: {other_users} ({other_percentage:.1f}%)\n"
    
    response += f"\n<b>Всього користувачів:</b> {total_users}"
    
    await message.answer(response, parse_mode="HTML")


@dp.message_handler(IsAdmin(), lambda message: message.text == "Розсилка")
async def create_post(message: types.Message):
    user_id = message.from_user.id
    description = (
        "<b>СТВОРЕННЯ ПОСТУ:</b>\n\n"
        "Ця функція дозволяє створити пост і розіслати його всім користувачам бота. "
        "Ви можете додати текст, фото, відео або документ, а також URL-кнопки для посилання на зовнішні ресурси. "
        "Після створення поста, ви зможете переглянути його і підтвердити розсилку.\n\n"
        "Кроки для створення поста:\n"
        "1. Надішліть текст, фото, відео або документ, який ви хочете розіслати.\n"
        "2. Додайте опис, якщо потрібно.\n"
        "3. Додайте URL-кнопки, якщо потрібно.\n"
        "4. Перегляньте пост і підтвердьте розсилку.\n\n"
        "Після підтвердження розсилки, пост буде відправлено всім користувачам бота."
    )
    await message.answer(description, parse_mode='HTML', reply_markup=get_broadcast_keyboard())


user_data = {}

def initialize_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {}

@dp.callback_query_handler(Text(startswith='create_post'))
async def process_channel_selection(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    initialize_user_data(user_id)

    await Form.content.set()
    await callback_query.message.edit_text(
        f"Будь ласка, надішліть те, що ви хочете розіслати користувачам:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Назад", callback_data="back_to_posts")
        )
    )

@dp.message_handler(state=Form.content, content_types=['text', 'photo', 'video', 'document'])
async def handle_content(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    content_type = message.content_type
    content_info = ""
    media_info = None
    media_type = None
    html_content = None  

    if content_type == 'text':
        content_info = message.text
        entities = message.entities 

        if entities:
            html_content = format_entities(content_info, entities)

        else:
            html_content = content_info 

        await message.answer(html_content, parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        media_type = None
    elif content_type == 'photo':
        media_info = message.photo[-1].file_id
        await message.answer_photo(media_info, reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        media_type = 'photo'
    elif content_type == 'video':
        media_info = message.video.file_id
        await message.answer_video(media_info, reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        media_type = 'video'
    elif content_type == 'document':
        media_info = message.document.file_id
        await message.answer_document(media_info, reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        media_type = 'document'
    else:
        await message.answer("Невідомий формат.")
    if html_content:
        user_data[user_id]['content'] = html_content
        await state.update_data(content=html_content)

    user_data[user_id]['media'] = media_info
    user_data[user_id]['media_type'] = media_type

    await state.finish()

    
@dp.callback_query_handler(Text(startswith='media_'))
async def handle_media(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await Form.media.set()
    await callback_query.message.answer(
        "Будь ласка, надішліть медіа, яке ви хочете додати або змінити:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Назад", callback_data="back_to_my_post")
        )
    )

@dp.message_handler(state=Form.media, content_types=['photo', 'video', 'document'])
async def handle_media_content(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    media_info = None
    media_type = None
    if message.content_type == 'photo':
        media_info = message.photo[-1].file_id
        media_type = 'photo'
    elif message.content_type == 'video':
        media_info = message.video.file_id
        media_type = 'video'
    elif message.content_type == 'document':
        media_info = message.document.file_id
        media_type = 'document'

    user_data[user_id]['media'] = media_info
    user_data[user_id]['media_type'] = media_type

    content_info = user_data[user_id].get('content')

    if media_info:
        if media_type == 'photo':
            await message.answer_photo(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        elif media_type == 'video':
            await message.answer_video(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        elif media_type == 'document':
            await message.answer_document(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
    else:
        await message.answer(f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))

    await state.finish()

@dp.callback_query_handler(Text(startswith='add_'))
async def handle_description(callback_query: types.CallbackQuery, state: FSMContext):
    await Form.description.set()
    await callback_query.message.answer(
        "Будь ласка, надішліть опис, який ви хочете додати або змінити:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Назад", callback_data="back_to_my_post")
        )
    )

@dp.message_handler(state=Form.description, content_types=['text'])
async def handle_description_content(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    media_info = user_data[user_id].get('media')
    media_type = user_data[user_id].get('media_type')
    
    content_info = message.text
    entities = message.entities 
    formatted_content = format_entities(content_info, entities)
    
    user_data[user_id]['content'] = formatted_content

    if media_info:
        if media_type == 'photo':
            await message.answer_photo(media_info, caption=formatted_content, parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        elif media_type == 'video':
            await message.answer_video(media_info, caption=formatted_content, parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
        elif media_type == 'document':
            await message.answer_document(media_info, caption=formatted_content, parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))
    else:
        await message.answer(formatted_content, parse_mode='HTML', reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))

    await state.finish()


@dp.callback_query_handler(Text(startswith='url_buttons_'))
async def handle_url_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await Form.url_buttons.set()
    await callback_query.message.answer(
        "<b>URL-КНОПКИ</b>\n\n"
        "Будь ласка, надішліть список URL-кнопок у форматі:\n\n"
        "<code>Кнопка 1 - http://link.com\n"
        "Кнопка 2 - http://link.com</code>\n\n"
        "Використовуйте роздільник <code>' | '</code>, щоб додати до 8 кнопок в один ряд (допустимо 15 рядів):\n\n"
        "<code>Кнопка 1 - http://link.com | Кнопка 2 - http://link.com</code>\n\n",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Назад", callback_data="back_to_my_post")
        ),
        disable_web_page_preview=True 
    )


@dp.message_handler(state=Form.url_buttons, content_types=['text'])
async def handle_url_buttons_content(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    media_info = user_data[user_id].get('media')
    media_type = user_data[user_id].get('media_type')
    content_info = user_data[user_id].get('content')

    url_buttons_text = message.text
    url_buttons = parse_url_buttons(url_buttons_text)

    user_data[user_id]['url_buttons'] = url_buttons

    if media_info:
        if media_type == 'photo':
            await message.answer_photo(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, url_buttons))
        elif media_type == 'video':
            await message.answer_video(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, url_buttons))
        elif media_type == 'document':
            await message.answer_document(media_info, caption=f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, url_buttons))
    else:
        await message.answer(f"{content_info}", parse_mode='HTML', reply_markup=create_post(user_data, user_id, url_buttons))

    await state.finish()


@dp.callback_query_handler(Text(startswith='bell_'))
async def handle_comments(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if 'bell' not in user_data[user_id]:
        user_data[user_id]['bell'] = 0 
    user_data[user_id]['bell'] = 1 if user_data[user_id]['bell'] == 0 else 0
    await callback_query.message.edit_reply_markup(reply_markup=create_post(user_data, user_id, user_data[user_id].get('url_buttons')))

    
@dp.callback_query_handler(Text(startswith='next_'))
async def handle_url_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    await callback_query.message.answer("<b>💼 НАЛАШТУВАННЯ ВІДПРАВКИ</b>\n\n"
                                           f"Пост готовий до розсилки.", parse_mode='HTML', reply_markup=publish_post(user_data, user_id))
    
    
    
@dp.callback_query_handler(Text(startswith='publish_'))
async def confirm_publish(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    confirm_keyboard = InlineKeyboardMarkup(row_width=2)
    confirm_keyboard.add(
        InlineKeyboardButton("✓ Так", callback_data=f"confirm_publish_"),
        InlineKeyboardButton("❌ Ні", callback_data="cancel_publish")
    )
    await callback_query.message.edit_text("Ви впевнені, що хочете зробити розсилку?", reply_markup=confirm_keyboard)

@dp.callback_query_handler(Text(startswith='confirm_publish_'))
async def handle_publish_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    initialize_user_data(user_id)
    
    await callback_query.message.edit_text("Починаю розсилку...")

    media_info = user_data[user_id].get('media')
    media_type = user_data[user_id].get('media_type')
    content_info = user_data[user_id].get('content')
    url_buttons = user_data[user_id].get('url_buttons')

    bell = user_data[user_id].get('bell', 0) 
    disable_notification = (bell == 0)
    user_ids = get_all_user_ids()

    sent_count = 0
    for recipient_id in user_ids: 
        try:
            translated_content = translate(content_info, recipient_id)
            if media_info:
                if media_type == 'photo':
                    await bot.send_photo(recipient_id, media_info, caption=translated_content, parse_mode='HTML', reply_markup=post_keyboard(user_data, user_id, url_buttons), disable_notification=disable_notification)
                elif media_type == 'video':
                    await bot.send_video(recipient_id, media_info, caption=translated_content, parse_mode='HTML', reply_markup=post_keyboard(user_data, user_id, url_buttons), disable_notification=disable_notification)
                elif media_type == 'document':
                    await bot.send_document(recipient_id, media_info, caption=translated_content, parse_mode='HTML', reply_markup=post_keyboard(user_data, user_id, url_buttons), disable_notification=disable_notification)
            else:
                await bot.send_message(recipient_id, translated_content, parse_mode='HTML', reply_markup=post_keyboard(user_data, user_id, url_buttons), disable_notification=disable_notification)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send message to user {recipient_id}: {e}")
        await asyncio.sleep(2)

    await callback_query.message.answer(f"Пост опубліковано для {sent_count} користувачів!", show_alert=True)


@dp.callback_query_handler(text="back_to_my_post", state=[Form.url_buttons, Form.description, Form.media])
async def process_channel_info(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.delete()

 
@dp.callback_query_handler(text="back_to_posts", state=Form.content)
async def process_channel_info(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await state.finish()
    description = (
        "<b>СТВОРЕННЯ ПОСТУ:</b>\n\n"
        "Ця функція дозволяє створити пост і розіслати його всім користувачам бота. "
        "Ви можете додати текст, фото, відео або документ, а також URL-кнопки для посилання на зовнішні ресурси. "
        "Після створення поста, ви зможете переглянути його і підтвердити розсилку.\n\n"
        "Кроки для створення поста:\n"
        "1. Надішліть текст, фото, відео або документ, який ви хочете розіслати.\n"
        "2. Додайте опис, якщо потрібно.\n"
        "3. Додайте URL-кнопки, якщо потрібно.\n"
        "4. Перегляньте пост і підтвердьте розсилку.\n\n"
        "Після підтвердження розсилки, пост буде відправлено всім користувачам бота."
    )
    await callback_query.message.edit_text(description, parse_mode='HTML', reply_markup=get_broadcast_keyboard())

    
@dp.callback_query_handler(Text(equals='cancel_publish'))
async def cancel_publish(callback_query: types.CallbackQuery):
    await callback_query.answer("Публікацію скасовано.", show_alert=True)
 
@dp.callback_query_handler(text="back_to")
async def process_channel_info(callback_query: types.CallbackQuery):
    await callback_query.message.delete()



def register_admin_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(process_channel_selection, lambda c: c.data == 'confirm_parcel')