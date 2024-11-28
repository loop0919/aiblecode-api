from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status

from api import database
from api.core.security import get_current_active_user
from api.schemas import submission as problem_schema
from api.crud import submission as submission_crud
from api.models import user as user_model

router = APIRouter()


@router.get(
    "/problem/{category_path_id}/{problem_path_id}/submissions",
    tags=["submission"],
    response_model=list[problem_schema.SubmissionSummary],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Problem not found"}
    },
)
def submission_list(
    category_path_id: str,
    problem_path_id: str,
    user: user_model.User = Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> list[problem_schema.SubmissionSummary]:
    """\
    当ユーザーが出した提出一覧を返す。  
    ❗**一般ユーザーログインが必須**
    """
    submissions = submission_crud.get_submission_summary_list(
        db, category_path_id, problem_path_id, user
    )
    
    if submissions is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    return [
        problem_schema.SubmissionSummary(
            id=submission.id,
            created_at=submission.created_at,
            username=user.username,
            language=submission.language,
            statuses=statuses,
        )
        for submission, statuses in submissions
    ]


@router.post(
    "/problem/{category_path_id}/{problem_path_id}/submit",
    tags=["submission"],
    response_model=problem_schema.SubmissionCreateResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Problem not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid language"}
    }
)
def submit(
    category_path_id: str,
    problem_path_id: str,
    submission: problem_schema.SubmissionCreate,
    background_tasks: BackgroundTasks,
    user: user_model.User = Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.Submission:
    """\
    問題に対してコードを提出する。  
    ❗**一般ユーザーログインが必須**
    """
    db_submission = submission_crud.create_submission(
        db, submission, category_path_id, problem_path_id, user
    )
    
    if db_submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    
    background_tasks.add_task(submission_crud.judge_submission, db, db_submission)

    return problem_schema.SubmissionCreateResponse(
        id=db_submission.id,
        created_at=db_submission.created_at,
        message="Submission created successfully",
    )
