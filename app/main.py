from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.game.router import router as game_router 

import logging
from contextlib import asynccontextmanager
from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.router import router as bot_router
from app.config import settings
from app.game.router import router as game_router
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update
from fastapi import FastAPI, Request

"""Строка app.mount('/static', StaticFiles(directory='app/static'), 'static') настраивает маршрут /static 
для доступа к статическим файлам.

Строка app.include_router(game_router) подключает маршруты из game_router 
в основное приложение, организуя логику игры в отдельном модуле.
"""

app = FastAPI()


app.mount('/static', StaticFiles(directory='app/static'), 'static')
app.include_router(game_router)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

"""
Жизненный цикл работы с FastAPI
Логика работы с FastAPI предполагает использование механизма жизненного цикла (lifespan), который управляется через декоратор @asynccontextmanager в функции lifespan(app: FastAPI). Этот цикл делится на две основные части:

Запуск приложения (до yield): выполняется один раз при старте приложения. Здесь мы:

Подключаем роутер бота bot_router.

Вызываем функции, необходимые сразу после запуска бота.

Устанавливаем вебхук для получения обновлений от Telegram.

Остановка приложения (после yield): выполняется при завершении работы приложения. Здесь мы:

Удаляем вебхук.

Выполняем функции для корректного завершения работы бота и закрытия всех активных процессов.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting bot setup...")
    dp.include_router(bot_router)
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(url=webhook_url,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    logging.info(f"Webhook set to {webhook_url}")
    yield
    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logging.info("Webhook deleted")


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory='app/static'), 'static')

@app.post("/webhook")
async def webhook(request: Request) -> None:
    logging.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    logging.info("Update processed")

app.include_router(game_router)