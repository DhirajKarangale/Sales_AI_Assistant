import os
import psycopg2
from dotenv import load_dotenv


def init_db():
    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")

    required_env = {
        "DB_HOST": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_PORT": db_port
    }
    missing = [k for k, v in required_env.items() if not v]
    if missing:
        raise ValueError(f"Missing required database environment variable(s): {', '.join(missing)}")

    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    return conn

