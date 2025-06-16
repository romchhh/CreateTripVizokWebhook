import asyncio
import aiohttp
from ulits.webhook_client import webhook_client
from handlers.create_trip_handlers import handle_webhook_data

async def check_webhook_data():
    """Перевіряє webhook дані кожні 2 секунди"""
    print("🔄 Запущено перевірку webhook даних")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{webhook_client.base_url}/get_trips") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for trip_data in data.get('trips', []):
                            await handle_webhook_data(trip_data)
                            
                            # Видаляємо оброблені дані з сервера
                            user_id = trip_data.get('user_id')
                            if user_id:
                                await session.delete(f"{webhook_client.base_url}/clear_data/{user_id}")
                                
        except Exception as e:
            print(f"❌ Помилка при перевірці webhook даних: {e}")
            
        await asyncio.sleep(2)

def start_webhook_checker():
    """Запускає перевірку webhook даних"""
    print("🚀 Ініціалізація webhook checker")
    asyncio.create_task(check_webhook_data()) 