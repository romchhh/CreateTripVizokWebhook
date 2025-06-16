from googletrans import Translator
from functools import lru_cache
from database.client_db import check_user_language
import re

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

translator = Translator()
HTML_TAGS = ['code', 'b', 'i', 'u', 'strong', 'em', 'a', 'br']

# Функція для видалення HTML тегів
def remove_html_tags(text):
    # Регулярний вираз для пошуку всіх HTML тегів
    tag_pattern = re.compile(r'<(/?)(\w+)[^>]*?>')
    
    # Заміняємо теги на порожній рядок, якщо це один з вказаних тегів
    def remove_tag(match):
        tag = match.group(2).lower()
        if tag in HTML_TAGS:
            return ''  # Видаляємо тег
        return match.group(0)  # Якщо тег не в списку, залишаємо як є
    
    # Видаляємо теги
    return re.sub(tag_pattern, remove_tag, text)

# Оновлений кешований переклад
@lru_cache(maxsize=1000)
def translate_cached(text, dest_language):
    try:
        # Видаляємо HTML теги з тексту перед перекладом
        cleaned_text = remove_html_tags(text)
        
        # Перекладаємо очищений текст
        result = translator.translate(cleaned_text, dest=dest_language)
        
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate(text, user_id):
    user_language = check_user_language(user_id)

    if user_language == 'uk' or user_language is None:
        return text

    if user_language not in SUPPORTED_LANGUAGES:
        return text

    return translate_cached(text, user_language)

# Функція для отримання перекладів міста з урахуванням тегів
def get_city_translations(city):
    translations = {city.lower()}
    for lang in SUPPORTED_LANGUAGES.keys():
        try:
            translated = translator.translate(city, dest=lang).text.lower()
            translations.add(translated)
        except Exception as e:
            print(f"Error translating city {city} to {lang}: {e}")
    return translations

def get_user_lang(user_id):
    """
    Отримує мову користувача. Якщо мова не встановлена або не підтримується,
    повертає 'uk' (українська) як мову за замовчуванням.
    """
    user_language = check_user_language(user_id)
    if user_language is None or user_language not in SUPPORTED_LANGUAGES:
        return 'uk'
    return user_language