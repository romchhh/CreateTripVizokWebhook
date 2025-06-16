# 🌍 VizokBot WebApp - Багатомовний веб-додаток для створення маршрутів

Цей веб-додаток є частиною екосистеми **VizokBot** - Telegram бота для організації спільних поїздок. Додаток дозволяє користувачам створювати маршрути поїздок через зручний веб-інтерфейс.

## 🚀 Демо

**Живий демо:** https://romchhh.github.io/CreateTripVizokWebhook/docs/

## ✨ Функціональність

- 🌐 **10 мов підтримки**: Українська, Польська, Англійська, Німецька, Чеська, Болгарська, Румунська, Угорська, Італійська, Іспанська, Російська
- 🔍 **Розумний пошук міст** через кілька API:
  - GeoNames API (основний)
  - Nominatim OpenStreetMap API (резервний)
  - REST Countries API (столиці)
- ➕ **Ручне додавання міст** якщо автопошук не знайшов результатів
- 🗺️ **Візуальне відображення маршруту** з номерами зупинок
- 🌍 **Показ країни** для кожної зупинки
- 📱 **Telegram WebApp API** інтеграція
- 🔗 **Вебхук система** для передачі даних до бота

## 🛠️ Технології

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **API Integration**: Multiple REST APIs для пошуку міст
- **Telegram**: WebApp API для інтеграції з ботом
- **Deployment**: GitHub Pages

## 📖 Як використовувати

### Параметри URL

| Параметр | Опис | Приклад |
|----------|------|---------|
| `lang` | Мова інтерфейсу | `uk`, `en`, `de`, `pl`, `cs`, `bg`, `ro`, `hu`, `it`, `es`, `ru` |
| `user_id` | ID користувача Telegram | `123456789` |
| `create` | Тип дії | `trip` або `search` |
| `webhook_url` | URL для відправки даних | `https://your-server.com/webhook` |

### Приклад посилання

```
https://romchhh.github.io/CreateTripVizokWebhook/docs/?lang=uk&user_id=123456&create=trip&webhook_url=https://your-webhook.com/webhook
```

## 🌐 Підтримувані мови

- 🇺🇦 **Українська** (`uk`) - Повна локалізація
- 🇵🇱 **Польська** (`pl`) - Polski
- 🇬🇧 **Англійська** (`en`) - English
- 🇩🇪 **Німецька** (`de`) - Deutsch
- 🇨🇿 **Чеська** (`cs`) - Čeština
- 🇧🇬 **Болгарська** (`bg`) - Български
- 🇷🇴 **Румунська** (`ro`) - Română
- 🇭🇺 **Угорська** (`hu`) - Magyar
- 🇮🇹 **Італійська** (`it`) - Italiano
- 🇪🇸 **Іспанська** (`es`) - Español
- 🇷🇺 **Російська** (`ru`) - Русский

## 🔧 Локальна розробка

1. Клонуйте репозиторій:
```bash
git clone https://github.com/romchhh/CreateTripVizokWebhook.git
cd CreateTripVizokWebhook
```

2. Запустіть локальний сервер:
```bash
python -m http.server 8000
```

3. Відкрийте браузер:
```
http://localhost:8000/docs/?lang=uk&user_id=123&create=trip&webhook_url=http://localhost:8001/webhook
```

## 📱 Інтеграція з Telegram ботом

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def create_webapp_keyboard(user_id: int, user_lang: str, action: str = "trip"):
    webapp_url = f"https://romchhh.github.io/CreateTripVizokWebhook/docs/?lang={user_lang}&user_id={user_id}&create={action}&webhook_url=https://your-webhook.com/webhook"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗺️ Створити маршрут",
            web_app=WebAppInfo(url=webapp_url)
        )]
    ])
    return keyboard
```

## 🔗 Пов'язані проєкти

- **VizokBot** - Головний Telegram бот для спільних поїздок
- **Webhook Handler** - Сервер для обробки даних з веб-додатка

## 📄 Ліцензія

MIT License

## 👥 Автори

- **romchhh** - Розробка та підтримка

---

**🤖 Частина екосистеми VizokBot - зробимо подорожі зручнішими разом!** 