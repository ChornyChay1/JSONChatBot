from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from secret import API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
