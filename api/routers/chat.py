from typing import Generator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api import database
from api.core.security import get_current_active_user
from api.crud import (
    submission as submission_crud,
    chat as chat_crud,
    problem as problem_crud,
)
from api.schemas import chat as chat_schema

router = APIRouter()


@router.post(
    "/problems/{submission_id}/review",
    tags=["chat"],
    response_model=chat_schema.Chat,
)
def review(
    submission_id: str,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> chat_schema.Chat:
    """\
    チャットを取得する。  
    ❗**一般ユーザーログインが必須**
    """

    submission = submission_crud.get_submission(db, submission_id)
    problem = problem_crud.get_problem(db, submission.problem_id)

    return chat_crud.chat(db, problem, submission)


@router.post(
    "/problems/{submission_id}/review_stream",
    tags=["chat"],
    response_model=Generator[str, None, None],
)
def review_stream(
    submission_id: str,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
):
    """\
    チャットのストリームを取得する。  
    ❗**一般ユーザーログインが必須**
    """

    submission = submission_crud.get_submission(db, submission_id)
    problem = problem_crud.get_problem(db, submission.problem_id)

    return StreamingResponse(
        chat_crud.chat_stream(db, problem, submission), media_type="application/json"
    )
