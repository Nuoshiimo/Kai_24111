import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

from weather import get_weather, WeatherError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWM_API_KEY = os.getenv("OWM_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

POPULAR_CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Казань"]

# функция для создания кнопок в боте
def main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=city)] for city in POPULAR_CITIES]
    buttons.append([KeyboardButton(text="Отправить геолокацию", request_location=True)])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# функция для запуска бота и для ответа на команду /start
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Бот прогноза погоды\n\n"
        "Напишите название города, чтобы получить прогноз погоду.\n"
        "Можете выбрать город из списка ниже или отправить геолокацию.",
        reply_markup=main_keyboard(),
    )

# функция для получения геолокации по широте и долготе
@router.message(F.location)
async def handle_location(message: Message) -> None:
    lat = message.location.latitude
    lon = message.location.longitude
    await send_weather_by_coords(message, lat, lon)

# функция для обработки сообщения пользователя
@router.message(F.text)
async def handle_city(message: Message) -> None:
    city = message.text.strip()
    await send_weather_by_city(message, city)

# функции для отправки прогноза погоды по выбранному городу
async def send_weather_by_city(message: Message, city: str) -> None:
    try:
        data = await get_weather(OWM_API_KEY, city=city)
        await message.answer(format_weather(data), reply_markup=main_keyboard())
    except WeatherError as e:
        await message.answer(f"{e}", reply_markup=main_keyboard())
    except Exception:
        logger.exception("Ошибка при обращению к сервису погоды")
        await message.answer(
            "Что-то пошло не так при обращении к сервису погоды. Попробуйте ещё раз.",
            reply_markup=main_keyboard(),
        )


async def send_weather_by_coords(message: Message, lat: float, lon: float) -> None:
    try:
        data = await get_weather(OWM_API_KEY, lat=lat, lon=lon)
        weather_text = format_weather(data, title="Погода по вашим координатам:")
        await message.answer(weather_text, reply_markup=main_keyboard())
    except WeatherError as e:
        await message.answer(f"{e}", reply_markup=main_keyboard())
    except Exception:
        logger.exception("Ошибка при обращению к сервису погоды")
        await message.answer(
            "Что-то пошло не так при обращении к сервису погоды. Попробуйте ещё раз.",
            reply_markup=main_keyboard(),
        )

# форматирование данных
def format_weather(data: dict, title: str | None = None) -> str:
    header = title or f"Погода в городе {data['name']}:"

    temp = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    wind_speed = data["wind"]["speed"]
    description = data["weather"][0]["description"].capitalize()

    return (
        f"{header}\n\n"
        f"Температура: {temp}°C\n"
        f"Ощущается как: {feels_like}°C\n"
        f"Ветер: {wind_speed} м/с\n"
        f"{description}"
    )


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")
    if not OWM_API_KEY:
        raise RuntimeError("OWM_API_KEY не задан")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())