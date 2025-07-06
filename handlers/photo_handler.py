import random
from aiogram import Router, types, F
from db import save_state, load_state
from questions import QUESTIONS, ask_question
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app import bot  
from secret import APPROVAL_CHAT_ID
from config import END_PHRASES, CORRECT_ANSWER_PHRASES, INCORRECT_ANSWER_PHRASES, INVALID_OPTION_PHRASES, BRANCH_SELECTED_PHRASES, NOT_PHOTO_QUESTION_PHASES, PHOTO_APPROVED_PHRASES, PHOTO_REJECTED_PHRASES

router = Router()


@router.message(F.content_type == types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    question_id, state = await load_state(user_id) 
    question = QUESTIONS.get(question_id)
    if question.type == "end":
        response = random.choice(END_PHRASES)
        await bot.send_message(message.chat.id, response)
        return
    if question.is_photo:
        approval_chat_id = APPROVAL_CHAT_ID
        photo_id = message.photo[-1].file_id  

        caption = f"Пользователь @{message.from_user.username} отправил фото для вопроса: {question.question}"
        approve_button = InlineKeyboardButton(text="Одобрить", callback_data=f"approve:{user_id}:{question_id}")
        reject_button = InlineKeyboardButton(text="Не одобрить", callback_data=f"reject:{user_id}:{question_id}")
        markup = InlineKeyboardMarkup(inline_keyboard=[[approve_button, reject_button]])

        await bot.send_photo(chat_id=approval_chat_id, photo=photo_id, caption=caption, reply_markup=markup)
        audio = types.FSInputFile(question.audio_file) 
        await bot.send_audio(user_id, audio)
    else: 
        response = random.choice(NOT_PHOTO_QUESTION_PHASES)
        await message.reply(response)
        await ask_question(message.from_user, question_id=question_id, message=message)  


@router.callback_query(F.data.startswith("approve:") | F.data.startswith("reject:"))
async def handle_approval(callback_query: types.CallbackQuery):
    data = callback_query.data.split(":")
    action, user_id, question_id = data[0], int(data[1]), data[2]
    user_id = int(user_id)
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    if action == "approve":
        response = random.choice(PHOTO_APPROVED_PHRASES)
        next_button = InlineKeyboardButton(text="Ура", callback_data=f"next:{user_id}")
        markup = InlineKeyboardMarkup(inline_keyboard=[[next_button]])

        await bot.send_message(chat_id=user_id, text=response, reply_markup=markup)

        next_id = QUESTIONS[question_id].next_id
        await save_state(user_id, next_id) 
    elif action == "reject":
        
        audio = types.FSInputFile("files/audio_7.m4a") 
        await bot.send_audio(chat_id=user_id,audio= audio)


@router.callback_query(F.data.startswith("next:"))
async def handle_next(callback_query: types.CallbackQuery):
    data = callback_query.data.split(":")
    user_id = int(data[1])
    question_id, _ = await load_state(user_id)  

    await ask_question(user_id, question_id, callback_query.message)

def register_handlers(dp):
    dp.include_router(router)
