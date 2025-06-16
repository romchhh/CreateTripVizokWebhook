import sqlite3
import datetime
from datetime import datetime, timedelta
import pytz

current_time = datetime.now()

conn = sqlite3.connect('data/data.db')
cursor = conn.cursor()


def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    return count

def get_active_users_count():
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL")
    count = cursor.fetchone()[0]
    return count

def get_all_user_ids():
    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids
