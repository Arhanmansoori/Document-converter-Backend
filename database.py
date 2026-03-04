
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
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "oneclickdoc")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "public")  # Default schema
    
    # Validate all required values are present
    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT]):
        raise ValueError(
            "Missing database configuration. Please create a .env file with:\n"
            "SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:password@host:port/database\n"
            "OR individual components:\n"
            "POSTGRES_USER=postgres\n"
            "POSTGRES_PASSWORD=your_password\n"
            "POSTGRES_DB=oneclickdoc\n"
            "POSTGRES_HOST=localhost\n"
            "POSTGRES_PORT=5432"
        )
    
    # Ensure PORT is a valid integer
    try:
        int(POSTGRES_PORT)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid POSTGRES_PORT: {POSTGRES_PORT}. Must be a number.")
    
    # Construct DATABASE_URL with schema support
    # Format: postgresql+psycopg2://user:password@host:port/database?options=-csearch_path=schema
    if POSTGRES_SCHEMA and POSTGRES_SCHEMA != "public":
        DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?options=-csearch_path%3D{POSTGRES_SCHEMA}"
    else:
        DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    # Use provided SQLALCHEMY_DATABASE_URL
    DATABASE_URL = SQLALCHEMY_DATABASE_URL

# Create engine with schema support
# For PostgreSQL, we can set default schema in connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Function to set schema for a session (optional, for explicit schema usage)
def set_schema(session, schema_name="public"):
    """Set the search path (schema) for the current session"""
    session.execute(f"SET search_path TO {schema_name}")
    session.commit()
