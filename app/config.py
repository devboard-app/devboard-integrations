import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    DATABASE_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    REDIS_URL = f"redis://{os.environ['REDIS_HOST']}:6379/0"
    JWT_SECRET: str = os.environ["JWT_SECRET"]
    INTERNAL_API_KEY: str = os.environ["INTERNAL_API_KEY"]
    EMAIL_SERVICE_URL: str = os.environ["EMAIL_SERVICE_URL"]
    DEVBOARD_WORK_URL: str = os.environ["DEVBOARD_WORK_URL"]

settings = Settings()

