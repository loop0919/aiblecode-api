import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, case, distinct, func, literal, select
from sqlalchemy.orm import Session

from api.models import problem as problem_model
from api.models import submission as submission_model
from api.models import user as user_model
from api.schemas import problem as problem_schema


# Category #########################################################################################
def get_category(db: Session, category_id: str) -> problem_model.Category:
    return (
        db.query(problem_model.Category)
        .filter(problem_model.Category.id == category_id)
        .first()
    )


def get_category_by_path_id(db: Session, path_id: str) -> problem_model.Category:
    return (
        db.query(problem_model.Category)
        .filter(problem_model.Category.path_id == path_id)
        .first()
    )


def get_category_list(db: Session) -> list[problem_model.Category]:
    return (
        db.query(problem_model.Category).order_by(problem_model.Category.path_id).all()
    )


def create_category(
    db: Session, category: problem_schema.CategoryCreate
) -> problem_model.Category:
    db_category = get_category_by_path_id(db, category.path_id)

    if not db_category:
        db_category = problem_model.Category(path_id=category.path_id)

    db_category.title = category.title
    db_category.description = category.description

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# Problem ##########################################################################################
def get_problem_list(db: Session, category_path_id: str) -> list[problem_model.Problem]:
    category = get_category_by_path_id(db, category_path_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return (
        db.query(problem_model.Problem)
        .filter(problem_model.Problem.category_id == category.id)
        .order_by(problem_model.Problem.path_id)
        .all()
    )


def get_problem_list_with_ac_submissions(
    db: Session, category_path_id: str
) -> list[tuple[problem_model.Problem, int]]:
    category = get_category_by_path_id(db, category_path_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    testcase_count_subquery = (
        db.query(func.count(problem_model.Testcase.id))
        .filter(problem_model.Testcase.problem_id == problem_model.Problem.id)
        .correlate(problem_model.Problem)
        .scalar_subquery()
    )

    ac_submission_count_subquery = (
        db.query(func.count(submission_model.SubmissionDetail.id))
        .filter(
            submission_model.SubmissionDetail.submission_id
            == submission_model.Submission.id,
            submission_model.SubmissionDetail.status == "AC",
        )
        .correlate(submission_model.Submission)
        .scalar_subquery()
    )

    result = (
        db.query(
            problem_model.Problem,
            func.count(distinct(submission_model.Submission.user_id)),
        )
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
            ),
        )
        .filter(problem_model.Problem.category_id == category.id)
        .group_by(problem_model.Problem.id)
        .order_by(problem_model.Problem.path_id)
        .all()
    )

    print(result)

    return result


def get_problem_list_with_datas(
    db: Session, user: user_model.User | None, category_path_id: str
) -> list[tuple[problem_model.Problem, int]]:
    category = get_category_by_path_id(db, category_path_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    testcase_count_subquery = (
        db.query(func.count(problem_model.Testcase.id))
        .filter(problem_model.Testcase.problem_id == problem_model.Problem.id)
        .correlate(problem_model.Problem)
        .scalar_subquery()
    )

    ac_submission_count_subquery = (
        db.query(func.count(submission_model.SubmissionDetail.id))
        .filter(
            submission_model.SubmissionDetail.submission_id
            == submission_model.Submission.id,
            submission_model.SubmissionDetail.status == "AC",
        )
        .correlate(submission_model.Submission)
        .scalar_subquery()
    )

    is_accepted_subquery = (
        db.query(
            problem_model.Problem.id.label("problem_id"),
            case(
                ((func.count(submission_model.Submission.id) >= 1, 1)),
                else_=0,
            ).label("is_accepted"),
        )
        .select_from(problem_model.Problem)
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
                submission_model.Submission.user_id == user.id,
            ),
        )
        .group_by(problem_model.Problem.id)
        .subquery()
        if user
        else (
            db.query(
                problem_model.Problem.id.label("problem_id"),
                literal(0).label("is_accepted"),
            ).subquery()
        )
    )

    result = (
        db.query(
            problem_model.Problem,
            func.count(distinct(submission_model.Submission.user_id)),
            is_accepted_subquery.c.is_accepted.label("is_accepted"),
        )
        .select_from(problem_model.Problem)
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
            ),
        )
        .join(
            is_accepted_subquery,
            is_accepted_subquery.c.problem_id == problem_model.Problem.id,
        )
        .filter(problem_model.Problem.category_id == category.id)
        .group_by(problem_model.Problem.id)
        .order_by(problem_model.Problem.path_id)
        .all()
    )

    return result


