from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from api import database
from api.core.security import get_current_active_user
from api.crud import problem as problem_crud
from api.crud import submission as submission_crud
from api.crud import user as user_crud
from api.models import user as user_model
from api.schemas import submission as problem_schema

router = APIRouter()


@router.get(
    "/problem/{category_path_id}/{problem_path_id}/submissions",
    tags=["submission"],
    response_model=list[problem_schema.SubmissionSummary],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Problem not found"},
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
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid language"},
    },
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

    background_tasks.add_task(submission_crud.judge_submission, db, db_submission)

    return problem_schema.SubmissionCreateResponse(
        id=db_submission.id,
        created_at=db_submission.created_at,
        message="Submission created successfully",
    )


@router.get(
    "/submission/{submission_id}",
    tags=["submission"],
    response_model=problem_schema.Submission,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Submission not found"},
    },
)
def submission(
    db=Depends(database.get_db),
    submission_id: str = None,
    user: user_model.User = Depends(get_current_active_user),
) -> problem_schema.Submission:
    """\
    提出の詳細を返す。
    ❗**一般ユーザーログインが必須**
    """
    submission = submission_crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    curr_user = user_crud.get_user(db, submission.user_id)

    return problem_schema.Submission(
        id=submission.id,
        created_at=submission.created_at,
        username=curr_user.username,
        language=submission.language,
        code=submission.code,
        statuses=submission_crud.summarize_status(db, submission),
        details=[
            problem_schema.SubmissionDetail(
                id=detail.id,
                testcase_name=problem_crud.get_testcase(db, detail.testcase_id).name,
                status=detail.status,
                time=detail.time,
                memory=detail.memory,
            )
            for detail in submission_crud.get_submission_detail_list(db, submission)
        ],
    )


@router.post(
    "/run",
    tags=["submission"],
    response_model=problem_schema.RunCodeResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid language"},
    },
)
def run_code(
    runcode: problem_schema.RunCode,
    user: user_model.User = Depends(get_current_active_user),
) -> problem_schema.RunCodeResponse:
    """\
    コードを実行する。
    ❗**一般ユーザーログインが必須**
    """
    stdout, stderr = submission_crud.run_submission(runcode)

    return problem_schema.RunCodeResponse(
        stdout=stdout,
        stderr=stderr,
    )
