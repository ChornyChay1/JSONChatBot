import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, ValidationError
import json
from aiogram.filters import Command
from secret import API_TOKEN,DATABASE_URL
 
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
 
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

class UserState(Base):
    __tablename__ = "user_states"

    user_id = Column(Integer, primary_key=True, index=True)
    current_question_id = Column(String, nullable=False)
    data = Column(JSON, nullable=True)

Base.metadata.create_all(bind=engine)

class Question(BaseModel):
    question: str
    type: str
    options: list[str] = []
    correct_answer: str | None = None
    next_id: str | None = None
    audio_file: str | None = None

try:
    with open("questions.json", "r",encoding="utf-8") as file:
        raw_data = json.load(file)

        QUESTIONS = {}
        for qid, q in raw_data.items():
            try:
                QUESTIONS[qid] = Question(**q)
            except ValidationError as ve:
                print(f"Ошибка валидации вопроса с ID {qid}: {ve}")
except FileNotFoundError:
    print("Ошибка: Файл 'questions.json' не найден. Проверьте, что файл существует в текущей директории.")
    QUESTIONS = {}
except json.JSONDecodeError as je:
    print(f"Ошибка разбора JSON-файла: {je}")
    QUESTIONS = {}
except Exception as e:
    print(f"Произошла непредвиденная ошибка при загрузке вопросов: {e}")
    QUESTIONS = {}

if not QUESTIONS:
    print("Внимание: список вопросов пуст. Проверьте корректность данных в файле 'questions.json'.") 

def save_state(user_id, question_id, data):
    state = session.query(UserState).filter(UserState.user_id == user_id).first()
    if state:
        state.current_question_id = question_id
        state.data = data
    else:
        state = UserState(user_id=user_id, current_question_id=question_id, data=data)
        session.add(state)
    session.commit()

def load_state(user_id):
    state = session.query(UserState).filter(UserState.user_id == user_id).first()
    if state:
        return state.current_question_id, state.data
    return "1", {}  # Начинаем с первого вопроса

async def handle_text_question(user_id, question_id, message: types.Message):
    question = QUESTIONS[question_id]
    user_answer = message.text

    if user_answer == question.correct_answer:
        response = "Верно!"
        correct = True
    else:
        response = "Неверно!"
        correct = False

    await message.answer(response)

    next_id = question.next_id
    save_state(user_id, next_id, {"last_correct": correct})

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, message)
    else:
        await message.answer("Тест завершен! Спасибо за участие.")

 

async def ask_question(user_id, question_id, message):
    question = QUESTIONS[question_id]

    if question.type == "text":
        options = question.options
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=opt)] for opt in options],
            resize_keyboard=True
        )
        await bot.send_message(message.chat.id, question.question, reply_markup=markup)

    elif question.type == "audio":
        audio = types.FSInputFile(question.audio_file)
        markup = InlineKeyboardMarkup()
        for opt in question.options:
            markup.add(InlineKeyboardButton(opt, callback_data=opt))
        await bot.send_audio(message.chat.id, audio, caption=question.question, reply_markup=markup)

    elif question.type == "video":
        video = types.FSInputFile(question.video_file)
        markup = InlineKeyboardMarkup()
        for opt in question.options:
            markup.add(InlineKeyboardButton(opt, callback_data=opt))
        await bot.send_video(message.chat.id, video, caption=question.question, reply_markup=markup)

    elif question.type == "video_note":
        video_note = types.FSInputFile(question.video_note_file)
        markup = InlineKeyboardMarkup()
        for opt in question.options:
            markup.add(InlineKeyboardButton(opt, callback_data=opt))
        await bot.send_video_note(message.chat.id, video_note)

    elif question.type == "end":
        await bot.send_message(message.chat.id, question.question)

@router.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    question_id, _ = load_state(user_id)

    question = QUESTIONS.get(question_id)
    if question:
        if question.type in ["audio", "video", "video_note"]:
            await handle_media_question(user_id, question_id, callback_query)

async def handle_media_question(user_id, question_id, callback_query: types.CallbackQuery):
    question = QUESTIONS[question_id]
    user_answer = callback_query.data

    if user_answer == question.correct_answer:
        response = "Верно!"
        correct = True
    else:
        response = "Неверно!"
        correct = False

    await bot.send_message(callback_query.message.chat.id, response)

    next_id = question.next_id
    save_state(user_id, next_id, {"last_correct": correct})

    if next_id in QUESTIONS:
        await ask_question(user_id, next_id, callback_query.message)
    else:
        await bot.send_message(callback_query.message.chat.id, "Тест завершен! Спасибо за участие.")


@router.message(Command("start"))
async def start_quiz(message: types.Message):
    user_id = message.from_user.id
    question_id, _ = load_state(user_id)

    save_state(user_id, question_id, {})
    await ask_question(user_id, question_id, message)

@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    question_id, _ = load_state(user_id)

    question = QUESTIONS.get(question_id)
    if question and question.type == "text":
        await handle_text_question(user_id, question_id, message)

@router.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    question_id, _ = load_state(user_id)

    question = QUESTIONS.get(question_id)
    if question and question.type == "audio":
        await handle_audio_question(user_id, question_id, callback_query)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
