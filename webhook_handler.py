#!/usr/bin/env python3
"""
FastAPI webhook сервер для обробки даних з веб-додатка GitHub Pages
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VizokBot WebHook Server", version="1.0.0")

# Додаємо CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production краще вказати конкретні домени
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зберігання даних поїздок
trips_storage: Dict[str, Dict[str, Any]] = {}

class TripData(BaseModel):
    user_id: str
    route: str
    lang: str = "uk"
    timestamp: Optional[str] = None

@app.post("/webhook")
async def receive_webhook(trip_data: TripData):
    """Отримує дані поїздки з веб-додатка"""
    try:
        user_id = str(trip_data.user_id)
        
        # Додаємо timestamp якщо його немає
        if not trip_data.timestamp:
            trip_data.timestamp = datetime.now().isoformat()
        
        # Зберігаємо дані
        trips_storage[user_id] = {
            "user_id": user_id,
            "route": trip_data.route,
            "lang": trip_data.lang,
            "timestamp": trip_data.timestamp,
            "processed": False
        }
        
        logger.info(f"📨 Received trip data for user {user_id}: {trip_data.route}")
        
        return {
            "status": "success",
            "message": "Trip data received successfully",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_trips")
async def get_trips():
    """Повертає всі необроблені поїздки"""
    try:
        unprocessed_trips = []
        
        for user_id, trip_data in trips_storage.items():
            if not trip_data.get("processed", False):
                unprocessed_trips.append(trip_data)
                # Позначаємо як оброблений
                trips_storage[user_id]["processed"] = True
        
        logger.info(f"📤 Returning {len(unprocessed_trips)} unprocessed trips")
        
        return {
            "status": "success",
            "trips": unprocessed_trips,
            "count": len(unprocessed_trips)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear_data/{user_id}")
async def clear_user_data(user_id: str):
    """Видаляє дані користувача"""
    try:
        if user_id in trips_storage:
            del trips_storage[user_id]
            logger.info(f"🗑️ Cleared data for user {user_id}")
        
        return {
            "status": "success",
            "message": f"Data cleared for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fallback_webhook")
async def fallback_webhook(user_id: str, route: str, lang: str = "uk"):
    """Fallback webhook через GET запит (для обходу Mixed Content)"""
    try:
        # Створюємо дані як при POST запиті
        trip_data = {
            "user_id": user_id,
            "route": route,
            "lang": lang,
            "timestamp": datetime.now().isoformat(),
            "processed": False
        }
        
        # Зберігаємо дані
        trips_storage[user_id] = trip_data
        
        logger.info(f"📨 Received fallback trip data for user {user_id}: {route}")
        
        # Повертаємо 1x1 піксель (щоб image.src працював)
        from fastapi.responses import Response
        
        # 1x1 transparent GIF
        gif_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
        
        return Response(content=gif_data, media_type="image/gif")
        
    except Exception as e:
        logger.error(f"❌ Error processing fallback webhook: {e}")
        # Навіть при помилці повертаємо картинку
        gif_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
        return Response(content=gif_data, media_type="image/gif")

@app.get("/health")
async def health_check():
    """Перевірка здоров'я сервера"""
    return {
        "status": "healthy",
        "users_count": len(trips_storage),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Корінь API"""
    return {
        "message": "VizokBot WebHook Server",
        "version": "1.0.0",
        "endpoints": {
            "POST /webhook": "Receive trip data",
            "GET /get_trips": "Get unprocessed trips",
            "DELETE /clear_data/{user_id}": "Clear user data",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    logger.info("🚀 Starting VizokBot WebHook Server")
    uvicorn.run(
        "webhook_handler:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    ) 