import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.user import router as user_router
from api.routers.problem import router as problem_router
from api.routers.submission import router as submission_router

from api.core.config import HOST, PORT

import sys

if "-d" in sys.argv or "--debug" in sys.argv:
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

app = FastAPI(
    title="AIbleCode API",
    root_path="/api"
)
app.include_router(user_router)
app.include_router(problem_router)
app.include_router(submission_router)

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello World! Get started with the API at /api/docs."}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
