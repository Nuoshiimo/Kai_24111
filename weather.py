import aiohttp
import aiohttp

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherError(Exception):
    """Понятная пользователю ошибка"""


async def get_weather(
    api_key: str,
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    params = {
        "appid": api_key,
        "units": "metric",  # градусы Цельсия
        "lang": "ru",       # описание погоды на русском
    }

    if city:
        params["q"] = city
    elif lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        raise ValueError("Нужно передать либо city, либо lat и lon")

    async with aiohttp.ClientSession() as session:
        async with session.get(OWM_URL, params=params) as response:
            if response.status == 404:
                raise WeatherError("Не нашёл такой город. Проверь название и попробуй ещё раз.")
            if response.status == 401:
                raise WeatherError("Неверный API-ключ погодного сервиса.")
            if response.status != 200:
                raise WeatherError("Сервис погоды временно недоступен.")

            return await response.json()