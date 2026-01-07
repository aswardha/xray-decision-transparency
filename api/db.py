from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Database connection URL.
# Here we are using SQLite for simplicity.
# The database will be created as a local file named "xray.db".
#
# In production, this could be:
#   - PostgreSQL
#   - MySQL
#   - Cloud-hosted database

DATABASE_URL = "sqlite:///./xray.db"


# Create the SQLAlchemy engine.
# The engine is the low-level interface that:
# - manages connections to the database
# - sends SQL queries to the database

# "check_same_thread": False is required for SQLite because:
# - FastAPI handles requests concurrently
# - SQLite is otherwise strict about thread usage

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# SessionLocal is a factory for creating database sessions.

# A session:
# - represents a single unit of work
# - is used to query and write data
# - is typically scoped to a single request

SessionLocal = sessionmaker(bind=engine)


# Base is the base class for all ORM models.

# Every database model (table) will inherit from Base.
# SQLAlchemy uses this to:
# - track models
# - create tables
# - map Python objects to database rows

Base = declarative_base()