def get_problem_with_submission_count(
    db: Session, category_path_id: str, problem_path_id: str
) -> tuple[problem_model.Problem, int]:
    problem = get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    testcase_count_subquery = (
        db.query(func.count(problem_model.Testcase.id))
        .filter(problem_model.Testcase.problem_id == problem_model.Problem.id)
        .correlate(problem_model.Problem)
        .scalar_subquery()
    )

    ac_submission_count_subquery = (
        db.query(func.count(submission_model.SubmissionDetail.id))
        .filter(
            submission_model.SubmissionDetail.submission_id
            == submission_model.Submission.id,
            submission_model.SubmissionDetail.status == "AC",
        )
        .correlate(submission_model.Submission)
        .scalar_subquery()
    )

    result = (
        db.query(
            problem_model.Problem,
            func.count(distinct(submission_model.Submission.user_id)).label(
                "submission_count"
            ),
        )
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
            ),
        )
        .filter(problem_model.Problem.id == problem.id)
        .group_by(problem_model.Problem.id)
        .first()
    )

    return result


def get_problem_with_datas(
    db: Session,
    user: user_model.User | None,
    category_path_id: str,
    problem_path_id: str,
) -> tuple[problem_model.Problem, int, int]:
    problem = get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    testcase_count_subquery = (
        db.query(func.count(problem_model.Testcase.id))
        .filter(problem_model.Testcase.problem_id == problem_model.Problem.id)
        .correlate(problem_model.Problem)
        .scalar_subquery()
    )

    ac_submission_count_subquery = (
        db.query(func.count(submission_model.SubmissionDetail.id))
        .filter(
            submission_model.SubmissionDetail.submission_id
            == submission_model.Submission.id,
            submission_model.SubmissionDetail.status == "AC",
        )
        .correlate(submission_model.Submission)
        .scalar_subquery()
    )

    is_accepted_subquery = (
        db.query(
            problem_model.Problem.id.label("problem_id"),
            case(
                ((func.count(submission_model.Submission.id) >= 1, 1)),
                else_=0,
            ).label("is_accepted"),
        )
        .select_from(problem_model.Problem)
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
                submission_model.Submission.user_id == user.id,
            ),
        )
        .group_by(problem_model.Problem.id)
        .subquery()
        if user
        else (
            db.query(
                problem_model.Problem.id.label("problem_id"),
                literal(0).label("is_accepted"),
            ).subquery()
        )
    )

    result = (
        db.query(
            problem_model.Problem,
            func.count(distinct(submission_model.Submission.user_id)),
            is_accepted_subquery.c.is_accepted.label("is_accepted"),
        )
        .select_from(problem_model.Problem)
        .outerjoin(
            submission_model.Submission,
            and_(
                problem_model.Problem.id == submission_model.Submission.problem_id,
                testcase_count_subquery == ac_submission_count_subquery,
            ),
        )
        .join(
            is_accepted_subquery,
            is_accepted_subquery.c.problem_id == problem_model.Problem.id,
        )
        .filter(problem_model.Problem.id == problem.id)
        .group_by(problem_model.Problem.id)
        .order_by(problem_model.Problem.path_id)
        .first()
    )

    return result


def get_problem(db: Session, problem_id: str) -> problem_model.Problem:
    return (
        db.query(problem_model.Problem)
        .filter(problem_model.Problem.id == problem_id)
        .first()
    )


