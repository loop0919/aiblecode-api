import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import user as user_model
from api.models.problem import Problem, Testcase
from api.models.submission import Submission, SubmissionDetail
from api.schemas import user as user_schema
from api.utils.hash import hash_password


def get_user(db: Session, user_id: uuid.UUID) -> user_model.User:
    return db.query(user_model.User).filter(user_model.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> user_model.User:
    return (
        db.query(user_model.User).filter(user_model.User.username == username).first()
    )


def get_user_list(db: Session) -> list[user_model.User]:
    return db.query(user_model.User).all()


def create_user(db: Session, user: user_schema.UserCreate) -> user_model.User:
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )

    hashed_password = hash_password(user.password)

    db_user = user_model.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_session(db: Session, id: str) -> user_model.Session:
    return db.query(user_model.Session).filter(user_model.Session.id == id).first()


def get_ranking(db: Session) -> list[user_schema.UserPoints]:
    min_created_at = (
        select(
            Submission.user_id,
            Submission.problem_id,
            func.min(Submission.created_at).label("min_created_at"),
        )
        .join(SubmissionDetail, Submission.id == SubmissionDetail.submission_id)
        .join(Testcase, Submission.problem_id == Testcase.problem_id)
        .where(
            select(func.count())
            .select_from(SubmissionDetail)
            .where(
                SubmissionDetail.submission_id == Submission.id,
                SubmissionDetail.status == "AC",
            )
            .correlate(Submission)
            .as_scalar()
            == select(func.count())
            .select_from(Testcase)
            .where(Submission.problem_id == Testcase.problem_id)
            .correlate(Submission)
            .as_scalar()
        )
        .group_by(Submission.user_id, Submission.problem_id)
        .cte("min_created_at")
    )

    # accepted_submissions CTE
    accepted_submissions = (
        select(
            Submission.user_id,
            Problem.id.label("problem_id"),
            Problem.level,
            Submission.created_at,
        )
        .select_from(Submission)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(
            Submission.created_at
            == (
                select(min_created_at.c.min_created_at)
                .where(
                    Submission.user_id == min_created_at.c.user_id,
                    Submission.problem_id == min_created_at.c.problem_id,
                )
                .as_scalar()
            )
        )
        .cte("accepted_submissions")
    )

    # 最終的なランキングクエリ
    query = (
        select(
            func.rank()
            .over(
                order_by=(
                    func.sum(accepted_submissions.c.level).desc(),
                    func.max(accepted_submissions.c.created_at).desc(),
                )
            )
            .label("rank"),
            user_model.User.username,
            func.sum(func.coalesce(accepted_submissions.c.level, 0)).label("point"),
            func.max(accepted_submissions.c.created_at).label("last_submit"),
        )
        .select_from(user_model.User)
        .outerjoin(
            accepted_submissions,
            accepted_submissions.c.user_id == user_model.User.id,
        )
        .group_by(user_model.User.username)
        .order_by(
            func.sum(accepted_submissions.c.level).desc(),
            func.max(accepted_submissions.c.created_at).desc(),
        )
    )

    print(query)
    result = db.execute(query).fetchall()

    return [
        user_schema.UserPoints(
            rank=rank, username=username, point=point * 10, last_submit=last_submit
        )
        for (rank, username, point, last_submit) in result
    ]
