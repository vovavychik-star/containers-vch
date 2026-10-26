from fastapi import FastAPI
from pydantic import BaseModel
import os
import httpx
import json
import redis

app = FastAPI(title="Personal Assistant")

#   
OWNER = os.getenv("APP_OWNER", "vychik")
SECRET_KEY = os.getenv("APP_SECRET", "secret63vychik")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "120"))

#  Redis (decode_responses=True     )
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class Note(BaseModel):
    text: str


notes: list[str] = []


@app.get("/")
async def root():
    return {
        "message": f" , {OWNER}!",
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
    """Secret endpoint - checking environment variables"""
    if key == SECRET_KEY:
        return {
            "flag": f"LAB2_SUCCESS_{OWNER.upper()}",
            "message": "The secret key is correct!",
        }
    return {
        "error": "The secret key is incorrect",
        "hint": "Check the APP_SECRET environment variable",
    }


WEATHER_CODES: dict[int, str] = {
    0: "", 1: " ", 2: " ",
    3: "", 45: "", 48: " ",
    51: " ", 53: " ", 55: " ",
    61: " ", 63: " ", 65: " ",
    71: " ", 73: " ", 75: " ",
    80: " ", 81: " ", 82: " ",
    95: "", 96: "   ", 99: "   ",
}


@app.get("/weather/{city}")
async def weather(city: str):
    try:
        #        
        cache_key = f"weather:{OWNER}:{city.lower()}"

        #   Redis
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["source"] = "cache"  # ,     
            return data

        async with httpx.AsyncClient(timeout=5.0) as client:
            geo_resp = await client.get(
                "https://open-meteo.com",
                params={"name": city, "count": 1, "language": "ru"},
            )
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return {"error": f"City '{city}' not found"}

            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location.get("name", city)
            country = location.get("country", "")

            weather_resp = await client.get(
                "https://open-meteo.com",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                },
            )
            weather_data = weather_resp.json()["current"]
            code = weather_data.get("weather_code", -1)

            result = {
                "city": city_name,
                "country": country,
                "coordinates": {"lat": lat, "lon": lon},
                "temperature_c": weather_data["temperature_2m"],
                "humidity_pct": weather_data["relative_humidity_2m"],
                "wind_km_h": weather_data["wind_speed_10m"],
                "condition": WEATHER_CODES.get(code, f"Code {code}"),
                "source": "api",  # ,      API
            }

            #       TTL (120 )
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
            return result

    except Exception as e:
        return {"error": f"Failed to get weather: {type(e).__name__}: {e}"}


@app.get("/cache/stats")
async def cache_stats():
    """    """
    keys = redis_client.keys(f"weather:{OWNER}:*")
    return {
        "owner": OWNER,
        "ttl_seconds": CACHE_TTL,
        "cached_count": len(keys),
        "cached_cities": sorted(k.split(":")[-1] for k in keys),
    }


@app.post("/notes")
async def create_note(note: Note):
    notes.append(note.text)
    return {"status": "saved", "note_id": len(notes) - 1, "total": len(notes)}


@app.get("/notes")
async def list_notes():
    return {"notes": notes, "count": len(notes)}