def get_problem_by_path_id(
    db: Session, category_path_id: str, path_id: str
) -> problem_model.Problem:
    category = get_category_by_path_id(db, category_path_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return (
        db.query(problem_model.Problem)
        .filter(
            problem_model.Problem.category_id == category.id,
            problem_model.Problem.path_id == path_id,
        )
        .first()
    )


def create_problem(
    db: Session, problem: problem_schema.ProblemCreate
) -> problem_model.Problem:
    category = get_category_by_path_id(db, problem.category_path_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    db_problem = get_problem_by_path_id(db, problem.category_path_id, problem.path_id)

    if not db_problem:
        db_problem = problem_model.Problem(
            path_id=problem.path_id, category_id=category.id
        )

    db_problem.title = problem.title
    db_problem.statement = problem.statement
    db_problem.level = problem.level
    db_problem.time_limit = problem.time_limit
    db_problem.memory_limit = problem.memory_limit

    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem


def check_accepted_user_by_path_id(
    db: Session,
    user: user_model.User,
    category_path_id: str,
    problem_path_id: str,
) -> bool:
    problem = get_problem_by_path_id(db, category_path_id, problem_path_id)

    min_created_at = (
        select(
            submission_model.Submission.user_id,
            submission_model.Submission.problem_id,
            func.min(submission_model.Submission.created_at).label("min_created_at"),
        )
        .join(
            submission_model.SubmissionDetail,
            submission_model.Submission.id
            == submission_model.SubmissionDetail.submission_id,
        )
        .join(
            problem_model.Testcase,
            submission_model.Submission.problem_id == problem_model.Testcase.problem_id,
        )
        .where(
            select(func.count())
            .select_from(submission_model.SubmissionDetail)
            .where(
                submission_model.SubmissionDetail.submission_id
                == submission_model.Submission.id,
                submission_model.SubmissionDetail.status == "AC",
            )
            .correlate(submission_model.Submission)
            .as_scalar()
            == select(func.count())
            .select_from(problem_model.Testcase)
            .where(
                submission_model.Submission.problem_id
                == problem_model.Testcase.problem_id
            )
            .correlate(submission_model.Submission)
            .as_scalar()
        )
        .group_by(
            submission_model.Submission.user_id, submission_model.Submission.problem_id
        )
        .cte("min_created_at")
    )

    # accepted_submissions CTE
    accepted_submissions = (
        select(
            submission_model.Submission.user_id,
            problem_model.Problem.id.label("problem_id"),
            problem_model.Problem.level,
            submission_model.Submission.created_at,
        )
        .select_from(submission_model.Submission)
        .join(
            problem_model.Problem,
            submission_model.Submission.problem_id == problem_model.Problem.id,
        )
        .where(
            submission_model.Submission.created_at
            == (
                select(min_created_at.c.min_created_at)
                .where(
                    submission_model.Submission.user_id == min_created_at.c.user_id,
                    submission_model.Submission.problem_id
                    == min_created_at.c.problem_id,
                )
                .as_scalar()
            )
        )
        .cte("accepted_submissions")
    )

    query = (
        select(func.count())
        .select_from(accepted_submissions)
        .where(
            accepted_submissions.c.user_id == user.id,
            accepted_submissions.c.problem_id == problem.id,
        )
    )

    result = db.execute(query).fetchone()

    return bool(result[0])


# Testcase #########################################################################################
def get_testcase_list(
    db: Session, problem_id: uuid.UUID
) -> list[problem_model.Testcase]:
    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.problem_id == problem_id)
        .order_by(problem_model.Testcase.name)
        .all()
    )


def get_testcase_list_by_path_id(
    db: Session, category_path_id: str, problem_path_id: str
) -> list[problem_model.Testcase]:
    problem = get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.problem_id == problem.id)
        .order_by(problem_model.Testcase.name)
        .all()
    )


def get_testcase(db: Session, testcase_id: str) -> problem_model.Testcase:
    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.id == testcase_id)
        .first()
    )


def get_testcase_by_name(
    db: Session, problem_id: uuid, name: str
) -> problem_model.Testcase:
    return (
        db.query(problem_model.Testcase)
        .filter(
            problem_model.Testcase.problem_id == problem_id,
            problem_model.Testcase.name == name,
        )
        .first()
    )


def create_testcase(
    db: Session, testcase: problem_schema.TestcaseCreate
) -> problem_model.Testcase:
    problem = get_problem_by_path_id(
        db, testcase.category_path_id, testcase.problem_path_id
    )

    if not problem:
        raise

    db_testcase = get_testcase_by_name(db, problem.id, testcase.name)

    if not db_testcase:
        db_testcase = problem_model.Testcase(problem_id=problem.id, name=testcase.name)

    db_testcase.input = testcase.input
    db_testcase.output = testcase.output

    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase
