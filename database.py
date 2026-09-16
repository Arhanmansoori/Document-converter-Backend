
#------------MYSQL--------------#

# from dotenv import load_dotenv
# import os
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import urllib.parse
# load_dotenv()
# # MySQL credentials
# MYSQL_USER = os.getenv("MYSQL_USER")
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
# MYSQL_DB = os.getenv("MYSQL_DB")
# MYSQL_HOST =os.getenv("MYSQL_HOST")
# MYSQL_PORT = os.getenv("MYSQL_PORT")

# # SQLAlchemy database URL
# DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# # SQLAlchemy setup
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


#-----------------PostgreSQL---------------------#
# AI assisted development
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Option 1: Use SQLALCHEMY_DATABASE_URL directly if provided
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# Option 2: Construct from individual components if SQLALCHEMY_DATABASE_URL not provided
if not SQLALCHEMY_DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Arhan@#123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "oneclickdoc")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "public")

    # Validate all required values are present
    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT]):
        raise ValueError(
            "Missing database configuration. Please set environment variables properly."
        )

    # Ensure PORT is a valid integer
    try:
        port_num = int(POSTGRES_PORT)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid POSTGRES_PORT: {POSTGRES_PORT}. Must be a number.")

    # Configure query parameters (e.g. custom schema)
    query_params = {}
    if POSTGRES_SCHEMA and POSTGRES_SCHEMA != "public":
        query_params["options"] = f"-csearch_path={POSTGRES_SCHEMA}"

    # Build safe connection URL using SQLAlchemy's URL builder
    # This automatically escapes special characters in passwords like '@' and '#'
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=port_num,
        database=POSTGRES_DB,
        query=query_params if query_params else None,
    )
else:
    DATABASE_URL = SQLALCHEMY_DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def set_schema(session, schema_name="public"):
    """Set the search path (schema) for the current session"""
    session.execute(f"SET search_path TO {schema_name}")
    session.commit()