from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base
from app.game.models import User

class UserDAO(Base):
    """ 
    UserDAO предназначен для создания методов, которые будут выполнять различные операции с записями пользователей. 
    """
    model = User


@classmethod
async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
    filter_dict = filters.model_dump(exclude_unset=True)
    try:
        query = select(cls.mode).filter_by(**filter_dict)
        result = await session.execute(query)
        record = result.scalar_one_or_none()
        return record 
    except SQLAlchemyError as e:
        raise

#мы создаем Pydantic-модель и передаем ее в качестве значения filters

@classmethod
async def add(cls, session: AsyncSession, values: BaseModel):
    values_dict = values.model_dump(exclude_unset=True)
    new_instance = cls.model(**values_dict)
    session.add(new_instance)
    try:
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise e 
    return new_instance


@classmethod
async def get_top_scores(cls, session: AsyncSession, limit: int = 20):
    """В select мы указываем, какие значения колонок хотим получить. Для отображения топа пользователей достаточно telegram_id, first_name и best_score.
        Сортировка выполняется функцией desc, которая упорядочивает пользователей по best_score в порядке убывания. Параметр limit ограничивает список до 20 пользователей.
        Мы добавляем rank — место в турнирной таблице — на стороне приложения. Это удобно и делает запрос проще.
        Возвращается список словарей с данными о пользователях и их позициями.
    """
    try:
        query = (
            select(cls.model.telegram_id, cls.model.first_name, cls.model.best_score)
            .order_by(desc(cls.model.best_score))
            .limit(limit)
        )
        result = await session.execute(query)
        records = result.fetchall()

        ranked_records = [
            {'rank': index + 1, 'telegram_id': record.telegram_id, 'first_name': record.first_name, 'best_score': record.best_score}
            for index, record in enumerate(records)
        ]

        return ranked_records
    except SQLAlchemyError as e:
        raise e 
    

@classmethod
async def get_user_rank(cls, session: AsyncSession, telegram_id: int):
    try: 
        rank_subquery = (
            select(
                cls.model.telegram_id,
                cls.model.best_score,
                func.rank().over(order_by=desc(cls.model.best_score)).label(rank)
            )
            .order_by(desc(cls.model.best_score))
            .subquery()
        )

        query = select(rank_subquery.c.rank, rank_subquery.c.best_score).where(
            rank_subquery.c.telegram_id == telegram_id
        )
        result = await session.execute(query)
        rank_row = result.fetchone()

        return {'rank': rank_row, 'best_score': rank_row.best_score} if rank_row else None
    except SQLAlchemyError as e:
        raise e 
