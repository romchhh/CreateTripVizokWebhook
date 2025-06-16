"""
Клієнт для роботи з вебхук сервером
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class WebHookClient:
    def __init__(self, webhook_server_url: str = "http://localhost:8001"):
        """
        Ініціалізація клієнта для роботи з вебхук сервером
        
        Args:
            webhook_server_url: URL вебхук сервера (може бути IP або домен)
        """
        self.base_url = webhook_server_url.rstrip('/')
        
    async def get_cities_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Отримує міста для користувача з вебхук сервера
        
        Args:
            user_id: ID користувача
            
        Returns:
            Словник з містами або None якщо не знайдено
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/get_cities/{user_id}"
                
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "success":
                            logger.info(f"🔗 Got cities for user {user_id}: {data['data']['cities_string']}")
                            return data["data"]
                        else:
                            logger.debug(f"🔗 No cities found for user {user_id}")
                            return None
                    else:
                        logger.warning(f"🔗 Failed to get cities for user {user_id}: {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.warning(f"🔗 Timeout getting cities for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"🔗 Error getting cities for user {user_id}: {e}")
            return None
    
    async def clear_cities_for_user(self, user_id: str) -> bool:
        """
        Очищає дані користувача на вебхук сервері
        
        Args:
            user_id: ID користувача
            
        Returns:
            True якщо успішно очищено
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/clear_cities/{user_id}"
                
                async with session.delete(url, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"🔗 Cleared cities for user {user_id}")
                        return True
                    else:
                        logger.warning(f"🔗 Failed to clear cities for user {user_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"🔗 Error clearing cities for user {user_id}: {e}")
            return False
    
    async def check_health(self) -> bool:
        """
        Перевіряє здоров'я вебхук сервера
        
        Returns:
            True якщо сервер працює
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/health"
                
                async with session.get(url, timeout=3) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"🔗 WebHook server is healthy: {data.get('users_count', 0)} users")
                        return True
                    else:
                        logger.warning(f"🔗 WebHook server unhealthy: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"🔗 WebHook server check failed: {e}")
            return False

# Глобальний клієнт (буде ініціалізований в main.py)
webhook_client: Optional[WebHookClient] = None

def init_webhook_client(server_url: str = "http://localhost:8001"):
    """Ініціалізує глобальний вебхук клієнт"""
    global webhook_client
    webhook_client = WebHookClient(server_url)
    logger.info(f"🔗 WebHook client initialized for {server_url}")

async def get_user_cities_from_webhook(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Зручна функція для отримання міст користувача
    
    Args:
        user_id: ID користувача
        
    Returns:
        Словник з містами або None
    """
    if webhook_client:
        return await webhook_client.get_cities_for_user(str(user_id))
    else:
        logger.warning("🔗 WebHook client not initialized")
        return None

async def clear_user_cities_webhook(user_id: str) -> bool:
    """
    Зручна функція для очищення даних користувача
    
    Args:
        user_id: ID користувача
        
    Returns:
        True якщо успішно
    """
    if webhook_client:
        return await webhook_client.clear_cities_for_user(str(user_id))
    else:
        logger.warning("🔗 WebHook client not initialized")
        return False 