from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(verbose=True, override=True)
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path)

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

CSRF_SECRET = os.getenv("CSRF_SECRET")

DATABASE_URL = os.getenv("DATABASE_URL")

JUDGE_API_URL = os.getenv("JUDGE_API_URL")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
