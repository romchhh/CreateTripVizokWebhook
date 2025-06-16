import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from config import *
from ulits.webhook_client import init_webhook_client

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler(timezone='Europe/Kyiv')
scheduler.start()

# Ініціалізуємо вебхук клієнт
WEBHOOK_SERVER_URL = "http://139.59.208.152:8001"
init_webhook_client(WEBHOOK_SERVER_URL)

if __name__ == '__main__':
    from handlers.client_handlers import dp, on_startup, on_shutdown
    from handlers.admin_handlers import dp
    from handlers.create_trip_handlers import dp
    from handlers.search_trip_handlers import dp
    from handlers.my_profile_handlers import dp
    
    loop = asyncio.get_event_loop()
    executor.start_polling(dp, loop=loop, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)