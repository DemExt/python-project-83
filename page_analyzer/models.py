import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Используйте вашу реальную строку подключения PostgreSQL:
SQLALCHEMY_DATABASE_URI = (
    'postgresql+psycopg2://username:'
    'password@localhost:5432/yourdbname'
)

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Check(Base):
    __tablename__ = 'url_checks'
    id = Column(Integer, primary_key=True)
    url_id = Column(
        Integer, ForeignKey('urls.id', ondelete="CASCADE"), nullable=False)
    status_code = Column(Integer, nullable=True)
    h1 = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    url = relationship('Url', back_populates='checks')


class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    checks = relationship(
        'Check', back_populates='url', cascade='all, delete-orphan')


Base.metadata.create_all(bind=engine)
