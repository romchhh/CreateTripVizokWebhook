# 🌍 Приклади посилань для веб-додатка VizokBot

## 📱 Локальне тестування (HTTP сервер на localhost:8003)

### 🇺🇦 Українська мова
```
http://localhost:8003?lang=uk&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇵🇱 Польська мова
```
http://localhost:8003?lang=pl&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇬🇧 Англійська мова
```
http://localhost:8003?lang=en&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇩🇪 Німецька мова
```
http://localhost:8003?lang=de&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇨🇿 Чеська мова
```
http://localhost:8003?lang=cs&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇧🇬 Болгарська мова
```
http://localhost:8003?lang=bg&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇷🇴 Румунська мова
```
http://localhost:8003?lang=ro&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇭🇺 Угорська мова
```
http://localhost:8003?lang=hu&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇮🇹 Італійська мова
```
http://localhost:8003?lang=it&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇪🇸 Іспанська мова
```
http://localhost:8003?lang=es&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

### 🇷🇺 Російська мова
```
http://localhost:8003?lang=ru&user_id=123456&create=trip&webhook_url=http://localhost:8001/webhook
```

## 🌐 Продакшн (GitHub Pages + сервер на IP)

### 🇺🇦 Українська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=uk&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇵🇱 Польська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=pl&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇬🇧 Англійська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=en&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇩🇪 Німецька - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=de&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇨🇿 Чеська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=cs&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇧🇬 Болгарська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=bg&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇷🇴 Румунська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=ro&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇭🇺 Угорська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=hu&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇮🇹 Італійська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=it&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇪🇸 Іспанська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=es&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

### 🇷🇺 Російська - створення поїздки
```
https://YOUR_USERNAME.github.io/VizokBot?lang=ru&user_id=585621771&create=trip&webhook_url=http://194.104.23.37:8001/webhook
```

## 📝 Параметри URL

| Параметр | Опис | Значення |
|----------|------|----------|
| `lang` | Мова інтерфейсу | `uk`, `pl`, `en`, `de`, `cs`, `bg`, `ro`, `hu`, `it`, `es`, `ru` |
| `user_id` | ID користувача Telegram | Будь-яке число |
| `create` | Тип дії | `trip` (створення), `search` (пошук) |
| `webhook_url` | URL для вебхука | `http://194.104.23.37:8001/webhook` |

## 🧪 Тестування API міст

### GeoNames API
```
https://secure.geonames.org/searchJSON?q=Kyiv&maxRows=8&featureClass=P&username=demo&lang=uk
```

### Nominatim API
```
https://nominatim.openstreetmap.org/search?format=json&q=Kyiv&limit=10&addressdetails=1&accept-language=uk
```

### REST Countries API
```
https://restcountries.com/v3.1/name/Ukraine?fields=name,capital
```

## 🔧 Налаштування для Telegram бота

У коді бота використовуйте такий URL для WebApp:

```javascript
const webappUrl = `https://YOUR_USERNAME.github.io/VizokBot?lang=${userLang}&user_id=${userId}&create=trip&webhook_url=http://194.104.23.37:8001/webhook`;

const keyboard = InlineKeyboardMarkup();
keyboard.add(InlineKeyboardButton("🗺️ Додати маршрут", web_app=WebAppInfo(url=webappUrl)));
```

## 📋 Приклади тестування

1. **Спробуйте популярні міста:**
   - Київ, Львів, Одеса, Харків
   - London, Paris, Berlin, Rome  

2. **Спробуйте менш популярні:**
   - Житомир, Рівне, Тернопіль
   - Біла Церква, Бровари

3. **Спробуйте неіснуючі міста:**
   - МоєМісто123
   - TestCity
   - Вигадане місто

4. **Перевірте різні мови:**
   - Київ / Kyiv / Киев
   - Львів / Lviv / Львов 