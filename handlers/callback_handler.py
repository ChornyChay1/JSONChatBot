import random
from email import message
from aiogram import Router, types, F
from db import save_state, load_state
from questions import QUESTIONS, ask_question
from aiogram.types import ReplyKeyboardRemove
from app import bot  
from config import END_PHRASES, CORRECT_ANSWER_PHRASES, INCORRECT_ANSWER_PHRASES, INVALID_OPTION_PHRASES, BRANCH_SELECTED_PHRASES, NOT_PHOTO_QUESTION_PHASES, PHOTO_APPROVED_PHRASES, PHOTO_REJECTED_PHRASES, NO_OPTION_PHRASES, SAME_ID_PHRASES

router = Router()


@router.callback_query(~(F.data.startswith("approve:") | F.data.startswith("reject:")))
async def handle_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    question_id, _ = await load_state(user_id)  

    question = QUESTIONS.get(question_id)
    if question.type == "end":
        response = random.choice(END_PHRASES)
        await bot.send_message(callback_query.message.chat.id, response)
        return

    if question.branching:
        await handle_media_branch_question(user_id, question_id, callback_query)
    else:
        if question:
            await handle_media_question(user_id, question_id, callback_query)


async def handle_media_question(user_id, question_id, callback_query: types.CallbackQuery):
    question = QUESTIONS[question_id]
    user_answer = callback_query.data

    if user_answer == question.correct_answer:
        response = "🎉 Верно! Отличная работа!"
        correct = True
    else:
        response = "❌ Неверно! Но не сдавайся!"
        correct = False

    if question.type == "text":
        markup = ReplyKeyboardRemove()
    else:
        markup = None

    await bot.send_message(callback_query.message.chat.id, response, reply_markup=markup)

    next_id = question.next_id
    await save_state(user_id, next_id, {"last_correct": correct})  # Добавлено await

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, callback_query.message)
    else:
        await bot.send_message(callback_query.message.chat.id, "🎄 Тест завершен! Спасибо за участие.")


async def handle_media_branch_question(user_id, question_id, callback_query: types.CallbackQuery):
    question = QUESTIONS[question_id]
    message = callback_query.data


    if message in question.options:
        response = f'Ты выбрал "{message}".'
    else:
        response = random.choice(NO_OPTION_PHRASES)
        await bot.send_message(callback_query.message.chat.id, response)
        await ask_question(callback_query.message.from_user, question_id=question_id, message=callback_query.message)
        return

    await bot.send_message(callback_query.message.chat.id, response)

    next_id = question.branches.get(message)
    if next_id is None:
  
        response = random.choice(NO_OPTION_PHRASES)
        await bot.send_message(callback_query.message.chat.id, response)
        await ask_question(callback_query.message.from_user, question_id=question_id, message=callback_query.message)
        return

    if next_id == question_id:
        response = random.choice(NO_OPTION_PHRASES)
        await bot.send_message(callback_query.message.chat.id,response)
        await ask_question(callback_query.message.from_user, question_id=question_id, message=callback_query.message)
        return

    await save_state(user_id, next_id) 

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, callback_query.message)
    else:
        await bot.send_message(callback_query.message.chat.id, "🎄 Тест завершен! Спасибо за участие.")


def register_handlers(dp):
    dp.include_router(router)
