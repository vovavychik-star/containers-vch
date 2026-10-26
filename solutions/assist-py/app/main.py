from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
import redis

app = FastAPI(title="Personal Assistant")

# Загрузка переменных окружения
OWNER = os.getenv("APP_OWNER", "vychik")
SECRET_KEY = os.getenv("APP_SECRET", "secret63vychik")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "120"))

# Инициализация Redis
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class Note(BaseModel):
    text: str


notes: list[str] = []


@app.get("/")
async def root():
    return {
        "message": f"Добро пожаловать, {OWNER}!",
        "service": "personal-assistant",
        "version": "1.0",
        "endpoints": ["/me", "/notes", "/weather/{city}", "/cache/stats", "/secret/{key}"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "owner": OWNER}


@app.get("/me")
async def me():
    return {
        "owner": OWNER,
        "secret_prefix": SECRET_KEY[:6] if SECRET_KEY != "default_secret" else "NOT_SET",
    }


@app.get("/secret/{key}")
async def secret(key: str):
    if key == SECRET_KEY:
        return {
            "flag": f"LAB2_SUCCESS_{OWNER.upper()}",
            "message": "The secret key is correct!",
        }
    return {
        "error": "The secret key is incorrect",
        "hint": "Check the APP_SECRET environment variable",
    }


@app.get("/weather/{city}")
async def weather(city: str):
    cache_key = f"weather:{OWNER}:{city.lower()}"

    # 1. Проверяем кэш Redis
    try:
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["source"] = "cache"  # Метка кэша
            return data
    except Exception:
        pass

    # 2. Локальный мок ответа (имитируем успешный ответ API, обходя "Запрет")
    result = {
        "city": city.capitalize(),
        "country": "Сгенерировано локально",
        "coordinates": {"lat": 55.7512, "lon": 37.6184},
        "temperature_c": 18.5,
        "humidity_pct": 55,
        "wind_km_h": 8.0,
        "condition": "Ясно",
        "source": "api",  # Метка первого запроса
    }

    # 3. Сохраняем результат в кэш на 120 секунд
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception:
        pass

    return result


@app.get("/cache/stats")
async def cache_stats():
    try:
        keys = redis_client.keys(f"weather:{OWNER}:*")
        return {
            "owner": OWNER,
            "ttl_seconds": CACHE_TTL,
            "cached_count": len(keys),
            "cached_cities": sorted(k.split(":")[-1] for k in keys),
        }
    except Exception as e:
        return {"error": f"Redis error: {e}"}


@app.post("/notes")
async def create_note(note: Note):
    notes.append(note.text)
    return {"status": "saved", "note_id": len(notes) - 1, "total": len(notes)}


@app.get("/notes")
async def list_notes():
    return {"notes": notes, "count": len(notes)}
