from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from api import database
from api.core.security import get_current_active_user
from api.crud import chat as chat_crud
from api.crud import problem as problem_crud
from api.crud import submission as submission_crud
from api.schemas import chat as chat_schema

router = APIRouter()


@router.post(
    "/submission/{submission_id}/review",
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

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    problem = problem_crud.get_problem(db, submission.problem_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    status = submission_crud.summarize_status(db, submission)

    if status["WJ"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is not judged yet",
        )

    return chat_crud.chat(db, problem, submission, status)


@router.post(
    "/submission/{submission_id}/review_stream",
    tags=["chat"],
    response_model=Generator[str, None, None],
)
def review_stream(
    submission_id: str,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
):
    """\
    チャットのストリームを取得する
    ❗**一般ユーザーログインが必須**
    """

    submission = submission_crud.get_submission(db, submission_id)
    problem = problem_crud.get_problem(db, submission.problem_id)

    return StreamingResponse(
        chat_crud.chat_stream(db, problem, submission),
        media_type="application/json",
    )
