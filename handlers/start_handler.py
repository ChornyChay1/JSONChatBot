from aiogram import Router, types
from aiogram.filters import Command
from db import save_state, load_state
from questions import ask_question

router = Router()

@router.message(Command("start"))
async def start_quiz(message: types.Message):
    user_id = message.from_user.id
    question_id, _ = await load_state(user_id)  
    await save_state(user_id, question_id, {})  
    await ask_question(user_id, question_id, message)

def register_handlers(dp):
    dp.include_router(router)
