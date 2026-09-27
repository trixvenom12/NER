import httpx
import datetime as dt

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

async def fetch_rain(points):
    """
    points: list of (id, lat, lon). Open-Meteo accepts comma lists.
    Sample the corridor every ~10 km rather than per road segment.
    Store each fetch in a weather_obs table with a timestamp.
    """
    params = {
        "latitude": ",".join(str(p[1]) for p in points),
        "longitude": ",".join(str(p[2]) for p in points),
        "hourly": "precipitation,visibility",
        "past_days": 3, 
        "forecast_days": 2, 
        "timezone": "Asia/Kolkata",
    }
    
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(OPEN_METEO, params=params)
        r.raise_for_status()
        return r.json()

# In a real setup, this would insert the results into the weather_obs table
