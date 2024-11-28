from typing import Literal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from collections import defaultdict

from api.models import (
    user as user_model,
    submission as submission_model,
)
from api.schemas import submission as submission_schema
from api.crud import problem as problem_crud
from api.core.config import JUDGE_API_URL

import judge0api as judge

language_dict = {
    "Python": 71,
    "Java": 62,
    "C++": 105,
}

Status = Literal["AC", "WA", "TLE", "MLE", "RE", "CE", "IE"]


def create_submission(
    db: Session,
    submission: submission_schema.SubmissionCreate,
    category_path_id: str,
    problem_path_id: str,
    user: user_model.User,
) -> submission_model.Submission:
    problem = problem_crud.get_problem_by_path_id(
        db, category_path_id, problem_path_id
    )
    
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
    expected_output: str,
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

    return submission


def judge_submission(db: Session, submission: submission_model.Submission):
    problem = problem_crud.get_problem(db, submission.problem_id)
    testcases = problem_crud.get_testcase_list(db, submission.problem_id)
    
    if not problem:
        raise ValueError(f"No problem found for problem_id: {submission.problem_id}")

    if not testcases:
        raise ValueError(f"No test cases found for problem_id: {submission.problem_id}")

    client = judge.Client(JUDGE_API_URL)

    for testcase in testcases:
        result = submit(
            client,
            submission.language,
            submission.code,
            testcase.input,
            testcase.output,
            problem.time_limit,
            problem.memory_limit,
        )

        status = map_result_status(result.status["description"])

        save_submission_detail(
            db, submission.id, testcase.id, status, result.time, result.memory
        )


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
