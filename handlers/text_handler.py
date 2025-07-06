import random
from aiogram import Router, types
from db import save_state, load_state
from questions import QUESTIONS, ask_question
from aiogram.types import ReplyKeyboardRemove
from app import bot  # Отложенный импорт
from config import END_PHRASES, CORRECT_ANSWER_PHRASES, INCORRECT_ANSWER_PHRASES, INVALID_OPTION_PHRASES, BRANCH_SELECTED_PHRASES
from db import AsyncSessionLocal
from db import UserState
from sqlalchemy.future import select

router = Router()

 
@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    question_id, _ = await load_state(user_id)   

    question = QUESTIONS.get(question_id)   
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserState).filter(UserState.user_id == user_id))
        state = result.scalars().first()
    if not state:
        await ask_question(user_id, "1", message)

    if question.type == "end":
        response = random.choice(END_PHRASES)
        await bot.send_message(message.chat.id, response)
        return
    if question.branching:
        await handle_text_branch_question(user_id, question_id, message)
    else:
        if question:
            await handle_text_question(user_id, question_id, message)

async def handle_text_question(user_id, question_id, message: types.Message):
    question = QUESTIONS[question_id]
    user_answer = message.text

    if user_answer == question.correct_answer:
        response = random.choice(CORRECT_ANSWER_PHRASES)
        correct = True
    else:
        response = random.choice(INCORRECT_ANSWER_PHRASES)
        correct = False

    markup = ReplyKeyboardRemove()

    await message.answer(response, reply_markup=markup)

    next_id = question.next_id
    await save_state(user_id, next_id, {"last_correct": correct})  # Добавлено await

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, message)
    else:
        await message.answer("Тест завершен! Спасибо за участие.")

async def handle_text_branch_question(user_id, question_id, message: types.Message):
    question = QUESTIONS[question_id]
    user_answer = message.text

    if question.options and user_answer not in question.options:
        response = random.choice(INVALID_OPTION_PHRASES)
        await message.answer(response)
        await ask_question(message.from_user, question_id=question_id, message=message) 
        return
    elif not question.options and user_answer not in question.branches:
        response = random.choice(INVALID_OPTION_PHRASES)
        await message.answer(response)
        await ask_question(message.from_user, question_id=question_id, message=message)
        return

    response = random.choice(BRANCH_SELECTED_PHRASES)

    markup = ReplyKeyboardRemove()
    await message.answer(response, reply_markup=markup)

    next_id = question.branches[user_answer]
    await save_state(user_id, next_id)  

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, message)
    else:
        await message.answer("Тест завершен! Спасибо за участие.")

def register_handlers(dp):
    dp.include_router(router)
