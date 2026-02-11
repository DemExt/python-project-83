from sqlalchemy import create_engine, Column
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'

engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)
    status_code = Column(Integer, nullable=False)
    error = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    title = Column(String, nullable=True)
    h1 = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)

    url = relationship('Url', back_populates='checks')


class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    checks = relationship('Check', back_populates='url', cascade='all, delete')


# Создайте таблицы, если еще не существуют
Base.metadata.create_all(bind=engine)
