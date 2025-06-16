import sqlite3
import datetime
from datetime import datetime, timedelta
import pytz

tz_kiev = pytz.timezone('Europe/Kyiv')
current_time = datetime.now(tz_kiev)

conn = sqlite3.connect('data/data.db')
cursor = conn.cursor()

def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id NUMERIC,
            user_name TEXT,
            user_first_name TEXT,
            real_name TEXT,
            phone NUMERIC,
            lang TEXT DEFAULT 'uk',
            blocked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    
def create_users_search_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_search (
            id INTEGER PRIMARY KEY,
            user_id NUMERIC,
            search_date TEXT,
            wanted_date TEXT,
            search_stops TEXT,
            found INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    
    
def create_cars_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_cars (
            id INTEGER PRIMARY KEY,
            user_id NUMERIC,
            mark TEXT,
            number TEXT,
            photo_path TEXT
        )
    ''')
    conn.commit()  
    
def create_trips_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            car_mark TEXT NOT NULL,
            car_number TEXT NOT NULL,
            seats INTEGER NOT NULL,
            stops TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(car_id) REFERENCES users_cars(id)
        );  
    ''')
    conn.commit()
    

    
def create_reviews_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            receiver_id NUMERIC,
            sender_id NUMERIC,
            stars INTEGER,
            text TEXT,
            date TEXT
        )
    ''')
    conn.commit() 

    
def add_user(user_id, user_name, user_first_name):
    cursor.execute("SELECT user_name FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is None:
        # Додати нового користувача, якщо його немає в базі
        join_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(''' 
            INSERT INTO users (user_id, user_name, user_first_name, real_name, date_joined)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, user_name, user_first_name, user_first_name, join_date))
        conn.commit()
    else:
        # Оновити user_name, якщо він відрізняється або відсутній
        current_user_name = existing_user[0]
        if current_user_name != user_name or not current_user_name:
            cursor.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (user_name, user_id))
            conn.commit()

 
        
def check_user(user_id):
    cursor.execute(f'SELECT * FROM Users WHERE user_id = {user_id}')
    user = cursor.fetchone()
    if user:
        return True
    return False
    
def check_phone_number(user_id):
    cursor.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if user and user[0]: 
        return True
    return False

def update_user_phone(user_id, phone_number):
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone_number, user_id))
    conn.commit()
    
def get_user_phone(user_id):
    cursor.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
    phone = cursor.fetchone()
    return phone if phone else None


def check_user_language(user_id):
    cursor.execute('SELECT lang FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None
    
    
def update_user_language(user_id, lang):
    cursor.execute('''
        UPDATE users
        SET lang = ?
        WHERE user_id = ?
    ''', (lang, user_id))
    conn.commit()
    
def update_trip_date(trip_id: int, new_date: datetime.date):
    cursor.execute(
        "UPDATE trips SET date = ? WHERE id = ?",
        (new_date.strftime("%Y-%m-%d"), trip_id)
    )
    conn.commit()
    
def update_trip_time(trip_id: int, new_time: str):
    cursor.execute(
        "UPDATE trips SET time = ? WHERE id = ?",
        (new_time, trip_id)
    )
    conn.commit()
    
def update_trip_stops(trip_id: int, new_stops: str):
    cursor.execute(
        "UPDATE trips SET stops = ? WHERE id = ?",
        (new_stops, trip_id)
    )
    conn.commit()
    
def get_driver_info(driver_user_id):
    query = '''
        SELECT u.user_name, u.real_name, u.phone, u.phone2, u.photo, u.lang
        FROM users u
        WHERE u.user_id = ?
    '''
    cursor.execute(query, (driver_user_id,))
    return cursor.fetchone()


def get_driver_trips(driver_user_id):
    query = '''
        SELECT COUNT(DISTINCT t.id) 
        FROM trips t
        WHERE t.user_id = ?
    '''
    cursor.execute(query, (driver_user_id,))
    return cursor.fetchone()[0]

def get_driver_reviews(driver_user_id):
    query = '''
        SELECT AVG(r.stars), COUNT(DISTINCT r.id)
        FROM reviews r
        WHERE r.receiver_id = ?
    '''
    cursor.execute(query, (driver_user_id,))
    return cursor.fetchone()  # Повертаємо середній рейтинг і кількість відгуків


def get_driver_reviews_text(driver_user_id):
    query = """
        SELECT stars, text, date 
        FROM reviews 
        WHERE receiver_id = ?
        ORDER BY date DESC
    """
    cursor.execute(query, (driver_user_id,))
    reviews = cursor.fetchall()

    return reviews


def find_user_by_username_or_phone(query: str):
    # Якщо це номер телефону (містить тільки цифри, можливо з "+")
    if query.replace("+", "").isdigit():
        # Створюємо обидва варіанти номера (з "+" і без)
        clean_number = query.replace("+", "")
        with_plus = "+" + clean_number
        # Шукаємо за обома варіантами
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE user_name = ? 
            OR phone IN (?, ?) 
            OR phone2 IN (?, ?)
        """, (query, clean_number, with_plus, clean_number, with_plus))
    else:
        # Якщо це не номер телефону, шукаємо тільки за username
        cursor.execute("SELECT user_id FROM users WHERE user_name = ?", (query,))
    
    user = cursor.fetchone()
    return user[0] if user else None

def find_username_by_id(user_id):
    cursor.execute("SELECT user_name FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        return user[0]  # Return only the user_id (first element of the tuple)
    else:
        return None  # If no user is found, return None

def create_referral_links_table():
    cursor.execute('''CREATE TABLE IF NOT EXISTS referral_links
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     platform TEXT NOT NULL,
                     name TEXT NOT NULL,
                     code TEXT UNIQUE NOT NULL,
                     clicks INTEGER DEFAULT 0)''')
    conn.commit()

def add_initial_referral_links():
    links = [
        ('Instagram', 'Пост в сторіс', 'inst_story'),
        ('Instagram', 'Пост в стрічці', 'inst_post'),
        ('Facebook', 'Реклама', 'fb_ads'),
        ('Facebook', 'Органічний пост', 'fb_post'),
        ('TikTok', 'Відео реклама', 'tt_video'),
        ('TikTok', 'Органічний пост', 'tt_post'),
        ('Viber', 'Пост в групі', 'viber_group'),
        ('Viber', 'Пост в особистій перепискі', 'viber_chat'),
        ('Telegram', 'Пост в групі', 'telegram_group'),
        ('Telegram', 'Пост в особистій перепискі', 'telegram_chat'),
        ('YouTube', 'Відео реклама', 'yt_video'),
        ('YouTube', 'Органічний пост', 'yt_post')
    ]
    
    cursor.execute('SELECT COUNT(*) FROM referral_links')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO referral_links (platform, name, code) VALUES (?, ?, ?)', links)
        conn.commit()

def update_referral_clicks(ref_code):
    cursor.execute('UPDATE referral_links SET clicks = clicks + 1 WHERE code = ?', (ref_code,))
    conn.commit()

async def get_trip_by_id(trip_id: int):
    cursor.execute("""
        SELECT id, user_id, car_id, date, time, car_mark, car_number, seats, stops, created_at, watched
        FROM trips 
        WHERE id = ?
    """, (trip_id,))
    return cursor.fetchone()


def update_user_username(user_id, user_name):
    cursor.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (user_name, user_id))
    conn.commit()