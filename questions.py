import json
from secret import APPROVAL_CHAT_ID
from models import Question
from pydantic import ValidationError
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app import bot
from aiogram.types import ReplyKeyboardRemove

try:
    with open("questions.json", "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    QUESTIONS = {}
    for qid, q in raw_data.items():
        try:
            QUESTIONS[qid] = Question(**q)
        except ValidationError as ve:
            print(f"Validation error for question ID {qid}: {ve}")
except FileNotFoundError:
    print("Error: 'questions.json' not found.")
    QUESTIONS = {}
except json.JSONDecodeError as je:
    print(f"JSON parsing error: {je}")
    QUESTIONS = {}
except Exception as e:
    print(f"Unexpected error loading questions: {e}")
    QUESTIONS = {}

if not QUESTIONS:
    print("Warning: Question list is empty.")


async def ask_question(user_id, question_id, message):
    if message.chat.id == APPROVAL_CHAT_ID:
        return
    question = QUESTIONS[question_id]
    if question.addictional_images:
            media_group = []
            for img_path in question.addictional_images:
                try:
                    media_group.append(types.InputMediaPhoto(media=types.FSInputFile(img_path)))
                except Exception as e:
                    print(f"Ошибка загрузки изображения {img_path}: {e}")

            if media_group:
                await bot.send_media_group(message.chat.id, media=media_group)
    if question.type == "photo":
            await bot.send_message(message.chat.id, text="Пришли фото в этом месте!", reply_markup=markup)


    if question.type == "text":
        
        options = question.options
        if options:
            markup = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=opt)] for opt in options],
                resize_keyboard=True
            )
        else:
            markup = ReplyKeyboardMarkup(
                keyboard=[],
                resize_keyboard=True
            )
        await bot.send_message(message.chat.id, question.question, reply_markup=markup)

    elif question.type == "audio":
        try:
            audio = types.FSInputFile(question.audio_file)
            inlineKeyboardButtons = []
            for opt in question.options:
                inlineKeyboardButtons.append(InlineKeyboardButton(text=opt, callback_data=opt))
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [button] for button in inlineKeyboardButtons 
                ]
            )
            if question.question!= "":
                await bot.send_message(chat_id= message.chat.id,text=question.question)
            await bot.send_audio(message.chat.id, audio, reply_markup=markup)
        except Exception as e:
            await bot.send_message(message.chat.id, f"Ошибка при отправке аудио: {e}")

    elif question.type == "video":
        video = types.FSInputFile(question.video_file)
        inlineKeyboardButtons = []
        for opt in question.options:
            inlineKeyboardButtons.append(InlineKeyboardButton(text=opt, callback_data=opt))
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [button] for button in inlineKeyboardButtons  
            ]
        )
        if markup.inline_keyboard:  
            await bot.send_video(message.chat.id, video, caption=question.question, reply_markup=markup)
        else:
            await bot.send_video(message.chat.id, video, caption=question.question)

    elif question.type == "image":
        image = types.FSInputFile(question.image_file)
        inlineKeyboardButtons = []

        for opt in question.options:
            inlineKeyboardButtons.append(InlineKeyboardButton(text=opt, callback_data=opt))

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [button] for button in inlineKeyboardButtons 
            ]
        )
        if markup.inline_keyboard:
            await bot.send_photo(message.chat.id, image, caption=question.question, reply_markup=markup)
        else:
            await bot.send_photo(message.chat.id, image, caption=question.question)

    elif question.type == "video_note":
        video = types.FSInputFile(question.video_file)
        inlineKeyboardButtons = []
        for opt in question.options:
            inlineKeyboardButtons.append(InlineKeyboardButton(text=opt, callback_data=opt))
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [button] for button in inlineKeyboardButtons 
            ]
        )
        if markup.inline_keyboard: 
            await bot.send_video_note(message.chat.id, video, reply_markup=markup)
        else:
            await bot.send_video_note(message.chat.id, video)
            await bot.send_message(message.chat.id, text=question.question)


    elif question.type == "end":
        await bot.send_message(message.chat.id, question.question)
