from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import ValidationError
from models import Question
import json 
from secret import DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class UserState(Base):
    __tablename__ = "user_states"

    user_id = Column(Integer, primary_key=True, index=True)
    current_question_id = Column(String, nullable=False)
    data = Column(JSON, nullable=True)


async def save_state(user_id, question_id, data=None):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            state = await session.get(UserState, user_id)
            if state:
                state.current_question_id = question_id
                state.data = data
            else:
                state = UserState(user_id=user_id, current_question_id=question_id, data=data)
                session.add(state)
            await session.commit()


async def load_state(user_id):
    async with AsyncSessionLocal() as session:
        state = await session.get(UserState, user_id)
        if state:
            return state.current_question_id, state.data
        return "1", {}


def load_questions(file_path="questions.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            return {qid: Question(**q) for qid, q in raw_data.items()}
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {}
