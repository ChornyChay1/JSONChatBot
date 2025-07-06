import asyncio
import logging
from app import bot, dp
from handlers.start_handler import register_handlers as register_start
from handlers.text_handler import register_handlers as register_text
from handlers.callback_handler import register_handlers as register_callback
from handlers.photo_handler import register_handlers as register_photo

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Регистрация обработчиков
register_photo(dp)
register_start(dp)
register_text(dp)
register_callback(dp)

async def main():
    logger.info("Bot is starting...")  # Логирование при запуске бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
