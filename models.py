import os
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    DateTime,
    String,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.engine import URL
from datetime import datetime

from db import movies

load_dotenv()

# PostgreSQL credentials
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "movies_db")

# Connect to the existing default database first
admin_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database="postgres",
)

admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

# Create movies_db if it does not exist
with admin_engine.connect() as conn:
    exists = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": DB_NAME},
    ).scalar()

    if not exists:
        conn.execute(
            text(f'CREATE DATABASE "{DB_NAME}"')
        )
        print(f"Database '{DB_NAME}' created successfully.")
    else:
        print(f"Database '{DB_NAME}' already exists.")

admin_engine.dispose()

# Now connect to movies_db
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL, echo=False)


class Base(DeclarativeBase):
    pass


class Movies(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    genre = Column(String)
    show_time = Column(String)
    price = Column(Float)
    total_seats = Column(Integer, default=0)
    booked_seats = Column(Integer, default=0)

    @property
    def available_seats(self):
        return self.total_seats - self.booked_seats


class Booking(Base):
    __tablename__ = "booking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer)
    customer_name = Column(String)
    seats = Column(Integer)
    total_amount = Column(Float)
    status = Column(String, default="confirmed")
    booked_at = Column(DateTime, default=datetime.now)


def create_table():
    Base.metadata.create_all(bind=engine)


def seed_movies():
    with Session(engine) as db:
        if db.query(Movies).count() > 0:
            print("Data already exists.")
            return

        movie_objects = [
            Movies(
                title=movie["title"],
                genre=movie["genre"],
                show_time=movie["show_time"],
                price=movie["price"],
                total_seats=movie["total_seats"],
                booked_seats=movie.get("booked_seats", 0)
            )
            for movie in movies
        ]

        db.add_all(movie_objects)
        db.commit()

        print("Movie data seeded successfully.")