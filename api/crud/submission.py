from collections import defaultdict
from typing import Literal

import judge0api as judge
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.core.config import JUDGE_API_URL
from api.crud import problem as problem_crud
from api.models import problem as problem_model
from api.models import submission as submission_model
from api.models import user as user_model
from api.schemas import submission as submission_schema

language_dict = {
    "Python": 71,
    "Java": 62,
    "C++": 105,
}

Status = Literal["AC", "WA", "TLE", "MLE", "RE", "CE", "IE"]


def map_status(status: dict[Status | Literal["WJ"], int]) -> str:
    if status["WJ"] > 0:
        return "ジャッジ中"
    elif status["AC"] == sum(status.values()):
        return "正解"
    elif status["CE"] > 0:
        return "コンパイルエラー"
    elif status["RE"] > 0:
        return "実行時エラー"
    elif status["WA"] > 0:
        return "不正解"
    elif status["TLE"] > 0:
        return "実行時間オーバー"
    elif status["MLE"] > 0:
        return "メモリオーバー"
    else:
        return "内部エラー"


def is_judging(db: Session, submission: submission_model.Submission) -> bool:
    statuses = summarize_status(db, submission)
    return map_status(statuses) == "ジャッジ中"


def create_submission(
    db: Session,
    submission: submission_schema.SubmissionCreate,
    category_path_id: str,
    problem_path_id: str,
    user: user_model.User,
) -> submission_model.Submission:
    problem = problem_crud.get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    if submission.language not in language_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language",
        )

    db_submission = submission_model.Submission(
        problem_id=problem.id,
        user_id=user.id,
        language=submission.language,
        code=submission.code,
    )

    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


def get_current_submission(
    db: Session, user: user_model.User
) -> submission_model.Submission:
    return (
        db.query(submission_model.Submission)
        .filter(submission_model.Submission.user_id == user.id)
        .order_by(submission_model.Submission.created_at.desc())
        .first()
    )


def summarize_status(
    db: Session, submission: submission_model.Submission
) -> dict[Status | Literal["WJ"], int]:
    details = get_submission_detail_list(db, submission)
    results = {detail.testcase_id: detail.status for detail in details}

    testcases = problem_crud.get_testcase_list(db, submission.problem_id)

    summary = defaultdict(int)

    for testcase in testcases:
        if testcase.id not in results:
            summary["WJ"] += 1
        else:
            summary[results[testcase.id]] += 1

    return summary


def get_submission_summary_list(
    db: Session, category_path_id: str, problem_path_id: str, user: user_model.User
) -> list[list[submission_model.Submission, dict[Status | Literal["WJ"], int]]]:
    problem = problem_crud.get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    submissions = (
        db.query(submission_model.Submission)
        .filter(
            submission_model.Submission.user_id == user.id,
            submission_model.Submission.problem_id == problem.id,
        )
        .order_by(submission_model.Submission.created_at.desc())
        .all()
    )

    return [
        [submission, summarize_status(db, submission)] for submission in submissions
    ]


def get_submission_detail_list(
    db: Session, submission: submission_model.Submission
) -> list[submission_model.SubmissionDetail]:
    return (
        db.query(submission_model.SubmissionDetail)
        .filter(submission_model.SubmissionDetail.submission_id == submission.id)
        .all()
    )


def submit(
    client: judge.Client,
    language: str,
    source_code: str,
    input_data: str,
    expected_output: str = "",
    time_limit: float = 2.0,
    memory_limit: int = 256,
) -> judge.submission.Submission:
    submission = judge.submission.Submission()
    submission.language_id = language_dict[language]
    submission.source_code = source_code.encode()
    submission.stdin = input_data.encode()
    submission.expected_output = expected_output.encode()
    submission.cpu_time_limit = time_limit
    submission.memory_limit = memory_limit * 1024

    submission.submit(client)
    submission.load(client)

    if map_result_status(submission.status["description"]) == "CE":
        submission.stderr = submission.compile_output

    return submission


def multiple_submit(
    db: Session,
    id: int,
    client: judge.Client,
    language: str,
    source_code: str,
    testcases: list[problem_model.Testcase],
    time_limit: float = 2.0,
    memory_limit: int = 256,
):
    submission = judge.submission.Submission()
    submission.language_id = language_dict[language]
    submission.source_code = source_code.encode()
    submission.cpu_time_limit = time_limit
    submission.memory_limit = memory_limit * 1000
    submission.max_file_size = 65536

    for testcase in testcases:
        try:
            submission.stdin = testcase.input.encode()
            submission.expected_output = testcase.output.encode()
            submission.submit(client)
            submission.load(client)

            status = map_result_status(submission.status["description"])

            save_submission_detail(
                db, id, testcase.id, status, submission.time, submission.memory
            )
        except Exception as e:
            save_submission_detail(db, id, testcase.id, "IE", 0, 0)
            print(e)


def judge_submission(db: Session, submission: submission_model.Submission):
    problem = problem_crud.get_problem(db, submission.problem_id)
    testcases = problem_crud.get_testcase_list(db, submission.problem_id)

    if not problem:
        raise ValueError(f"No problem found for problem_id: {submission.problem_id}")

    if not testcases:
        raise ValueError(f"No test cases found for problem_id: {submission.problem_id}")

    client = judge.Client(JUDGE_API_URL)

    if submission.code:
        multiple_submit(
            db,
            submission.id,
            client,
            submission.language,
            submission.code,
            testcases,
            problem.time_limit,
            problem.memory_limit,
        )
    else:
        for testcase in testcases:
            save_submission_detail(db, submission.id, testcase.id, "WA", 0, 0)


def map_result_status(result_status: str) -> str:
    if result_status == "Accepted":
        return "AC"
    elif result_status == "Wrong Answer":
        return "WA"
    elif result_status == "Time Limit Exceeded":
        return "TLE"
    elif result_status == "Memory Limit Exceeded":
        return "MLE"
    elif "Runtime Error" in result_status:
        return "RE"
    elif "Compilation Error" in result_status:
        return "CE"
    else:
        return "IE"


def save_submission_detail(
    db: Session,
    submission_id: int,
    testcase_id: int,
    status: str,
    time: float,
    memory: int,
):
    db_submission_detail = submission_model.SubmissionDetail(
        submission_id=submission_id,
        testcase_id=testcase_id,
        status=status,
        time=time,
        memory=memory,
    )

    db.add(db_submission_detail)
    db.commit()
    db.refresh(db_submission_detail)


def run_submission(runcode: submission_schema.RunCode) -> tuple[str, str]:
    if runcode.language not in language_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid language",
        )

    if runcode.code == "":
        return ("", "")

    client = judge.Client(JUDGE_API_URL)
    result = submit(
        client,
        runcode.language,
        runcode.code,
        runcode.input,
        time_limit=5.0,
        memory_limit=256,
    )

    status_val = map_result_status(result.status["description"])

    stdout = result.stdout.decode() if result.stdout else ""
    stderr = result.stderr.decode() if result.stderr else ""

    if status_val == "IE":
        return (stdout, "[Error] Internal Error")
    elif status_val == "TLE":
        return (stdout, "[Error] Time Limit Exceeded (over 5 sec)\n" + stderr)
    elif status_val == "MLE":
        return (
            stdout,
            "[Error] Memory Limit Exceeded (over 256 MB)\n" + stderr,
        )
    else:
        return (stdout, stderr)


def get_submission(db: Session, submission_id: int) -> submission_model.Submission:
    return (
        db.query(submission_model.Submission)
        .filter(submission_model.Submission.id == submission_id)
        .first()
    )
