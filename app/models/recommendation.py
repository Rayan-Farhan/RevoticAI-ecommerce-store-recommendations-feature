from sqlalchemy import Column, Integer, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ItemSimilarity(Base):
    __tablename__ = "item_similarity"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, nullable=False, index=True)
    similar_item_id = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=False)


class UserSimilarity(Base):
    __tablename__ = "user_similarity"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    similar_user_id = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=False)