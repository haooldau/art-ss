from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from ..config.database import Base
from datetime import datetime

class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    tag = Column(String(50))
    city = Column(String(50))
    venue = Column(String(255))
    lineup = Column(Text)
    date = Column(Date, nullable=False)
    price = Column(String(100))
    status = Column(String(50))
    detail_url = Column(String(255))
    poster = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow) 