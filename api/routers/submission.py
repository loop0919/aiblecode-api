from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Response

from api import database
from api.core.config import ADMIN_USERNAME
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
    response: Response,
    user: user_model.User = Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.SubmissionCreateResponse:
    """\
    問題に対してコードを提出する。
    ❗**一般ユーザーログインが必須**
    """
    submission_crud.get_current_submission(db, user)
    current_submission = submission_crud.get_current_submission(db, user)

    if current_submission and submission_crud.is_judging(db, current_submission):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is being judged",
        )

    db_submission = submission_crud.create_submission(
        db, submission, category_path_id, problem_path_id, user
    )

    background_tasks.add_task(submission_crud.judge_submission, db, db_submission)

    response.set_cookie(key="language", value=submission.language, samesite="lax")

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
    response: Response,
    user: user_model.User = Depends(get_current_active_user),
) -> problem_schema.RunCodeResponse:
    """\
    コードを実行する。
    ❗**一般ユーザーログインが必須**
    """
    stdout, stderr = submission_crud.run_submission(runcode)

    response.set_cookie(key="language", value=runcode.language, samesite="lax")

    return problem_schema.RunCodeResponse(
        stdout=stdout,
        stderr=stderr,
    )


@router.post(
    "/rejudge",
    tags=["submission"],
    response_model=problem_schema.Response,
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid language"},
    },
)
def rejudge(
    category_path_id: str,
    problem_path_id: str,
    background_tasks: BackgroundTasks,
    user: user_model.User = Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.Response:
    """
    カテゴリーを作成する。
    🚨**管理者ログインが必須**
    """
    if user != user_crud.get_user_by_username(db, ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    submissions = submission_crud.get_all_submission_list(
        db, category_path_id, problem_path_id
    )

    background_tasks.add_task(
        submission_crud.judge_multiple_submission, db, submissions
    )

    return problem_schema.Response(
        message="Rejudge Submission created successfully",
    )
