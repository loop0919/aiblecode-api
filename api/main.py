import logging
import os

import uvicorn
from fastapi import FastAPI

from api.core.config import HOST, PORT
from api.routers.chat import router as chat_router
from api.routers.problem import router as problem_router
from api.routers.submission import router as submission_router
from api.routers.user import router as user_router

# デバッグモードを環境変数で切り替え
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

if DEBUG:
    logger.info("Running in DEBUG mode.")
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

# アプリケーション初期化
app = FastAPI(
    title="AIbleCode API",
    root_path="/api",
)

# ルーターの登録
app.include_router(user_router)
app.include_router(problem_router)
app.include_router(submission_router)
app.include_router(chat_router)


@app.get("/")
def read_root():
    return {"message": "Hello World! Get started with the API at /api/documentation."}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
