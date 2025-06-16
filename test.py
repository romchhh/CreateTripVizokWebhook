import sqlite3
from datetime import datetime, timedelta
import random

# Шлях до бази даних
data = "data/data.db"

# Списки для генерації випадкових даних
first_names = [
    # Українські імена
    "Олександр", "Максим", "Дмитро", "Андрій", "Іван", "Михайло", "Павло", "Богдан", "Василь", "Віктор",
    "Владислав", "Володимир", "Денис", "Євген", "Ігор", "Костянтин", "Леонід", "Микита", "Назар", "Олег",
    "Петро", "Роман", "Сергій", "Степан", "Тарас", "Юрій", "Ярослав",
    "Анна", "Марія", "Олена", "Софія", "Юлія", "Катерина", "Вікторія", "Алла", "Валентина", "Галина",
    "Дарина", "Євгенія", "Жанна", "Зоряна", "Ірина", "Людмила", "Наталія", "Оксана", "Поліна", "Руслана",
    "Світлана", "Тетяна", "Уляна", "Христина", "Яна",
    
    # Польські імена
    "Jan", "Piotr", "Adam", "Paweł", "Marcin", "Michał", "Stanisław", "Tomasz", "Andrzej", "Krzysztof",
    "Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Ewa", "Krystyna", "Magdalena",
    
    # Англійські імена
    "John", "Michael", "William", "David", "Richard", "Thomas", "Robert", "James", "Charles", "Daniel",
    "Sarah", "Emma", "Emily", "Jessica", "Laura", "Sophie", "Charlotte", "Lucy", "Hannah", "Elizabeth",
    
    # Німецькі імена
    "Hans", "Klaus", "Wolfgang", "Peter", "Martin", "Andreas", "Stefan", "Thomas", "Michael", "Frank",
    "Emma", "Hannah", "Julia", "Sophie", "Marie", "Lisa", "Sarah", "Anna", "Lea", "Lena",
    
    # Чеські імена
    "Pavel", "Jan", "Martin", "Tomáš", "Jiří", "Josef", "Petr", "Jaroslav", "Milan", "Karel",
    "Jana", "Eva", "Hana", "Anna", "Marie", "Lenka", "Kateřina", "Lucie", "Věra", "Alena"
]

usernames = [
    # Транспортні теми
    "rider", "traveler", "journey", "road", "driver", "passenger", "way", "path", "route", "track",
    "voyage", "trip", "travel", "move", "go", "wanderer", "explorer", "pathfinder", "navigator",
    "roadrunner", "wayfarer", "cruiser", "pilot", "captain", "guide", "rover", "transit", "voyager",
    
    # Автомобільні теми
    "cardriver", "automate", "wheelman", "motorist", "chauffeur", "trucker", "cabbie", "speedster",
    "racer", "pilot", "wheeler", "driver", "roadmaster", "carpilot", "autofan",
    
    # Українські варіанти
    "vodiy", "dorozhnyk", "mandrivnyk", "podorozh", "shlyakh", "kolisnyk", "pereviz", "rukh",
    "avto", "kermo", "doroga", "marsh", "trasa", "reis", "poizdka",
    
    # Комбіновані
    "roadhero", "travelmaster", "pathmaker", "routeking", "roadwarrior", "travelstar", "journeyace",
    "roadexpert", "travelguru", "pathpro", "routemaster", "roadrunner", "travelexpert", "journeyking",
    
    # Професійні
    "taxidriver", "busdriver", "truckdriver", "deliveryace", "transportpro", "logisticspro",
    "shipper", "carrier", "transporter", "dispatcher", "operator", "controller"
]

# Функція для генерації випадкового номера телефону
def generate_phone():
    # Українські оператори
    operators = {
        # Київстар
        "67": "067",  # Старий формат
        "96": "096",  # Старий формат
        "97": "097",  # Старий формат
        "98": "098",  # Старий формат
        "68": "068",  # Новий формат
        # Vodafone
        "50": "050",  # Старий формат
        "66": "066",  # Старий формат
        "95": "095",  # Старий формат
        "99": "099",  # Старий формат
        # Lifecell
        "63": "063",  # Старий формат
        "93": "093",  # Старий формат
        "73": "073",  # Новий формат
        # Інші оператори
        "91": "091",  # Utel
        "92": "092",  # PeopleNet
        "94": "094",  # Інтертелеком
    }
    
    operator = random.choice(list(operators.values()))
    number = str(random.randint(1000000, 9999999))  # 7 цифр
    
    # 50% шанс отримати номер з +380, 50% шанс отримати номер без +380
    if random.random() < 0.5:
        return f"+380{operator}{number}"
    else:
        return f"0{operator}{number}"

# Функція для генерації випадкового username
def generate_username():
    prefix = random.choice(usernames)
    suffix = random.choice([
        str(random.randint(100, 999)),
        random.choice(["_pro", "_expert", "_ace", "_master", "_king", "_star", "_hero", "_guru"]) + str(random.randint(10, 99)),
        "_" + str(random.randint(1980, 2005)),
        random.choice([".", "_", "-"]) + str(random.randint(10, 99))
    ])
    return f"{prefix}{suffix}"

# Мови, які підтримує бот
languages = ["uk", "pl", "en", "de", "cs", "bg", "ro", "hu", "it", "es"]

# Підключення до бази даних
conn = sqlite3.connect(data)
cursor = conn.cursor()

# Створення таблиці (якщо вона ще не існує)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    user_id NUMERIC,
    user_name TEXT,
    user_first_name TEXT,
    real_name TEXT,
    phone TEXT,
    phone2 TEXT,
    lang TEXT DEFAULT 'uk',
    blocked INTEGER DEFAULT 0,
    date_joined TEXT,
    photo TEXT
)
''')

# Генерація та вставка тестових даних
start_date = datetime(2025, 4, 20)
end_date = datetime(2025, 5, 4)
date_range = (end_date - start_date).days

for i in range(110):
    user_id = random.randint(100000000, 999999999)
    user_name = generate_username()
    first_name = random.choice(first_names)
    real_name = first_name
    phone = generate_phone()
    phone2 = generate_phone() if random.random() < 0.3 else None  # 30% користувачів мають другий телефон
    lang = random.choice(languages)
    blocked = 1 if random.random() < 0.05 else 0  # 5% заблокованих користувачів
    random_days = random.randint(0, date_range)
    date_joined = (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')
    photo = f"photos/user_{i}.jpg" if random.random() < 0.7 else None  # 70% користувачів мають фото

    cursor.execute('''
    INSERT INTO users (user_id, user_name, user_first_name, real_name, phone, phone2, lang, blocked, date_joined, photo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, first_name, real_name, phone, phone2, lang, blocked, date_joined, photo))

# Збереження змін та закриття з'єднання
conn.commit()
conn.close()

print("Тестові дані успішно додано до бази даних!")

